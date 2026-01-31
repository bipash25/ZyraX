"""
Warns command - Show user's warnings
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, log_command
from utils.user_resolver import resolve_user, mention_user

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "warns",
    "aliases": ["warnings"],
    "description": "Show warnings for a user",
    "usage": "/warns [reply|@username|ID]",
    "category": "moderation",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /warns command
    
    Shows warning count and reasons for a user
    """
    chat_id = update.effective_chat.id
    user = update.effective_user
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Resolve target user (default to self if not specified)
    target_user, _ = await resolve_user(update, context, allow_self=True)
    
    if not target_user:
        target_user = user
    
    # Get warnings for user
    warnings_cursor = db.warnings.find({
        "chat_id": str(chat_id),
        "user_id": str(target_user.id)
    })
    
    warnings = await warnings_cursor.to_list(length=None)
    warn_count = len(warnings)
    
    # Get chat settings
    chat_doc = await db.chats.find_one({"_id": str(chat_id)})
    warn_limit = 3
    warn_mode = "ban"
    
    if chat_doc:
        warn_limit = chat_doc.get("warn_limit", 3)
        warn_mode = chat_doc.get("warn_mode", "ban")
    
    target_mention = mention_user(target_user, use_html=True)
    
    if warn_count == 0:
        await update.message.reply_html(
            f"✅ {target_mention} has <b>no warnings</b>."
        )
        return
    
    # Build warning list
    message = f"⚠️ <b>Warnings for {target_mention}</b>\n"
    message += f"<b>Total:</b> {warn_count}/{warn_limit}\n"
    message += f"<b>Action on limit:</b> {warn_mode}\n\n"
    
    for i, warning in enumerate(warnings, 1):
        reason = warning.get("reason", "No reason provided")
        created_at = warning.get("created_at")
        
        message += f"{i}. {reason}"
        if created_at:
            message += f" (<i>{created_at.strftime('%Y-%m-%d')}</i>)"
        message += "\n"
    
    await update.message.reply_html(message)

