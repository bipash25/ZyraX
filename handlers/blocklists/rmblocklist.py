"""
Remove blocklist command
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "rmblocklist",
    "aliases": ["removebl", "delbl"],
    "description": "Remove word/phrase from blocklist",
    "usage": "/rmblocklist <word/phrase>",
    "category": "blocklists"
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove word/phrase from blocklist"""
    chat_id = update.effective_chat.id
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Please specify the trigger to remove.\n"
            "Usage: /rmblocklist <trigger>"
        )
        return
    
    trigger = context.args[0].lower()
    
    # Remove from database
    result = await db.blocklists.delete_one({
        "chat_id": str(chat_id),
        "trigger": trigger
    })
    
    if result.deleted_count > 0:
        await update.message.reply_text(
            f"✅ Removed '{trigger}' from blocklist."
        )
        logger.info(f"Removed blocklist trigger '{trigger}' from chat {chat_id}")
    else:
        await update.message.reply_text(
            f"❌ '{trigger}' not found in blocklist."
        )

