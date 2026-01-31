"""
Purge command - Delete multiple messages at once
Supports: /purge, /del
"""
import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, require_bot_admin, log_command

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "purge",
    "aliases": ["del"],
    "description": "Delete messages in bulk",
    "usage": "/purge - Reply to a message to delete all messages from that message to latest\n"
             "/del - Reply to a message to delete only that message",
    "category": "moderation",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_delete_messages"])
@require_bot_admin(permissions=["can_delete_messages"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /purge and /del commands
    
    /purge: Delete all messages from replied message to current
    /del: Delete only the replied message
    
    Args:
        update: Telegram update
        context: PTB context
    """
    chat_id = update.effective_chat.id
    admin_user = update.effective_user
    message = update.effective_message
    
    # Get command
    command = message.text.split()[0].lower().lstrip('/')
    is_del = command == "del"
    
    # Check if replying to a message
    if not message.reply_to_message:
        await message.reply_html(
            "❌ <b>Please reply to a message to use this command.</b>\n\n"
            "<b>Usage:</b>\n"
            "• /purge - Delete from replied message to latest\n"
            "• /del - Delete only the replied message"
        )
        return
    
    start_message_id = message.reply_to_message.message_id
    end_message_id = message.message_id
    
    try:
        deleted_count = 0
        failed_count = 0
        
        if is_del:
            # Delete only the replied message
            try:
                await context.bot.delete_message(chat_id, start_message_id)
                deleted_count = 1
            except Exception as e:
                logger.debug(f"Failed to delete message {start_message_id}: {e}")
                failed_count = 1
            
            # Delete command message
            try:
                await message.delete()
            except Exception:
                pass
        else:
            # Purge all messages in range
            # Note: Can only delete messages less than 48 hours old
            for msg_id in range(start_message_id, end_message_id + 1):
                try:
                    await context.bot.delete_message(chat_id, msg_id)
                    deleted_count += 1
                except Exception as e:
                    logger.debug(f"Failed to delete message {msg_id}: {e}")
                    failed_count += 1
        
        # Send status message (will auto-delete after 5 seconds)
        if not is_del:
            status_text = f"🗑️ <b>Purge complete!</b>\n\n"
            status_text += f"✅ Deleted: {deleted_count} messages"
            
            if failed_count > 0:
                status_text += f"\n❌ Failed: {failed_count} messages"
                status_text += f"\n\n<i>Note: Cannot delete messages older than 48 hours</i>"
            
            try:
                status_msg = await message.reply_html(status_text)
                
                # Schedule deletion of status message after 5 seconds
                try:
                    import asyncio
                    await asyncio.sleep(5)
                    await status_msg.delete()
                except Exception:
                    pass
            except Exception as e:
                logger.debug(f"Could not send status message: {e}")
        
        # Log to database
        try:
            db = context.application.bot_data.get('database')
            if db is not None:
                await db.action_logs.insert_one({
                    "chat_id": str(chat_id),
                    "action_type": "purge" if not is_del else "delete",
                    "performed_by": str(admin_user.id),
                    "metadata": {
                        "deleted_count": deleted_count,
                        "failed_count": failed_count,
                        "start_message_id": start_message_id,
                        "end_message_id": end_message_id
                    },
                    "timestamp": datetime.now(timezone.utc)
                })
        except Exception as e:
            logger.error(f"Error logging purge action: {e}")
        
        logger.info(
            f"Purge in chat {chat_id} by admin {admin_user.id}: "
            f"{deleted_count} deleted, {failed_count} failed"
        )
        
    except Exception as e:
        logger.error(f"Error purging messages in chat {chat_id}: {e}")
        await message.reply_html(
            f"❌ <b>Failed to purge messages.</b>\n\n"
            f"Error: {str(e)}"
        )