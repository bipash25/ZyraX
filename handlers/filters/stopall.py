"""
Stopall command - Remove all filters from the chat
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "stopall",
    "description": "Remove all filters from the chat",
    "usage": "/stopall - Delete all filter triggers",
    "category": "filters",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /stopall command
    
    Remove all filters from the chat.
    """
    chat_id = update.effective_chat.id
    
    # Get count of filters first
    db = context.application.bot_data.get('database')
    if db is not None:
        count = await db.filters.count_documents({"chat_id": str(chat_id)})
        
        if count == 0:
            await update.message.reply_html(
                "ℹ️ <b>No filters to remove</b>\n\n"
                "This chat has no active filters."
            )
            return
        
        # Remove all filters
        result = await db.filters.delete_many({"chat_id": str(chat_id)})
        
        if result.deleted_count > 0:
            await update.message.reply_html(
                f"✅ <b>All filters removed</b>\n\n"
                f"Deleted {result.deleted_count} filter(s) from this chat."
            )
            
            logger.info(
                f"All filters removed from chat {chat_id} by user {update.effective_user.id} "
                f"(count: {result.deleted_count})"
            )
        else:
            await update.message.reply_html(
                "❌ <b>Failed to remove filters</b>"
            )
    else:
        await update.message.reply_html(
            "❌ <b>Database connection error</b>"
        )