"""
Locks enforcement middleware - Check and delete locked content types
"""
import logging
import re
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus

logger = logging.getLogger(__name__)


async def check_locks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Middleware to check if message violates any locks
    
    Deletes messages that violate lock settings.
    PTB middleware - doesn't return anything.
    """
    # Only check regular messages in groups
    if not update.message or not update.effective_chat or update.effective_chat.type == 'private':
        return
    
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    
    # Don't check messages from bots or channels
    if not user or user.is_bot:
        return
    
    chat_id = chat.id
    user_id = user.id
    
    try:
        # Get database
        db = context.application.bot_data.get('database')
        if db is None:
            return
        
        # Check if user is admin (admins bypass locks)
        try:
            chat_member = await chat.get_member(user_id)
            if chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                return
        except Exception:
            pass
        
        # Check if user is approved (approved users bypass locks)
        user_doc = await db.users.find_one({"_id": str(user_id)})
        if user_doc and user_doc.get('chat_data', {}).get(str(chat_id), {}).get('approved', False):
            return
        
        # Get chat locks
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        if not chat_doc or not chat_doc.get('locks'):
            return
        
        locks = chat_doc.get('locks', {})
        
        # Check each lock type
        violation = None
        
        # Media locks
        if locks.get('photo') and message.photo:
            violation = "photos"
        elif locks.get('video') and message.video:
            violation = "videos"
        elif locks.get('audio') and message.audio:
            violation = "audio files"
        elif locks.get('document') and message.document:
            violation = "documents"
        elif locks.get('sticker') and message.sticker:
            violation = "stickers"
        elif locks.get('animation') and message.animation:
            violation = "GIFs"
        elif locks.get('voice') and message.voice:
            violation = "voice messages"
        elif locks.get('video_note') and message.video_note:
            violation = "video notes"
        
        # Message type locks
        elif locks.get('text') and message.text and not message.text.startswith('/'):
            violation = "text messages"
        
        elif locks.get('url') and message.text:
            # Check for URLs
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            if re.search(url_pattern, message.text, re.IGNORECASE):
                violation = "URLs"
            elif message.entities:
                for entity in message.entities:
                    if entity.type in ['url', 'text_link']:
                        violation = "URLs"
                        break
        
        elif locks.get('forward') and message.forward_date:
            violation = "forwarded messages"
        
        elif locks.get('mention') and message.text:
            if '@' in message.text or (message.entities and any(e.type == 'mention' for e in message.entities)):
                violation = "mentions"
        
        elif locks.get('hashtag') and message.text:
            if '#' in message.text or (message.entities and any(e.type == 'hashtag' for e in message.entities)):
                violation = "hashtags"
        
        elif locks.get('command') and message.text and message.text.startswith('/'):
            violation = "bot commands"
        
        # Special type locks
        elif locks.get('poll') and message.poll:
            violation = "polls"
        elif locks.get('location') and message.location:
            violation = "location sharing"
        elif locks.get('contact') and message.contact:
            violation = "contact sharing"
        elif locks.get('game') and message.game:
            violation = "games"
        elif locks.get('invoice') and message.invoice:
            violation = "invoices"
        
        # If violation found, delete message
        if violation:
            try:
                await message.delete()
                logger.info(f"Deleted {violation} from user {user_id} in chat {chat_id} (locked)")
                
                # Optionally send notification (can be configured)
                # Optionally send notification
                # await context.bot.send_message(
                #     chat_id,
                #     f"⚠️ {violation.capitalize()} are not allowed in this chat.",
                #     reply_to_message_id=None
                # )
                
                return  # Message deleted, stop processing
                
            except Exception as e:
                logger.error(f"Failed to delete locked content: {e}")
        
        return  # No violation, continue processing
        
    except Exception as e:
        logger.error(f"Error in locks enforcer: {e}", exc_info=True)
        return  # Don't block on error