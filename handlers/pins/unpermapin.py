"""
Unpermapin command - Disable permanent pin for a message
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
    "name": "unpermapin",
    "description": "Disable permanent pin for the current message",
    "usage": "/unpermapin - Disable permapin protection",
    "category": "pins",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_pin_messages"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /unpermapin command
    
    Disable permanent pin for the chat.
    """
    chat_id = update.effective_chat.id
    
    try:
        # Check if permapin is enabled
        db = context.application.bot_data.get('database')
        if db is not None:
            chat_settings = await db.chats.find_one({"_id": str(chat_id)})
            
            if not chat_settings or not chat_settings.get("permapin_enabled"):
                await update.message.reply_html(
                    "❌ <b>Permapin is not enabled in this chat</b>\n\n"
                    "Use <code>/permapin</code> to enable it."
                )
                return
            
            # Disable permapin
            await db.chats.update_one(
                {"_id": str(chat_id)},
                {
                    "$set": {
                        "permapin_enabled": False,
                        "permapin_disabled_by": str(update.effective_user.id),
                        "permapin_disabled_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # Log action
            await db.action_logs.insert_one({
                "chat_id": str(chat_id),
                "action_type": "unpermapin",
                "performed_by": str(update.effective_user.id),
                "timestamp": datetime.now(timezone.utc)
            })
            
            message_id = chat_settings.get("permapin_message_id")
            
            await update.message.reply_html(
                "📌 <b>Permapin disabled</b>\n\n"
                f"The message will no longer be automatically re-pinned.\n\n"
                f"<b>Note:</b> The message is still pinned. Use <code>/unpin</code> to unpin it."
            )
            
            logger.info(f"Disabled permapin in chat {chat_id}")
        else:
            await update.message.reply_html(
                "❌ <b>Database connection error</b>"
            )
        
    except TelegramError as e:
        logger.error(f"Failed to disable permapin in chat {chat_id}: {e}")
        await update.message.reply_html(
            f"❌ <b>Failed to disable permapin</b>\n\n"
            f"Error: {str(e)}"
        )