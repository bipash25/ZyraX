"""
Federation ban checker middleware
Automatically bans users who join if they're federation-banned
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus

logger = logging.getLogger(__name__)


async def check_federation_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Check if new member is federation-banned
    
    This runs when a new member joins a federated chat.
    If they're fbanned, immediately ban them.
    """
    # Only process chat_member updates for new joins
    if not update.chat_member:
        return
    
    chat_member_update = update.chat_member
    old_status = chat_member_update.old_chat_member.status
    new_status = chat_member_update.new_chat_member.status
    
    # Check if this is a new member join
    if old_status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return  # Already was a member
    
    if new_status not in [ChatMemberStatus.MEMBER]:
        return  # Not a regular member join
    
    chat = chat_member_update.chat
    new_member = chat_member_update.new_chat_member.user
    
    # Don't check bots
    if new_member.is_bot:
        return
    
    chat_id = chat.id
    user_id = new_member.id
    
    try:
        db = context.application.bot_data.get('database')
        if db is None:
            return
        
        # Get chat's federation
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        
        if not chat_doc or not chat_doc.get('fed_id'):
            return  # Chat not in a federation
        
        fed_id = chat_doc['fed_id']
        
        # Get federation
        federation = await db.federations.find_one({"_id": fed_id})
        
        if not federation:
            return
        
        # Check if user is federation-banned
        is_fbanned = any(
            ban['user_id'] == str(user_id)
            for ban in federation.get('banned_users', [])
        )
        
        if is_fbanned:
            # Get ban info
            ban_info = next(
                ban for ban in federation['banned_users']
                if ban['user_id'] == str(user_id)
            )
            
            reason = ban_info.get('reason', 'No reason')
            banned_by = ban_info.get('banned_by_name', 'Unknown')
            
            # Ban the user
            await chat.ban_member(user_id)
            
            # Send notification
            try:
                notification = await context.bot.send_message(
                    chat_id,
                    f"🚫 <b>Federation Ban Enforced</b>\n\n"
                    f"User {new_member.mention_html()} is federation-banned and was automatically removed.\n\n"
                    f"<b>Federation:</b> {federation['name']}\n"
                    f"<b>Reason:</b> {reason}\n"
                    f"<b>Banned by:</b> {banned_by}",
                    parse_mode='HTML'
                )
                
                # Auto-delete after 30 seconds
                import asyncio
                asyncio.create_task(delete_after_delay(notification, 30))
                
            except Exception as e:
                logger.debug(f"Could not send federation ban notification: {e}")
            
            logger.info(
                f"Federation ban enforced: User {user_id} auto-banned in chat {chat_id} "
                f"(federation {fed_id})"
            )
    
    except Exception as e:
        logger.error(f"Error in federation ban checker: {e}")


async def delete_after_delay(message, seconds: int):
    """Helper to delete a message after a delay"""
    import asyncio
    try:
        await asyncio.sleep(seconds)
        await message.delete()
    except Exception:
        pass

