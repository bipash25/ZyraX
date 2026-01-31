"""
Reset Warnings command - Clear all warnings from a user
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timezone

from core.decorators import group_only, require_admin, log_command
from utils.user_resolver import resolve_user, mention_user

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "resetwarn",
    "aliases": ["resetwarns", "clearwarnings"],
    "description": "Clear all warnings from a user",
    "usage": "/resetwarn <reply|@username|ID>",
    "category": "moderation",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_restrict_members"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /resetwarn command
    
    Clears all warnings from a user
    """
    chat_id = update.effective_chat.id
    admin_user = update.effective_user
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Resolve target user
    target_user, _ = await resolve_user(update, context)
    
    if not target_user:
        await update.message.reply_html(
            "❌ <b>Please specify a user.</b>\n\n"
            "<b>Usage:</b> /resetwarn <reply|@username|ID>"
        )
        return
    
    # Count warnings to be removed
    warn_count = await db.warnings.count_documents({
        "chat_id": str(chat_id),
        "user_id": str(target_user.id)
    })
    
    if warn_count == 0:
        await update.message.reply_html(
            f"❌ {mention_user(target_user, use_html=True)} has no warnings to reset."
        )
        return
    
    # Delete all warnings
    await db.warnings.delete_many({
        "chat_id": str(chat_id),
        "user_id": str(target_user.id)
    })
    
    # Update user document
    await db.users.update_one(
        {"_id": str(target_user.id)},
        {
            "$set": {
                f"chat_data.{chat_id}.warnings": 0,
                f"chat_data.{chat_id}.warn_reasons": [],
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    target_mention = mention_user(target_user, use_html=True)
    
    await update.message.reply_html(
        f"✅ Cleared <b>{warn_count}</b> warning(s) from {target_mention}"
    )
    
    # Log action
    await db.action_logs.insert_one({
        "chat_id": str(chat_id),
        "action_type": "resetwarn",
        "performed_by": str(admin_user.id),
        "target_user": str(target_user.id),
        "metadata": {
            "warnings_cleared": warn_count
        },
        "timestamp": datetime.now(timezone.utc)
    })
    
    logger.info(f"Reset {warn_count} warnings for user {target_user.id} in chat {chat_id}")

