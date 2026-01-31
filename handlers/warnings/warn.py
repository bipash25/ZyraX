"""
Warn command - Issue a warning to a user
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timezone

from core.decorators import group_only, require_admin, require_bot_admin, not_self, log_command
from utils.user_resolver import resolve_user, mention_user

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "warn",
    "aliases": ["swarn"],
    "description": "Warn a user",
    "usage": "/warn <reply|@username|ID> [reason]",
    "category": "moderation",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_restrict_members"])
@require_bot_admin(permissions=["can_restrict_members"])
@not_self
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /warn command
    
    Issues a warning to a user and tracks warning count.
    Takes action when warning limit is reached.
    """
    chat_id = update.effective_chat.id
    admin_user = update.effective_user
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Resolve target user
    target_user, resolve_method = await resolve_user(update, context)
    
    if not target_user:
        await update.message.reply_html(
            "❌ <b>Please specify a user to warn.</b>\n\n"
            "<b>Usage:</b>\n"
            "• Reply to user's message with /warn [reason]\n"
            "• /warn @username [reason]\n"
            "• /warn &lt;user_id&gt; [reason]"
        )
        return
    
    # Check if target is bot
    if target_user.id == context.bot.id:
        await update.message.reply_text("❌ I cannot warn myself!")
        return
    
    # Check if target is admin
    try:
        target_member = await context.bot.get_chat_member(chat_id, target_user.id)
        if target_member.status in ["administrator", "creator"]:
            await update.message.reply_text("❌ Cannot warn an administrator.")
            return
    except Exception as e:
        logger.error(f"Error checking target member status: {e}")
    
    # Extract warning reason
    reason = None
    if resolve_method == "reply":
        if context.args:
            reason = " ".join(context.args)
    else:
        if len(context.args) > 1:
            reason = " ".join(context.args[1:])
    
    # Get chat settings
    chat_doc = await db.chats.find_one({"_id": str(chat_id)})
    warn_limit = 3
    warn_mode = "ban"
    warn_time = 0
    
    if chat_doc:
        warn_limit = chat_doc.get("warn_limit", 3)
        warn_mode = chat_doc.get("warn_mode", "ban")
        warn_time = chat_doc.get("warn_time", 0)
    
    # Get current warnings for user
    warnings = await db.warnings.count_documents({
        "chat_id": str(chat_id),
        "user_id": str(target_user.id)
    })
    
    new_warning_count = warnings + 1
    
    # Add warning to database
    await db.warnings.insert_one({
        "chat_id": str(chat_id),
        "user_id": str(target_user.id),
        "reason": reason,
        "warned_by": str(admin_user.id),
        "created_at": datetime.now(timezone.utc)
    })
    
    # Update user document
    await db.users.update_one(
        {"_id": str(target_user.id)},
        {
            "$set": {
                f"chat_data.{chat_id}.warnings": new_warning_count,
                f"chat_data.{chat_id}.last_warn": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            "$push": {
                f"chat_data.{chat_id}.warn_reasons": reason or "No reason provided"
            }
        },
        upsert=True
    )
    
    target_mention = mention_user(target_user, use_html=True)
    
    # Check if warning limit reached
    if new_warning_count >= warn_limit:
        # Take action based on warn_mode
        try:
            if warn_mode == "ban":
                await context.bot.ban_chat_member(chat_id, target_user.id)
                action_text = "banned"
            elif warn_mode == "kick":
                await context.bot.ban_chat_member(chat_id, target_user.id)
                await context.bot.unban_chat_member(chat_id, target_user.id)
                action_text = "kicked"
            elif warn_mode == "mute":
                from telegram import ChatPermissions
                await context.bot.restrict_chat_member(
                    chat_id, target_user.id,
                    permissions=ChatPermissions(can_send_messages=False)
                )
                action_text = "muted"
            else:
                action_text = "no action taken (invalid mode)"
            
            # Clear warnings after action
            await db.warnings.delete_many({
                "chat_id": str(chat_id),
                "user_id": str(target_user.id)
            })
            
            await db.users.update_one(
                {"_id": str(target_user.id)},
                {
                    "$set": {
                        f"chat_data.{chat_id}.warnings": 0,
                        f"chat_data.{chat_id}.warn_reasons": []
                    }
                }
            )
            
            message = (
                f"⚠️ {target_mention} has been <b>{action_text}</b>!\n\n"
                f"<b>Reason:</b> {reason or 'No reason provided'}\n"
                f"<b>Warnings:</b> {new_warning_count}/{warn_limit} (limit reached)"
            )
            
        except Exception as e:
            logger.error(f"Error taking warn action: {e}")
            message = (
                f"⚠️ {target_mention} reached warning limit ({new_warning_count}/{warn_limit})\n"
                f"but I couldn't take action: {str(e)}"
            )
    else:
        # Just show warning
        message = (
            f"⚠️ {target_mention} has been <b>warned</b>!\n\n"
            f"<b>Warnings:</b> {new_warning_count}/{warn_limit}"
        )
        
        if reason:
            message += f"\n<b>Reason:</b> {reason}"
    
    await update.message.reply_html(message)
    
    # Log action
    await db.action_logs.insert_one({
        "chat_id": str(chat_id),
        "action_type": "warn",
        "performed_by": str(admin_user.id),
        "target_user": str(target_user.id),
        "reason": reason,
        "metadata": {
            "warning_count": new_warning_count,
            "warning_limit": warn_limit
        },
        "timestamp": datetime.now(timezone.utc)
    })
    
    logger.info(f"User {target_user.id} warned in chat {chat_id} by {admin_user.id} ({new_warning_count}/{warn_limit})")

