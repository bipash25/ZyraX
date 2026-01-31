"""
Filters command - List all active filters in the chat
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "filters",
    "description": "List all active filters in the chat",
    "usage": "/filters - Show all filter triggers",
    "category": "filters",
    "scope": ["group", "supergroup"]
}


@group_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /filters command
    
    List all active filters in the current chat.
    """
    chat_id = update.effective_chat.id
    
    # Get all filters for this chat
    db = context.application.bot_data.get('database')
    if db is not None:
        filters = await db.filters.find({"chat_id": str(chat_id)}).to_list(length=None)
        
        if not filters:
            await update.message.reply_html(
                "ℹ️ <b>No filters set in this chat</b>\n\n"
                "Use <code>/filter &lt;trigger&gt;</code> to create one."
            )
            return
        
        # Build response message
        response = f"📋 <b>Active Filters ({len(filters)})</b>\n\n"
        
        # Group filters by type
        text_filters = []
        media_filters = []
        
        for f in filters:
            trigger = f['trigger']
            if f.get('file_id'):
                media_type = f.get('file_type', 'media')
                media_filters.append(f"• <code>{trigger}</code> ({media_type})")
            else:
                text_filters.append(f"• <code>{trigger}</code>")
        
        if text_filters:
            response += "<b>Text Filters:</b>\n"
            response += "\n".join(text_filters)
            response += "\n\n"
        
        if media_filters:
            response += "<b>Media Filters:</b>\n"
            response += "\n".join(media_filters)
            response += "\n\n"
        
        response += "<b>Usage:</b>\n"
        response += "• Type a trigger word to see the response\n"
        response += "• Use <code>/stop &lt;trigger&gt;</code> to remove a filter"
        
        await update.message.reply_html(response)
        
        logger.info(f"Listed {len(filters)} filters for chat {chat_id}")
    else:
        await update.message.reply_html(
            "❌ <b>Database connection error</b>"
        )