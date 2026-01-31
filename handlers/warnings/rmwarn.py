"""
Remove Warning command - Remove last warning from a user
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timezone

from core.decorators import group_only, require_admin, log_command
from utils.user_resolver import resolve_user, mention_user

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "rmwarn",
    "aliases": ["unwarn", "removewarn"],
    "description": "Remove the last warning from a user",
    "usage": "/rmwarn <reply|@username|ID>",
    "category": "moderation",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_restrict_members"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /rmwarn command
    
    Removes the most recent warning from a user
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
            "<b>Usage:</b> /rmwarn <reply|@username|ID>"
        )
        return
    
    # Find most recent warning
    warning = await db.warnings.find_one(
        {
            "chat_id": str(chat_id),
            "user_id": str(target_user.id)
        },
        sort=[("created_at", -1)]  # Most recent first
    )
    
    if not warning:
        await update.message.reply_html(
            f"❌ {mention_user(target_user, use_html=True)} has no warnings to remove."
        )
        return
    
    # Remove warning
    await db.warnings.delete_one({"_id": warning["_id"]})
    
    # Update user document
    remaining_warnings = await db.warnings.count_documents({
        "chat_id": str(chat_id),
        "user_id": str(target_user.id)
    })
    
    await db.users.update_one(
        {"_id": str(target_user.id)},
        {
            "$set": {
                f"chat_data.{chat_id}.warnings": remaining_warnings,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    target_mention = mention_user(target_user, use_html=True)
    removed_reason = warning.get("reason", "No reason provided")
    
    await update.message.reply_html(
        f"✅ Removed 1 warning from {target_mention}\n\n"
        f"<b>Removed warning:</b> {removed_reason}\n"
        f"<b>Remaining warnings:</b> {remaining_warnings}"
    )
    
    # Log action
    await db.action_logs.insert_one({
        "chat_id": str(chat_id),
        "action_type": "rmwarn",
        "performed_by": str(admin_user.id),
        "target_user": str(target_user.id),
        "metadata": {
            "removed_reason": removed_reason,
            "remaining_warnings": remaining_warnings
        },
        "timestamp": datetime.now(timezone.utc)
    })
    
    logger.info(f"Removed warning from user {target_user.id} in chat {chat_id}")

