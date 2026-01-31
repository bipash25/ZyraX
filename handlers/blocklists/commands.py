"""
Blocklist management commands
"""
import logging
import re
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timezone

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

# Add blocklist command
COMMAND_INFO = {
    "name": "addblocklist",
    "aliases": ["addbl"],
    "description": "Add word/phrase to blocklist",
    "usage": "/addblocklist <word/phrase> [reason]\n\nSupports wildcards:\n• ? = any single character\n• * = any characters",
    "category": "blocklists"
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add word/phrase to blocklist"""
    chat_id = update.effective_chat.id
    admin_user = update.effective_user
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    if not context.args:
        await update.message.reply_html(
            "❌ <b>Please specify a word or phrase to block.</b>\n\n"
            "<b>Usage:</b> /addblocklist &lt;trigger&gt; [reason]\n\n"
            "<b>Examples:</b>\n"
            "• <code>/addblocklist spam</code>\n"
            "• <code>/addblocklist badword Don't use this word</code>\n"
            "• <code>/addblocklist *casino* Contains casino</code>\n\n"
            "<b>Wildcards:</b>\n"
            "• <code>?</code> = any single character\n"
            "• <code>*</code> = any characters"
        )
        return
    
    # Extract trigger and reason
    trigger = context.args[0].lower()
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else None
    
    # Check if already exists
    existing = await db.blocklists.find_one({
        "chat_id": str(chat_id),
        "trigger": trigger
    })
    
    if existing:
        await update.message.reply_text(
            f"❌ '{trigger}' is already in the blocklist."
        )
        return
    
    # Add to database
    await db.blocklists.insert_one({
        "chat_id": str(chat_id),
        "trigger": trigger,
        "reason": reason,
        "action": "warn",  # Default action
        "delete_message": True,
        "created_by": str(admin_user.id),
        "created_at": datetime.now(timezone.utc)
    })
    
    await update.message.reply_html(
        f"✅ Added <code>{trigger}</code> to blocklist.\n\n"
        f"<b>Action:</b> Warn user\n"
        f"<b>Delete message:</b> Yes" +
        (f"\n<b>Reason:</b> {reason}" if reason else "")
    )
    
    logger.info(f"Added blocklist trigger '{trigger}' in chat {chat_id}")

