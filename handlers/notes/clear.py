"""
Clear command - Remove a saved note
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "clear",
    "description": "Remove a saved note",
    "usage": "/clear <notename> - Delete the specified note",
    "category": "notes",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /clear command
    
    Remove a note from the chat.
    """
    chat_id = update.effective_chat.id
    
    # Check if note name provided
    if not context.args:
        await update.message.reply_html(
            "❌ <b>Please specify which note to remove</b>\n\n"
            "<b>Usage:</b> <code>/clear &lt;notename&gt;</code>\n\n"
            "Use <code>/notes</code> to see all saved notes."
        )
        return
    
    # Get note name (lowercase for case-insensitive matching)
    note_name = ' '.join(context.args).lower().strip()
    
    # Remove # prefix if present
    if note_name.startswith('#'):
        note_name = note_name[1:]
    
    # Remove note from database
    db = context.application.bot_data.get('database')
    if db is not None:
        result = await db.notes.delete_one({
            "chat_id": str(chat_id),
            "name": note_name
        })
        
        if result.deleted_count > 0:
            await update.message.reply_html(
                f"✅ <b>Note removed</b>\n\n"
                f"Note '<code>{note_name}</code>' has been deleted."
            )
            
            logger.info(
                f"Note removed: '{note_name}' from chat {chat_id} by user {update.effective_user.id}"
            )
        else:
            await update.message.reply_html(
                f"❌ <b>Note not found</b>\n\n"
                f"No note with name '<code>{note_name}</code>' exists.\n\n"
                f"Use <code>/notes</code> to see all saved notes."
            )
    else:
        await update.message.reply_html(
            "❌ <b>Database connection error</b>"
        )