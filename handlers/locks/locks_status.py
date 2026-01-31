"""
Locks status and locktypes commands
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, log_command
from .commands import LOCK_TYPES

logger = logging.getLogger(__name__)

# Command metadata for /locks
COMMAND_INFO = {
    "name": "locks",
    "description": "Show current lock status",
    "usage": "/locks - Show all locked content types",
    "category": "locks",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /locks command
    
    Show current lock status for the chat.
    """
    chat_id = update.effective_chat.id
    
    db = context.application.bot_data.get('database')
    if db is None:
        await update.message.reply_html("❌ Database not available")
        return
    
    try:
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        
        if not chat_doc or not chat_doc.get('locks'):
            await update.message.reply_html(
                "🔓 <b>No locks active</b>\n\n"
                "All content types are currently allowed.\n\n"
                "Use <code>/lock &lt;type&gt;</code> to restrict content."
            )
            return
        
        locks = chat_doc.get('locks', {})
        locked_types = [t for t, locked in locks.items() if locked]
        
        if not locked_types:
            await update.message.reply_html(
                "🔓 <b>No locks active</b>\n\n"
                "All content types are currently allowed."
            )
            return
        
        # Group locks by category
        media_locks = []
        message_locks = []
        special_locks = []
        permission_locks = []
        
        media_types = ['photo', 'video', 'audio', 'document', 'sticker', 'animation', 'voice', 'video_note']
        message_types = ['url', 'forward', 'mention', 'hashtag', 'command', 'text']
        special_types = ['poll', 'location', 'contact', 'game', 'invoice']
        permission_types = ['invite', 'pin', 'info']
        
        for lock_type in locked_types:
            name = LOCK_TYPES.get(lock_type, lock_type)
            if lock_type in media_types:
                media_locks.append(f"  • {name}")
            elif lock_type in message_types:
                message_locks.append(f"  • {name}")
            elif lock_type in special_types:
                special_locks.append(f"  • {name}")
            elif lock_type in permission_types:
                permission_locks.append(f"  • {name}")
        
        message = "🔒 <b>Active Locks</b>\n\n"
        
        if media_locks:
            message += "<b>📸 Media:</b>\n" + "\n".join(media_locks) + "\n\n"
        
        if message_locks:
            message += "<b>💬 Messages:</b>\n" + "\n".join(message_locks) + "\n\n"
        
        if special_locks:
            message += "<b>🎯 Special:</b>\n" + "\n".join(special_locks) + "\n\n"
        
        if permission_locks:
            message += "<b>🔧 Permissions:</b>\n" + "\n".join(permission_locks) + "\n\n"
        
        message += f"💡 <b>Total:</b> {len(locked_types)} lock(s) active\n\n"
        message += "Use <code>/unlock &lt;type&gt;</code> to remove restrictions."
        
        await update.message.reply_html(message)
        
    except Exception as e:
        logger.error(f"Error showing locks in chat {chat_id}: {e}")
        await update.message.reply_html("❌ Failed to retrieve lock status")