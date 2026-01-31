"""
Stop command - Remove a filter
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "stop",
    "description": "Remove a filter trigger",
    "usage": "/stop <trigger> - Delete the specified filter",
    "category": "filters",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /stop command
    
    Remove a filter from the chat.
    """
    chat_id = update.effective_chat.id
    
    # Check if trigger word provided
    if not context.args:
        await update.message.reply_html(
            "❌ <b>Please specify which filter to remove</b>\n\n"
            "<b>Usage:</b> <code>/stop &lt;trigger&gt;</code>\n\n"
            "Use <code>/filters</code> to see all active filters."
        )
        return
    
    # Get trigger word (lowercase for case-insensitive matching)
    trigger = ' '.join(context.args).lower().strip()
    
    # Remove filter from database
    db = context.application.bot_data.get('database')
    if db is not None:
        result = await db.filters.delete_one({
            "chat_id": str(chat_id),
            "trigger": trigger
        })
        
        if result.deleted_count > 0:
            await update.message.reply_html(
                f"✅ <b>Filter removed</b>\n\n"
                f"Trigger '<code>{trigger}</code>' has been deleted."
            )
            
            logger.info(
                f"Filter removed: '{trigger}' from chat {chat_id} by user {update.effective_user.id}"
            )
        else:
            await update.message.reply_html(
                f"❌ <b>Filter not found</b>\n\n"
                f"No filter with trigger '<code>{trigger}</code>' exists.\n\n"
                f"Use <code>/filters</code> to see all active filters."
            )
    else:
        await update.message.reply_html(
            "❌ <b>Database connection error</b>"
        )