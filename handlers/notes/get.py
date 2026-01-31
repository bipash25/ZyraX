"""
Get command - Retrieve a saved note
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from core.decorators import group_only
from utils.message_parser import format_welcome_message

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "get",
    "description": "Retrieve a saved note",
    "usage": "/get <notename> - Get the specified note\n\n"
             "You can also use #notename as a shortcut",
    "category": "notes",
    "scope": ["group", "supergroup"]
}


@group_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /get command
    
    Retrieve and display a saved note.
    """
    chat_id = update.effective_chat.id
    
    # Check if note name provided
    if not context.args:
        await update.message.reply_html(
            "❌ <b>Please specify a note name</b>\n\n"
            "<b>Usage:</b> <code>/get &lt;notename&gt;</code>\n\n"
            "Use <code>/notes</code> to see all saved notes."
        )
        return
    
    # Get note name (lowercase for case-insensitive matching)
    note_name = ' '.join(context.args).lower().strip()
    
    # Remove # prefix if present
    if note_name.startswith('#'):
        note_name = note_name[1:]
    
    # Retrieve note from database
    db = context.application.bot_data.get('database')
    if db is not None:
        note_doc = await db.notes.find_one({
            "chat_id": str(chat_id),
            "name": note_name
        })
        
        if not note_doc:
            await update.message.reply_html(
                f"❌ <b>Note not found</b>\n\n"
                f"No note with name '<code>{note_name}</code>' exists.\n\n"
                f"Use <code>/notes</code> to see all available notes."
            )
            return
        
        # Format content with variables
        content_text = note_doc.get('content')
        file_id = note_doc.get('file_id')
        file_type = note_doc.get('file_type')
        
        user = update.effective_user
        chat = update.effective_chat
        
        formatted_text = None
        keyboard = None
        
        if content_text:
            formatted_text, keyboard = format_welcome_message(
                template=content_text,
                user_first=user.first_name,
                user_last=user.last_name or "",
                user_username=user.username or "",
                user_id=user.id,
                chat_name=chat.title or "",
                member_count=0  # Can be populated if needed
            )
        
        # Send note based on type
        try:
            if file_type == 'photo':
                await update.message.reply_photo(
                    photo=file_id,
                    caption=formatted_text if formatted_text else None,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            elif file_type == 'video':
                await update.message.reply_video(
                    video=file_id,
                    caption=formatted_text if formatted_text else None,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            elif file_type == 'document':
                await update.message.reply_document(
                    document=file_id,
                    caption=formatted_text if formatted_text else None,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            elif file_type == 'audio':
                await update.message.reply_audio(
                    audio=file_id,
                    caption=formatted_text if formatted_text else None,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            elif file_type == 'voice':
                await update.message.reply_voice(
                    voice=file_id,
                    caption=formatted_text if formatted_text else None,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            elif file_type == 'video_note':
                await update.message.reply_video_note(
                    video_note=file_id,
                    reply_markup=keyboard
                )
            elif file_type == 'sticker':
                await update.message.reply_sticker(
                    sticker=file_id,
                    reply_markup=keyboard
                )
            elif file_type == 'animation':
                await update.message.reply_animation(
                    animation=file_id,
                    caption=formatted_text if formatted_text else None,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            else:
                # Text only note
                if formatted_text:
                    await update.message.reply_html(
                        formatted_text,
                        reply_markup=keyboard
                    )
            
            logger.debug(f"Note retrieved: '{note_name}' in chat {chat_id}")
        
        except TelegramError as e:
            logger.error(f"Failed to send note in chat {chat_id}: {e}")
            await update.message.reply_html(
                f"❌ <b>Failed to send note</b>\n\n"
                f"Error: {str(e)}"
            )
    else:
        await update.message.reply_html(
            "❌ <b>Database connection error</b>"
        )