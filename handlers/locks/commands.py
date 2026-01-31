"""
Lock/Unlock commands - Restrict content types in groups
"""
import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

# Available lock types
LOCK_TYPES = {
    # Media types
    'photo': 'Photos/Images',
    'video': 'Videos',
    'audio': 'Audio files',
    'document': 'Documents/Files',
    'sticker': 'Stickers',
    'animation': 'GIFs/Animations',
    'voice': 'Voice messages',
    'video_note': 'Video notes/circles',
    
    # Message types
    'url': 'URLs/Links',
    'forward': 'Forwarded messages',
    'mention': 'Mentions (@username)',
    'hashtag': 'Hashtags (#tag)',
    'command': 'Bot commands',
    'text': 'Text messages',
    
    # Special types
    'poll': 'Polls',
    'location': 'Location sharing',
    'contact': 'Contact sharing',
    'game': 'Games',
    'invoice': 'Payment invoices',
    
    # Permissions
    'invite': 'Adding members',
    'pin': 'Pinning messages',
    'info': 'Changing chat info',
    
    # Combinations
    'media': 'All media types',
    'all': 'All message types'
}

# Command metadata
COMMAND_INFO = {
    "name": "lock",
    "description": "Lock a content type to restrict it",
    "usage": "/lock <type> - Lock a content type\n"
             "/lock media - Lock all media\n"
             "/lock all - Lock everything",
    "category": "locks",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_delete_messages"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /lock command
    
    Lock a specific content type in the chat.
    """
    chat_id = update.effective_chat.id
    
    db = context.application.bot_data.get('database')
    if db is None:
        await update.message.reply_html("❌ Database not available")
        return
    
    if not context.args:
        await update.message.reply_html(
            "❌ <b>Usage:</b> <code>/lock &lt;type&gt;</code>\n\n"
            "Use <code>/locktypes</code> to see all available types."
        )
        return
    
    lock_type = context.args[0].lower()
    
    # Validate lock type
    if lock_type not in LOCK_TYPES and lock_type not in ['media', 'all']:
        await update.message.reply_html(
            f"❌ <b>Invalid lock type:</b> <code>{lock_type}</code>\n\n"
            f"Use <code>/locktypes</code> to see available types."
        )
        return
    
    try:
        # Handle special cases
        if lock_type == 'media':
            # Lock all media types
            media_types = ['photo', 'video', 'audio', 'document', 'sticker', 
                          'animation', 'voice', 'video_note']
            
            update_dict = {f"locks.{t}": True for t in media_types}
            await db.chats.update_one(
                {"_id": str(chat_id)},
                {"$set": update_dict},
                upsert=True
            )
            
            await update.message.reply_html(
                f"🔒 <b>Locked all media types</b>\n\n"
                f"Locked: {', '.join(media_types)}"
            )
        
        elif lock_type == 'all':
            # Lock everything
            update_dict = {f"locks.{t}": True for t in LOCK_TYPES.keys() if t not in ['media', 'all']}
            await db.chats.update_one(
                {"_id": str(chat_id)},
                {"$set": update_dict},
                upsert=True
            )
            
            await update.message.reply_html(
                f"🔒 <b>Locked all content types</b>\n\n"
                f"All messages except from admins will be restricted."
            )
        
        else:
            # Lock single type
            await db.chats.update_one(
                {"_id": str(chat_id)},
                {"$set": {f"locks.{lock_type}": True}},
                upsert=True
            )
            
            type_name = LOCK_TYPES.get(lock_type, lock_type)
            await update.message.reply_html(
                f"🔒 <b>Locked:</b> {type_name}\n\n"
                f"This content type is now restricted for non-admins."
            )
        
        # Log action
        await db.action_logs.insert_one({
            "chat_id": str(chat_id),
            "action_type": "lock",
            "lock_type": lock_type,
            "performed_by": str(update.effective_user.id),
            "timestamp": datetime.now(timezone.utc)
        })
        
        logger.info(f"Locked {lock_type} in chat {chat_id}")
        
    except Exception as e:
        logger.error(f"Error locking {lock_type} in chat {chat_id}: {e}")
        await update.message.reply_html("❌ Failed to lock content type")