"""
Pin/Unpin commands - Pin messages in groups
"""
import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "pin",
    "description": "Pin a message in the chat",
    "usage": "/pin [notify] - Reply to a message to pin it\n"
             "/pin [notify] - Pin with notification (default: silent)",
    "category": "pins",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_pin_messages"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /pin command
    
    Pin a message in the chat.
    """
    chat_id = update.effective_chat.id
    
    # Must be a reply to a message
    if not update.message.reply_to_message:
        await update.message.reply_html(
            "❌ <b>Reply to a message to pin it</b>\n\n"
            "<b>Usage:</b>\n"
            "• Reply to any message with <code>/pin</code>\n"
            "• Use <code>/pin notify</code> to notify all members"
        )
        return
    
    message_to_pin = update.message.reply_to_message
    
    # Check if notification should be sent
    notify = False
    if context.args and context.args[0].lower() in ['notify', 'loud', 'notification']:
        notify = True
    
    try:
        # Pin the message
        await context.bot.pin_chat_message(
            chat_id=chat_id,
            message_id=message_to_pin.message_id,
            disable_notification=not notify
        )
        
        notification_text = " (with notification)" if notify else " (silently)"
        await update.message.reply_html(
            f"📌 <b>Message pinned{notification_text}</b>"
        )
        
        # Log action
        db = context.application.bot_data.get('database')
        if db is not None:
            await db.action_logs.insert_one({
                "chat_id": str(chat_id),
                "action_type": "pin",
                "message_id": message_to_pin.message_id,
                "notify": notify,
                "performed_by": str(update.effective_user.id),
                "timestamp": datetime.now(timezone.utc)
            })
        
        logger.info(
            f"Pinned message {message_to_pin.message_id} in chat {chat_id} "
            f"(notify: {notify})"
        )
        
    except TelegramError as e:
        logger.error(f"Failed to pin message in chat {chat_id}: {e}")
        await update.message.reply_html(
            f"❌ <b>Failed to pin message</b>\n\n"
            f"Error: {str(e)}"
        )