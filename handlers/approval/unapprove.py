"""
Unapprove command - Remove user from whitelist
"""
import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command
from utils.user_resolver import resolve_user

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "unapprove",
    "aliases": [],
    "description": "Remove user from approval whitelist",
    "usage": "/unapprove <reply/username/mention/userid>",
    "category": "approval",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /unapprove command
    
    Remove a user from the approval whitelist.
    
    Args:
        update: Telegram update
        context: PTB context
    """
    chat_id = update.effective_chat.id
    admin_user = update.effective_user
    
    # Resolve target user
    target_user = await resolve_user(update, context)
    
    if not target_user:
        await update.message.reply_html(
            "❌ <b>Please specify a user to unapprove.</b>\n\n"
            "<b>Usage:</b>\n"
            "• Reply to user's message\n"
            "• /unapprove @username\n"
            "• /unapprove user_id"
        )
        return
    
    # Update database
    db = context.application.bot_data.get('database')
    if db is None:
        await update.message.reply_html("❌ Database not available")
        return
    
    try:
        # Check if user was approved
        user_doc = await db.users.find_one({"_id": str(target_user.id)})
        
        was_approved = False
        if user_doc:
            chat_data = user_doc.get('chat_data', {}).get(str(chat_id), {})
            was_approved = chat_data.get('approved', False)
        
        if not was_approved:
            await update.message.reply_html(
                f"⚠️ {target_user.mention_html()} is not approved."
            )
            return
        
        # Remove approval status
        await db.users.update_one(
            {"_id": str(target_user.id)},
            {
                "$unset": {
                    f"chat_data.{chat_id}.approved": "",
                    f"chat_data.{chat_id}.approved_by": "",
                    f"chat_data.{chat_id}.approved_at": ""
                }
            }
        )
        
        await update.message.reply_html(
            f"✅ <b>Approval removed</b>\n\n"
            f"👤 User: {target_user.mention_html()}\n"
            f"🔒 User will now be subject to all restrictions"
        )
        
        logger.info(
            f"User {target_user.id} unapproved in chat {chat_id} "
            f"by admin {admin_user.id}"
        )
        
        # Log to database
        if db is not None:
            await db.action_logs.insert_one({
                "chat_id": str(chat_id),
                "action_type": "unapprove",
                "performed_by": str(admin_user.id),
                "target_user": str(target_user.id),
                "timestamp": datetime.now(timezone.utc)
            })
        
    except Exception as e:
        logger.error(f"Error unapproving user {target_user.id} in chat {chat_id}: {e}")
        await update.message.reply_html(
            "❌ Failed to unapprove user"
        )