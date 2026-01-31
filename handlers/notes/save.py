"""
Save command - Save a note for the chat
"""
import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command
from utils.message_parser import extract_filter_content

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "save",
    "description": "Save a note that can be retrieved later",
    "usage": "/save <notename> - Reply to a message to save it as a note\n\n"
             "<b>Features:</b>\n"
             "• Supports text, media, buttons\n"
             "• Use variables: {first}, {last}, {mention}, {username}\n"
             "• Add buttons: [Text](buttonurl://url)\n"
             "• Retrieve with /get or #notename\n\n"
             "<b>Examples:</b>\n"
             "• <code>/save rules</code> - Save chat rules\n"
             "• <code>/save welcome</code> - Save welcome message",
    "category": "notes",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /save command
    
    Save a note that can be retrieved with /get or #notename.
    """
    chat_id = update.effective_chat.id
    
    # Check if note name provided
    if not context.args:
        await update.message.reply_html(
            "❌ <b>Please specify a note name</b>\n\n"
            "<b>Usage:</b> <code>/save &lt;notename&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "Reply to a message with <code>/save rules</code>"
        )
        return
    
    # Get note name (lowercase for case-insensitive matching)
    note_name = ' '.join(context.args).lower().strip()
    
    # Validate note name (alphanumeric and underscore only)
    if not note_name.replace('_', '').replace('-', '').isalnum():
        await update.message.reply_html(
            "❌ <b>Invalid note name</b>\n\n"
            "Note names can only contain letters, numbers, hyphens, and underscores.\n\n"
            "<b>Examples:</b>\n"
            "✅ rules\n"
            "✅ welcome_message\n"
            "✅ faq-2024\n"
            "❌ rules!"
        )
        return
    
    # Must be a reply to set the content
    if not update.message.reply_to_message:
        await update.message.reply_html(
            "❌ <b>Reply to a message to save it as a note</b>\n\n"
            f"<b>Note name:</b> <code>{note_name}</code>\n\n"
            "<b>How to use:</b>\n"
            "1. Type the message you want to save\n"
            "2. Reply to it with <code>/save {note_name}</code>"
        )
        return
    
    reply_msg = update.message.reply_to_message
    
    # Extract content from reply
    content = extract_filter_content(reply_msg)
    
    # Validate content
    if not content['text'] and not content['file_id']:
        await update.message.reply_html(
            "❌ <b>Reply message must contain text or media</b>"
        )
        return
    
    # Save note to database
    db = context.application.bot_data.get('database')
    if db is not None:
        # Check if note already exists
        existing = await db.notes.find_one({
            "chat_id": str(chat_id),
            "name": note_name
        })
        
        note_doc = {
            "chat_id": str(chat_id),
            "name": note_name,
            "content": content['text'],
            "file_id": content['file_id'],
            "file_type": content['file_type'],
            "created_by": str(update.effective_user.id),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        if existing:
            # Update existing note
            await db.notes.update_one(
                {
                    "chat_id": str(chat_id),
                    "name": note_name
                },
                {"$set": note_doc}
            )
            action = "updated"
        else:
            # Create new note
            await db.notes.insert_one(note_doc)
            action = "saved"
        
        # Build response message
        response = f"✅ <b>Note {action}</b>\n\n"
        response += f"<b>Name:</b> <code>{note_name}</code>\n"
        response += f"<b>Type:</b> {content['type']}\n\n"
        response += f"<b>Retrieve with:</b>\n"
        response += f"• <code>/get {note_name}</code>\n"
        response += f"• <code>#{note_name}</code>"
        
        if content['text']:
            # Show preview (truncated)
            preview = content['text'][:100]
            if len(content['text']) > 100:
                preview += "..."
            response += f"\n\n<b>Preview:</b>\n{preview}"
        
        await update.message.reply_html(response)
        
        logger.info(
            f"Note {action}: '{note_name}' in chat {chat_id} by user {update.effective_user.id}"
        )
    else:
        await update.message.reply_html(
            "❌ <b>Database connection error</b>"
        )