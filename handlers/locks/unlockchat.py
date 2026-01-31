"""
Unlock Chat command - Remove all locks
"""
import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "unlockchat",
    "aliases": ["unlockall"],
    "description": "Unlock the chat - remove all locks",
    "usage": "/unlockchat - Remove all content restrictions",
    "category": "locks",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_delete_messages"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /unlockchat command
    
    Removes all locks from the chat.
    """
    chat_id = update.effective_chat.id
    
    db = context.application.bot_data.get('database')
    if db is None:
        await update.message.reply_html("❌ Database not available")
        return
    
    try:
        # Remove all locks by unsetting the locks field
        await db.chats.update_one(
            {"_id": str(chat_id)},
            {"$unset": {"locks": ""}},
            upsert=False
        )
        
        await update.message.reply_html(
            "🔓 <b>Chat Unlocked</b>\n\n"
            "All content restrictions have been removed.\n"
            "All users can now send any type of message."
        )
        
        # Log action
        await db.action_logs.insert_one({
            "chat_id": str(chat_id),
            "action_type": "unlockchat",
            "performed_by": str(update.effective_user.id),
            "timestamp": datetime.now(timezone.utc)
        })
        
        logger.info(f"Chat {chat_id} unlocked by user {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Error unlocking chat {chat_id}: {e}")
        await update.message.reply_html("❌ Failed to unlock chat")

