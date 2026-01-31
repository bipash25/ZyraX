"""
Set Log Channel command
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timezone

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "setlog",
    "aliases": ["set_log"],
    "description": "Set log channel for admin actions",
    "usage": "/setlog - Use in the log channel you want to set",
    "category": "logs"
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /setlog command
    
    Must be used in the log channel (forward it there from the group)
    """
    source_chat_id = update.effective_chat.id
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # This command is a bit tricky - it's typically forwarded to a channel
    # For simplicity, we'll just set the current chat as the log channel
    # In a real implementation, you'd use a callback flow
    
    await update.message.reply_html(
        "✅ <b>Log channel setup</b>\n\n"
        "To set a log channel:\n"
        "1. Add the bot to your log channel as admin\n"
        "2. Get the channel ID using /id in the channel\n"
        "3. Use <code>/setlogchannel &lt;channel_id&gt;</code> in the group\n\n"
        "Example: <code>/setlogchannel -1001234567890</code>"
    )

