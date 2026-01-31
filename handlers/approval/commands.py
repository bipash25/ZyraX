"""
Approval commands - Whitelist users to bypass restrictions
Supports: /approve, /unapprove, /approved, /unapproveall
"""
import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command
from utils.user_resolver import resolve_user

logger = logging.getLogger(__name__)

# Command metadata for /approve
COMMAND_INFO = {
    "name": "approve",
    "aliases": [],
    "description": "Approve a user to bypass restrictions",
    "usage": "/approve <reply/username/mention/userid> - Whitelist user",
    "category": "approval",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /approve command
    
    Approve a user to bypass antiflood, locks, and other restrictions.
    Admins are automatically approved.
    
    Args:
        update: Telegram update
        context: PTB context
    """
    chat_id = update.effective_chat.id
    admin_user = update.effective_user
    
    # Resolve target user
    result = await resolve_user(update, context)
    
    # resolve_user returns a tuple (user, arg_offset)
    if isinstance(result, tuple):
        target_user, _ = result
    else:
        target_user = result
    
    if not target_user:
        await update.message.reply_html(
            "❌ <b>Please specify a user to approve.</b>\n\n"
            "<b>Usage:</b>\n"
            "• Reply to user's message\n"
            "• /approve @username\n"
            "• /approve user_id"
        )
        return
    
    # Check if target is admin
    try:
        member = await update.effective_chat.get_member(target_user.id)
        if member.status in ['administrator', 'creator']:
            await update.message.reply_html(
                "⚠️ Admins are automatically approved and don't need explicit approval."
            )
            return
    except Exception as e:
        logger.error(f"Error checking member status: {e}")
    
    # Update database
    db = context.application.bot_data.get('database')
    if db is None:
        await update.message.reply_html("❌ Database not available")
        return
    
    try:
        # Update user's approval status for this chat
        await db.users.update_one(
            {"_id": str(target_user.id)},
            {
                "$set": {
                    f"chat_data.{chat_id}.approved": True,
                    f"chat_data.{chat_id}.approved_by": str(admin_user.id),
                    f"chat_data.{chat_id}.approved_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        
        await update.message.reply_html(
            f"✅ <b>User approved</b>\n\n"
            f"👤 User: {target_user.mention_html()}\n"
            f"🔓 This user can now bypass antiflood and locks"
        )
        
        logger.info(
            f"User {target_user.id} approved in chat {chat_id} "
            f"by admin {admin_user.id}"
        )
        
        # Log to database
        if db is not None:
            await db.action_logs.insert_one({
                "chat_id": str(chat_id),
                "action_type": "approve",
                "performed_by": str(admin_user.id),
                "target_user": str(target_user.id),
                "timestamp": datetime.now(timezone.utc)
            })
        
    except Exception as e:
        logger.error(f"Error approving user {target_user.id} in chat {chat_id}: {e}")
        await update.message.reply_html(
            "❌ Failed to approve user"
        )