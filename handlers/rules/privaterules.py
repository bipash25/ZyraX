"""
Private Rules command - Toggle private rules mode
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timezone

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "privaterules",
    "aliases": ["private_rules"],
    "description": "Toggle sending rules in PM instead of chat",
    "usage": "/privaterules <on/off> - Toggle private rules",
    "category": "rules"
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /privaterules command
    
    Toggles whether rules are sent via PM or in chat
    """
    chat_id = update.effective_chat.id
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Check arguments
    if not context.args:
        # Show current status
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        current = chat_doc.get('private_rules', False) if chat_doc else False
        
        await update.message.reply_html(
            f"📜 <b>Private Rules:</b> {'ON' if current else 'OFF'}\n\n"
            f"<b>Usage:</b> /privaterules &lt;on/off&gt;"
        )
        return
    
    # Parse argument
    arg = context.args[0].lower()
    
    if arg in ['on', 'yes', 'true', '1', 'enable']:
        enabled = True
    elif arg in ['off', 'no', 'false', '0', 'disable']:
        enabled = False
    else:
        await update.message.reply_text(
            "❌ Invalid argument. Use: /privaterules <on/off>"
        )
        return
    
    # Update database
    await db.chats.update_one(
        {"_id": str(chat_id)},
        {
            "$set": {
                "private_rules": enabled,
                "updated_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    
    status = "enabled" if enabled else "disabled"
    message = f"✅ Private rules {status}.\n\n"
    
    if enabled:
        message += "Rules will now be sent via PM with a button."
    else:
        message += "Rules will now be displayed in the chat."
    
    await update.message.reply_text(message)
    
    logger.info(f"Private rules {status} in chat {chat_id}")

