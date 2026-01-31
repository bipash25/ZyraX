"""
Unset Log Channel command
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timezone

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "unsetlog",
    "aliases": [],
    "description": "Remove log channel",
    "usage": "/unsetlog - Stop logging to channel",
    "category": "logs"
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove log channel"""
    chat_id = update.effective_chat.id
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Check if log channel is set
    chat_doc = await db.chats.find_one({"_id": str(chat_id)})
    
    if not chat_doc or not chat_doc.get('log_channel_id'):
        await update.message.reply_text("❌ No log channel is set.")
        return
    
    # Remove log channel
    await db.chats.update_one(
        {"_id": str(chat_id)},
        {
            "$unset": {"log_channel_id": ""},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    
    await update.message.reply_text("✅ Log channel removed.")
    
    logger.info(f"Log channel removed for chat {chat_id}")

