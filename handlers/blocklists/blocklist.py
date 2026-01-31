"""
List blocklists command
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "blocklist",
    "aliases": ["blocklists", "bl"],
    "description": "List all blocked words/phrases",
    "usage": "/blocklist - Show all blocklist triggers",
    "category": "blocklists"
}


@log_command
@group_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all blocklist triggers"""
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Get all blocklists
    cursor = db.blocklists.find({"chat_id": str(chat_id)})
    blocklists = await cursor.to_list(length=None)
    
    if not blocklists:
        await update.message.reply_html(
            "ℹ️ No blocklist triggers set in this chat.\n\n"
            "Admins can add triggers with /addblocklist"
        )
        return
    
    # Build message
    message = f"📛 <b>Blocklist for {chat_title}:</b>\n\n"
    
    for i, bl in enumerate(blocklists, 1):
        trigger = bl.get('trigger', '')
        reason = bl.get('reason')
        message += f"{i}. <code>{trigger}</code>"
        if reason:
            message += f" - {reason}"
        message += "\n"
    
    message += f"\n<b>Total:</b> {len(blocklists)} trigger(s)"
    
    await update.message.reply_html(message)

