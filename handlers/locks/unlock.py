"""
Unlock command - Remove content restrictions
"""
import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command
from .commands import LOCK_TYPES

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "unlock",
    "description": "Unlock a content type to allow it",
    "usage": "/unlock <type> - Unlock a content type\n"
             "/unlock media - Unlock all media\n"
             "/unlock all - Unlock everything",
    "category": "locks",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_delete_messages"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /unlock command
    
    Unlock a specific content type in the chat.
    """
    chat_id = update.effective_chat.id
    
    db = context.application.bot_data.get('database')
    if db is None:
        await update.message.reply_html("❌ Database not available")
        return
    
    if not context.args:
        await update.message.reply_html(
            "❌ <b>Usage:</b> <code>/unlock &lt;type&gt;</code>\n\n"
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
            # Unlock all media types
            media_types = ['photo', 'video', 'audio', 'document', 'sticker', 
                          'animation', 'voice', 'video_note']
            
            update_dict = {f"locks.{t}": False for t in media_types}
            await db.chats.update_one(
                {"_id": str(chat_id)},
                {"$set": update_dict},
                upsert=True
            )
            
            await update.message.reply_html(
                f"🔓 <b>Unlocked all media types</b>\n\n"
                f"Unlocked: {', '.join(media_types)}"
            )
        
        elif lock_type == 'all':
            # Unlock everything
            await db.chats.update_one(
                {"_id": str(chat_id)},
                {"$set": {"locks": {}}},
                upsert=True
            )
            
            await update.message.reply_html(
                f"🔓 <b>Unlocked all content types</b>\n\n"
                f"All content is now allowed."
            )
        
        else:
            # Unlock single type
            await db.chats.update_one(
                {"_id": str(chat_id)},
                {"$set": {f"locks.{lock_type}": False}},
                upsert=True
            )
            
            type_name = LOCK_TYPES.get(lock_type, lock_type)
            await update.message.reply_html(
                f"🔓 <b>Unlocked:</b> {type_name}\n\n"
                f"This content type is now allowed."
            )
        
        # Log action
        await db.action_logs.insert_one({
            "chat_id": str(chat_id),
            "action_type": "unlock",
            "lock_type": lock_type,
            "performed_by": str(update.effective_user.id),
            "timestamp": datetime.now(timezone.utc)
        })
        
        logger.info(f"Unlocked {lock_type} in chat {chat_id}")
        
    except Exception as e:
        logger.error(f"Error unlocking {lock_type} in chat {chat_id}: {e}")
        await update.message.reply_html("❌ Failed to unlock content type")