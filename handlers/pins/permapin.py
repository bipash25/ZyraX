"""
Permapin command - Permanently pin a message (prevent silent unpin)
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
    "name": "permapin",
    "description": "Pin a message permanently (prevents channel auto-unpin)",
    "usage": "/permapin [notify] - Reply to a message to pin it permanently\n"
             "/permapin [notify] - Pin with notification (default: silent)\n\n"
             "This prevents the message from being unpinned by linked channels",
    "category": "pins",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_pin_messages"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /permapin command
    
    Pin a message permanently by storing its ID in the database.
    Bot will automatically re-pin it if it gets unpinned.
    """
    chat_id = update.effective_chat.id
    
    # Must be a reply to a message
    if not update.message.reply_to_message:
        await update.message.reply_html(
            "❌ <b>Reply to a message to permapin it</b>\n\n"
            "<b>Usage:</b>\n"
            "• Reply to any message with <code>/permapin</code>\n"
            "• Use <code>/permapin notify</code> to notify all members\n\n"
            "<b>Note:</b> Permapin prevents linked channels from unpinning messages"
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
        
        # Store permapin info in database
        db = context.application.bot_data.get('database')
        if db is not None:
            # Update or insert permapin setting
            await db.chats.update_one(
                {"_id": str(chat_id)},
                {
                    "$set": {
                        "permapin_message_id": message_to_pin.message_id,
                        "permapin_enabled": True,
                        "permapin_set_by": str(update.effective_user.id),
                        "permapin_set_at": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
            
            # Log action
            await db.action_logs.insert_one({
                "chat_id": str(chat_id),
                "action_type": "permapin",
                "message_id": message_to_pin.message_id,
                "notify": notify,
                "performed_by": str(update.effective_user.id),
                "timestamp": datetime.now(timezone.utc)
            })
        
        notification_text = " (with notification)" if notify else " (silently)"
        await update.message.reply_html(
            f"📌 <b>Message permanently pinned{notification_text}</b>\n\n"
            f"This message will be automatically re-pinned if unpinned by linked channels.\n\n"
            f"<b>To remove permapin:</b>\n"
            f"Use <code>/unpermapin</code>"
        )
        
        logger.info(
            f"Permapinned message {message_to_pin.message_id} in chat {chat_id} "
            f"(notify: {notify})"
        )
        
    except TelegramError as e:
        logger.error(f"Failed to permapin message in chat {chat_id}: {e}")
        await update.message.reply_html(
            f"❌ <b>Failed to permapin message</b>\n\n"
            f"Error: {str(e)}"
        )