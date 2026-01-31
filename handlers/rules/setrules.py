"""
Set Rules command - Set chat rules
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timezone

from core.decorators import group_only, require_admin, log_command
from utils.message_parser import extract_filter_content

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "setrules",
    "aliases": ["set_rules"],
    "description": "Set chat rules",
    "usage": "/setrules <text> - Reply to message or provide text\n\nExample:\n/setrules 1. Be respectful\n2. No spam\n3. No NSFW content",
    "category": "rules"
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /setrules command
    
    Sets the rules for the chat from either:
    - Replied message content
    - Text after command
    """
    chat_id = update.effective_chat.id
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Get rules content
    rules_text = None
    
    # Check if replying to a message
    if update.message.reply_to_message:
        content = extract_filter_content(update.message.reply_to_message)
        rules_text = content.get('text')
    # Check if text provided after command
    elif context.args:
        rules_text = " ".join(context.args)
    # Check if message has text after command
    elif update.message.text and len(update.message.text.split(maxsplit=1)) > 1:
        rules_text = update.message.text.split(maxsplit=1)[1]
    
    if not rules_text:
        await update.message.reply_html(
            "❌ <b>No rules provided.</b>\n\n"
            "<b>Usage:</b>\n"
            "• Reply to a message with /setrules\n"
            "• /setrules &lt;your rules text&gt;\n\n"
            "<b>Example:</b>\n"
            "<code>/setrules 1. Be respectful\n2. No spam</code>"
        )
        return
    
    # Update database
    await db.chats.update_one(
        {"_id": str(chat_id)},
        {
            "$set": {
                "rules": rules_text,
                "updated_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    
    # Send confirmation
    await update.message.reply_html(
        f"✅ <b>Rules have been set for this chat!</b>\n\n"
        f"Use /rules to view them."
    )
    
    logger.info(f"Rules set in chat {chat_id}")

