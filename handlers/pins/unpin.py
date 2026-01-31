"""
Unpin command - Unpin the current pinned message
"""
import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "unpin",
    "description": "Unpin the current pinned message",
    "usage": "/unpin - Unpin the currently pinned message\n"
             "/unpin - Reply to a pinned message to unpin it specifically",
    "category": "pins",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_pin_messages"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /unpin command
    
    Unpin a message in the chat.
    """
    chat_id = update.effective_chat.id
    
    try:
        # Check if this is a reply to a specific pinned message
        if update.message.reply_to_message:
            message_id = update.message.reply_to_message.message_id
            
            # Unpin specific message
            await context.bot.unpin_chat_message(
                chat_id=chat_id,
                message_id=message_id
            )
            
            await update.message.reply_html(
                "📌 <b>Message unpinned</b>"
            )
        else:
            # Unpin the most recent pinned message
            await context.bot.unpin_chat_message(chat_id=chat_id)
            
            await update.message.reply_html(
                "📌 <b>Most recent pinned message unpinned</b>"
            )
        
        # Log action
        db = context.application.bot_data.get('database')
        if db is not None:
            await db.action_logs.insert_one({
                "chat_id": str(chat_id),
                "action_type": "unpin",
                "message_id": update.message.reply_to_message.message_id if update.message.reply_to_message else None,
                "performed_by": str(update.effective_user.id),
                "timestamp": datetime.now(timezone.utc)
            })
        
        logger.info(f"Unpinned message in chat {chat_id}")
        
    except TelegramError as e:
        logger.error(f"Failed to unpin message in chat {chat_id}: {e}")
        
        # Check if there are no pinned messages
        if "no pinned message" in str(e).lower() or "message to unpin not found" in str(e).lower():
            await update.message.reply_html(
                "❌ <b>No pinned messages found</b>"
            )
        else:
            await update.message.reply_html(
                f"❌ <b>Failed to unpin message</b>\n\n"
                f"Error: {str(e)}"
            )