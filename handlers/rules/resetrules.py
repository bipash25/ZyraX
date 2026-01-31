"""
Reset Rules command - Clear chat rules
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timezone

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "resetrules",
    "aliases": ["clear_rules"],
    "description": "Clear chat rules",
    "usage": "/resetrules - Remove the chat rules",
    "category": "rules"
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /resetrules command
    
    Removes the rules for the chat
    """
    chat_id = update.effective_chat.id
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Check if rules exist
    chat_doc = await db.chats.find_one({"_id": str(chat_id)})
    
    if not chat_doc or not chat_doc.get('rules'):
        await update.message.reply_text("❌ No rules are set for this chat.")
        return
    
    # Remove rules
    await db.chats.update_one(
        {"_id": str(chat_id)},
        {
            "$unset": {"rules": ""},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    
    await update.message.reply_text("✅ Chat rules have been cleared.")
    
    logger.info(f"Rules cleared in chat {chat_id}")

