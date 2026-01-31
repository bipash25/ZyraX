"""
Clearall command - Remove all notes from the chat
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "clearall",
    "description": "Remove all notes from the chat",
    "usage": "/clearall - Delete all saved notes",
    "category": "notes",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /clearall command
    
    Remove all notes from the chat.
    """
    chat_id = update.effective_chat.id
    
    # Get count of notes first
    db = context.application.bot_data.get('database')
    if db is not None:
        count = await db.notes.count_documents({"chat_id": str(chat_id)})
        
        if count == 0:
            await update.message.reply_html(
                "ℹ️ <b>No notes to remove</b>\n\n"
                "This chat has no saved notes."
            )
            return
        
        # Remove all notes
        result = await db.notes.delete_many({"chat_id": str(chat_id)})
        
        if result.deleted_count > 0:
            await update.message.reply_html(
                f"✅ <b>All notes removed</b>\n\n"
                f"Deleted {result.deleted_count} note(s) from this chat."
            )
            
            logger.info(
                f"All notes removed from chat {chat_id} by user {update.effective_user.id} "
                f"(count: {result.deleted_count})"
            )
        else:
            await update.message.reply_html(
                "❌ <b>Failed to remove notes</b>"
            )
    else:
        await update.message.reply_html(
            "❌ <b>Database connection error</b>"
        )