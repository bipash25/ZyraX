"""
Antiraid middleware - Automatically restrict new members during raids
"""
import logging
from datetime import datetime, timezone
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus

logger = logging.getLogger(__name__)


async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle new chat members - restrict them if antiraid is enabled
    
    This is called when a new member joins the chat.
    If antiraid mode is active, the new member is automatically muted.
    
    Args:
        update: Telegram update
        context: PTB context
    """
    # Only process chat_member updates for new joins
    if not update.chat_member:
        return
    
    chat_member_update = update.chat_member
    old_status = chat_member_update.old_chat_member.status
    new_status = chat_member_update.new_chat_member.status
    
    # Check if this is actually a new member join
    if old_status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return  # Already was a member
    
    if new_status not in [ChatMemberStatus.MEMBER]:
        return  # Not a regular member join
    
    chat = chat_member_update.chat
    new_member = chat_member_update.new_chat_member.user
    
    # Don't restrict bots
    if new_member.is_bot:
        return
    
    chat_id = chat.id
    user_id = new_member.id
    
    try:
        # Check if antiraid is enabled
        db = context.application.bot_data.get('database')
        if db is None:
            return
        
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        
        if not chat_doc or not chat_doc.get('antiraid_enabled', False):
            return  # Antiraid not active
        
        # Check if antiraid has expired
        expires = chat_doc.get('antiraid_expires')
        if expires and expires < datetime.now(timezone.utc):
            # Expired, disable it
            await db.chats.update_one(
                {"_id": str(chat_id)},
                {"$set": {"antiraid_enabled": False}}
            )
            return
        
        # Restrict the new member
        await chat.restrict_member(
            user_id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_audios=False,
                can_send_documents=False,
                can_send_photos=False,
                can_send_videos=False,
                can_send_video_notes=False,
                can_send_voice_notes=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
                can_manage_topics=False
            ),
            until_date=None  # Permanent until manually unmuted
        )
        
        # Send notification
        try:
            notification = await context.bot.send_message(
                chat_id,
                f"🛡️ <b>Antiraid Active</b>\n\n"
                f"User {new_member.mention_html()} has been automatically restricted.\n"
                f"An admin can approve them with /approve",
                parse_mode='HTML'
            )
            
            # Auto-delete notification after 30 seconds
            import asyncio
            asyncio.create_task(delete_after_delay(notification, 30))
            
        except Exception as e:
            logger.debug(f"Could not send antiraid notification: {e}")
        
        logger.info(
            f"Antiraid: Restricted new member {user_id} in chat {chat_id}"
        )
        
        # Log to database
        if db is not None:
            await db.action_logs.insert_one({
                "chat_id": str(chat_id),
                "action_type": "antiraid_restrict",
                "performed_by": "system",
                "target_user": str(user_id),
                "metadata": {
                    "username": new_member.username,
                    "first_name": new_member.first_name
                },
                "timestamp": datetime.now(timezone.utc)
            })
        
    except Exception as e:
        logger.error(f"Error in antiraid check for chat {chat_id}: {e}")


async def delete_after_delay(message, seconds: int):
    """Helper to delete a message after a delay"""
    import asyncio
    try:
        await asyncio.sleep(seconds)
        await message.delete()
    except Exception:
        pass