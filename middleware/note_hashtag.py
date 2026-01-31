"""
Note hashtag middleware - Automatically respond to #notename triggers
"""
import logging
import re
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from utils.message_parser import format_welcome_message

logger = logging.getLogger(__name__)


async def check_note_hashtag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Check if a message contains #notename and respond with the note
    
    This middleware runs on all text messages to detect hashtag triggers.
    """
    try:
        # Only process text messages in groups
        if not update.message or not update.message.text:
            return
        
        if not update.effective_chat or update.effective_chat.type not in ['group', 'supergroup']:
            return
        
        chat_id = update.effective_chat.id
        message_text = update.message.text
        
        # Find all hashtags in the message using regex
        # Pattern matches #word (letters, numbers, hyphens, underscores)
        hashtag_pattern = r'#([a-zA-Z0-9_-]+)'
        hashtags = re.findall(hashtag_pattern, message_text)
        
        if not hashtags:
            return
        
        # Get database
        db = context.application.bot_data.get('database')
        if db is None:
            return
        
        # Try to find a note matching any of the hashtags
        # Convert to lowercase for case-insensitive matching
        for hashtag in hashtags:
            note_name = hashtag.lower()
            
            note_doc = await db.notes.find_one({
                "chat_id": str(chat_id),
                "name": note_name
            })
            
            if note_doc:
                # Note found, send it
                await send_note(update, context, note_doc)
                # Only send the first matching note
                break
    
    except Exception as e:
        logger.error(f"Error in note hashtag middleware: {e}")


async def send_note(update: Update, context: ContextTypes.DEFAULT_TYPE, note_doc: dict) -> None:
    """
    Send a note to the chat
    
    Args:
        update: Telegram update
        context: Bot context
        note_doc: Note document from database
    """
    try:
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
                member_count=0
            )
        
        # Send note based on type
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
        
        logger.debug(
            f"Note hashtag triggered: '{note_doc['name']}' in chat {update.effective_chat.id}"
        )
    
    except TelegramError as e:
        logger.error(f"Failed to send note via hashtag: {e}")