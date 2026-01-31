"""
Filter trigger middleware - Automatically respond to filter triggers
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from utils.message_parser import parse_buttons, format_welcome_message

logger = logging.getLogger(__name__)


async def check_filter_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Check if a message contains a filter trigger and respond accordingly
    
    This middleware runs on all text messages to detect filter triggers.
    """
    try:
        # Only process text messages in groups
        if not update.message or not update.message.text:
            return
        
        if not update.effective_chat or update.effective_chat.type not in ['group', 'supergroup']:
            return
        
        chat_id = update.effective_chat.id
        message_text = update.message.text.lower().strip()
        
        # Get database
        db = context.application.bot_data.get('database')
        if db is None:
            return
        
        # Check if any filter matches
        # Try exact match first, then word match
        filter_doc = await db.filters.find_one({
            "chat_id": str(chat_id),
            "trigger": message_text
        })
        
        # If no exact match, check if trigger is a word in the message
        if not filter_doc:
            words = message_text.split()
            for word in words:
                filter_doc = await db.filters.find_one({
                    "chat_id": str(chat_id),
                    "trigger": word
                })
                if filter_doc:
                    break
        
        if not filter_doc:
            return
        
        # Filter found, send response
        response_text = filter_doc.get('response_text')
        file_id = filter_doc.get('file_id')
        file_type = filter_doc.get('file_type')
        
        # Format message with variables
        user = update.effective_user
        chat = update.effective_chat
        
        formatted_text = response_text
        keyboard = None
        
        if response_text:
            formatted_text, keyboard = format_welcome_message(
                template=response_text,
                user_first=user.first_name,
                user_last=user.last_name or "",
                user_username=user.username or "",
                user_id=user.id,
                chat_name=chat.title or "",
                member_count=0  # Can be populated if needed
            )
        
        # Send response based on type
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
                # Text only response
                if formatted_text:
                    await update.message.reply_html(
                        formatted_text,
                        reply_markup=keyboard
                    )
            
            logger.debug(
                f"Filter triggered: '{filter_doc['trigger']}' in chat {chat_id}"
            )
        
        except TelegramError as e:
            logger.error(f"Failed to send filter response in chat {chat_id}: {e}")
    
    except Exception as e:
        logger.error(f"Error in filter trigger middleware: {e}")