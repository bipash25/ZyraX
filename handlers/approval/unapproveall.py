"""
Unapproveall command - Remove all users from whitelist
"""
import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "unapproveall",
    "aliases": [],
    "description": "Remove all users from approval whitelist",
    "usage": "/unapproveall - Clear all approvals",
    "category": "approval",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /unapproveall command
    
    Remove all users from the approval whitelist in this chat.
    
    Args:
        update: Telegram update
        context: PTB context
    """
    chat_id = update.effective_chat.id
    admin_user = update.effective_user
    
    # Get database
    db = context.application.bot_data.get('database')
    if db is None:
        await update.message.reply_html("❌ Database not available")
        return
    
    try:
        # Count approved users first
        count = await db.users.count_documents({
            f"chat_data.{chat_id}.approved": True
        })
        
        if count == 0:
            await update.message.reply_html(
                "⚠️ No users are currently approved in this chat."
            )
            return
        
        # Remove all approvals for this chat
        result = await db.users.update_many(
            {f"chat_data.{chat_id}.approved": True},
            {
                "$unset": {
                    f"chat_data.{chat_id}.approved": "",
                    f"chat_data.{chat_id}.approved_by": "",
                    f"chat_data.{chat_id}.approved_at": ""
                }
            }
        )
        
        await update.message.reply_html(
            f"✅ <b>All approvals cleared</b>\n\n"
            f"🔒 Removed {result.modified_count} approved users\n"
            f"All users will now be subject to restrictions"
        )
        
        logger.info(
            f"All approvals cleared in chat {chat_id} by admin {admin_user.id} "
            f"({result.modified_count} users)"
        )
        
        # Log to database
        if db is not None:
            await db.action_logs.insert_one({
                "chat_id": str(chat_id),
                "action_type": "unapproveall",
                "performed_by": str(admin_user.id),
                "metadata": {
                    "users_affected": result.modified_count
                },
                "timestamp": datetime.now(timezone.utc)
            })
        
    except Exception as e:
        logger.error(f"Error clearing approvals in chat {chat_id}: {e}")
        await update.message.reply_html(
            "❌ Failed to clear approvals"
        )