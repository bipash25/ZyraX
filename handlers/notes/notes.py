"""
Notes command - List all saved notes in the chat
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "notes",
    "description": "List all saved notes in the chat",
    "usage": "/notes - Show all note names",
    "category": "notes",
    "scope": ["group", "supergroup"]
}


@group_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /notes command
    
    List all saved notes in the current chat.
    """
    chat_id = update.effective_chat.id
    
    # Get all notes for this chat
    db = context.application.bot_data.get('database')
    if db is not None:
        notes = await db.notes.find({"chat_id": str(chat_id)}).to_list(length=None)
        
        if not notes:
            await update.message.reply_html(
                "ℹ️ <b>No notes saved in this chat</b>\n\n"
                "Use <code>/save &lt;notename&gt;</code> to create one."
            )
            return
        
        # Build response message
        response = f"📝 <b>Saved Notes ({len(notes)})</b>\n\n"
        
        # Group notes by type
        text_notes = []
        media_notes = []
        
        for note in notes:
            name = note['name']
            if note.get('file_id'):
                media_type = note.get('file_type', 'media')
                media_notes.append(f"• <code>#{name}</code> ({media_type})")
            else:
                text_notes.append(f"• <code>#{name}</code>")
        
        if text_notes:
            response += "<b>Text Notes:</b>\n"
            response += "\n".join(text_notes)
            response += "\n\n"
        
        if media_notes:
            response += "<b>Media Notes:</b>\n"
            response += "\n".join(media_notes)
            response += "\n\n"
        
        response += "<b>Usage:</b>\n"
        response += "• Type <code>#notename</code> to retrieve a note\n"
        response += "• Use <code>/get notename</code> as alternative\n"
        response += "• Use <code>/clear notename</code> to remove a note"
        
        await update.message.reply_html(response)
        
        logger.info(f"Listed {len(notes)} notes for chat {chat_id}")
    else:
        await update.message.reply_html(
            "❌ <b>Database connection error</b>"
        )