"""
Unpinall command - Unpin all pinned messages in the chat
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
    "name": "unpinall",
    "description": "Unpin all pinned messages in the chat",
    "usage": "/unpinall - Remove all pinned messages",
    "category": "pins",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_pin_messages"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /unpinall command
    
    Unpin all messages in the chat.
    """
    chat_id = update.effective_chat.id
    
    try:
        # Unpin all messages
        await context.bot.unpin_all_chat_messages(chat_id=chat_id)
        
        await update.message.reply_html(
            "📌 <b>All pinned messages have been unpinned</b>"
        )
        
        # Log action
        db = context.application.bot_data.get('database')
        if db is not None:
            await db.action_logs.insert_one({
                "chat_id": str(chat_id),
                "action_type": "unpinall",
                "performed_by": str(update.effective_user.id),
                "timestamp": datetime.now(timezone.utc)
            })
        
        logger.info(f"Unpinned all messages in chat {chat_id}")
        
    except TelegramError as e:
        logger.error(f"Failed to unpin all messages in chat {chat_id}: {e}")
        
        # Check if there are no pinned messages
        if "no pinned message" in str(e).lower():
            await update.message.reply_html(
                "❌ <b>No pinned messages found</b>"
            )
        else:
            await update.message.reply_html(
                f"❌ <b>Failed to unpin all messages</b>\n\n"
                f"Error: {str(e)}"
            )