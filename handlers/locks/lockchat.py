"""
Lock Chat command - Restrict all messages from non-admins
"""
import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "lockchat",
    "aliases": ["lockall"],
    "description": "Lock the chat - only admins can send messages",
    "usage": "/lockchat - Restrict all messages from non-admins",
    "category": "locks",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_delete_messages"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /lockchat command
    
    Locks all message types - only admins can send anything.
    """
    chat_id = update.effective_chat.id
    
    db = context.application.bot_data.get('database')
    if db is None:
        await update.message.reply_html("❌ Database not available")
        return
    
    try:
        # Lock all message types except commands (so admins can still control)
        lock_types = [
            'photo', 'video', 'audio', 'document', 'sticker',
            'animation', 'voice', 'video_note', 'text', 'url',
            'forward', 'mention', 'hashtag', 'poll', 'location',
            'contact', 'game', 'invoice'
        ]
        
        update_dict = {f"locks.{t}": True for t in lock_types}
        
        await db.chats.update_one(
            {"_id": str(chat_id)},
            {"$set": update_dict},
            upsert=True
        )
        
        await update.message.reply_html(
            "🔒 <b>Chat Locked</b>\n\n"
            "All messages from non-admins will be deleted.\n"
            "Only administrators and approved users can send messages.\n\n"
            "<b>Note:</b> Commands are still allowed for all users.\n"
            "Use <code>/unlockchat</code> to unlock."
        )
        
        # Log action
        await db.action_logs.insert_one({
            "chat_id": str(chat_id),
            "action_type": "lockchat",
            "performed_by": str(update.effective_user.id),
            "timestamp": datetime.now(timezone.utc)
        })
        
        logger.info(f"Chat {chat_id} locked by user {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Error locking chat {chat_id}: {e}")
        await update.message.reply_html("❌ Failed to lock chat")

