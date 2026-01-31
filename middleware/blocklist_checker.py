"""
Blocklist checker middleware - Check messages against blocklist
"""
import logging
import re
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from telegram.constants import ChatType, ChatMemberStatus
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def wildcard_to_regex(pattern: str) -> str:
    """
    Convert wildcard pattern to regex
    
    ? = any single character
    * = any characters (including none)
    
    Args:
        pattern: Wildcard pattern
        
    Returns:
        Regex pattern string
    """
    # Escape special regex characters except * and ?
    pattern = re.escape(pattern)
    
    # Convert wildcards
    pattern = pattern.replace(r'\*', '.*')  # * = any characters
    pattern = pattern.replace(r'\?', '.')   # ? = single character
    
    return f'^{pattern}$'


async def check_blocklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Check message against blocklist
    
    If match found, delete message and take action
    """
    # Only check regular text messages in groups
    if not update.message or not update.message.text:
        return True
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Only in groups
    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return True
    
    # Don't check bots or admins
    if user.is_bot:
        return True
    
    chat_id = chat.id
    user_id = user.id
    message_text = update.message.text.lower()
    
    try:
        # Check if user is admin
        member = await chat.get_member(user_id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True
        
        db = context.application.bot_data.get('database')
        if db is None:
            return True
        
        # Check if user is approved (bypasses blocklist)
        user_doc = await db.users.find_one({"_id": str(user_id)})
        if user_doc and user_doc.get('chat_data', {}).get(str(chat_id), {}).get('approved', False):
            return True
        
        # Get all blocklists for this chat
        cursor = db.blocklists.find({"chat_id": str(chat_id)})
        blocklists = await cursor.to_list(length=None)
        
        if not blocklists:
            return True
        
        # Check each trigger
        for bl in blocklists:
            trigger = bl.get('trigger', '').lower()
            
            # Convert wildcard to regex
            regex_pattern = wildcard_to_regex(trigger)
            
            # Check if message matches
            if re.search(regex_pattern, message_text):
                # Match found!
                reason = bl.get('reason')
                action = bl.get('action', 'warn')
                delete_msg = bl.get('delete_message', True)
                
                # Delete message if configured
                if delete_msg:
                    try:
                        await update.message.delete()
                    except Exception as e:
                        logger.debug(f"Could not delete message: {e}")
                
                # Take action
                action_taken = ""
                try:
                    if action == 'ban':
                        await chat.ban_member(user_id)
                        action_taken = "banned"
                    
                    elif action == 'kick':
                        await chat.ban_member(user_id)
                        await chat.unban_member(user_id)
                        action_taken = "kicked"
                    
                    elif action == 'mute':
                        await chat.restrict_member(
                            user_id,
                            permissions=ChatPermissions(can_send_messages=False)
                        )
                        action_taken = "muted"
                    
                    elif action == 'warn':
                        # Add a warning
                        await db.warnings.insert_one({
                            "chat_id": str(chat_id),
                            "user_id": str(user_id),
                            "reason": f"Blocklist violation: {trigger}" + (f" ({reason})" if reason else ""),
                            "warned_by": "system",
                            "created_at": datetime.now(timezone.utc)
                        })
                        
                        # Get warning count
                        warn_count = await db.warnings.count_documents({
                            "chat_id": str(chat_id),
                            "user_id": str(user_id)
                        })
                        
                        # Update user document
                        await db.users.update_one(
                            {"_id": str(user_id)},
                            {
                                "$set": {
                                    f"chat_data.{chat_id}.warnings": warn_count
                                }
                            },
                            upsert=True
                        )
                        
                        action_taken = f"warned ({warn_count} warnings)"
                    
                    # Send notification
                    notification_text = (
                        f"🚫 <b>Blocklist violation!</b>\n\n"
                        f"User: {user.mention_html()}\n"
                        f"Trigger: <code>{trigger}</code>\n"
                    )
                    
                    if reason:
                        notification_text += f"Reason: {reason}\n"
                    
                    if action_taken:
                        notification_text += f"Action: {action_taken.capitalize()}"
                    
                    notification = await context.bot.send_message(
                        chat_id,
                        notification_text,
                        parse_mode='HTML'
                    )
                    
                    # Auto-delete notification after 10 seconds
                    import asyncio
                    asyncio.create_task(delete_after_delay(notification, 10))
                    
                except Exception as e:
                    logger.error(f"Error taking blocklist action: {e}")
                
                # Log the violation
                await db.action_logs.insert_one({
                    "chat_id": str(chat_id),
                    "action_type": f"blocklist_{action}",
                    "performed_by": "system",
                    "target_user": str(user_id),
                    "metadata": {
                        "trigger": trigger,
                        "reason": reason,
                        "message_text": message_text[:100]  # First 100 chars
                    },
                    "timestamp": datetime.now(timezone.utc)
                })
                
                logger.info(
                    f"Blocklist violation in chat {chat_id}: user {user_id} "
                    f"matched trigger '{trigger}'"
                )
                
                return False  # Stop processing
        
        return True
        
    except Exception as e:
        logger.error(f"Error in blocklist checker: {e}")
        return True


async def delete_after_delay(message, seconds: int):
    """Helper to delete a message after a delay"""
    import asyncio
    try:
        await asyncio.sleep(seconds)
        await message.delete()
    except Exception:
        pass

