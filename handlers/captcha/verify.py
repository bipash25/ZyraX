"""
Manually verify a user (bypass captcha)
Command: /verify <user>
"""

from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import require_admin, group_only, log_command
from utils.user_resolver import resolve_user
from utils.time_parser import now_utc
import logging

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "verify",
    "aliases": ["manualverify", "skipcaptcha"],
    "description": "Manually verify a user (skip captcha)",
    "usage": "/verify <reply/username/mention/userid>",
    "category": "captcha",
    "permissions": ["can_restrict_members"],
    "admin_only": True,
    "group_only": True
}

@require_admin(permissions=["can_restrict_members"])
@group_only
@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually verify a user"""
    chat_id = str(update.effective_chat.id)
    message = update.message
    
    # Resolve target user
    target_user = await resolve_user(update, context)
    
    if not target_user:
        await message.reply_text(
            "❌ Please specify a user to verify.\n\n"
            "<b>Usage:</b>\n"
            "• Reply to the user's message with <code>/verify</code>\n"
            "• <code>/verify @username</code>\n"
            "• <code>/verify userid</code>",
            parse_mode="HTML"
        )
        return
    
    user_id = str(target_user.id)
    
    try:
        # Get database
        db = context.application.bot_data.get('database')
        if not db:
            await message.reply_text("❌ Database not available")
            return
        
        # Check if captcha is enabled
        chat_settings = await db.chats.find_one({"_id": chat_id})
        
        if not chat_settings or not chat_settings.get("captcha_enabled", False):
            await message.reply_text(
                "ℹ️ Captcha is not enabled in this chat.\n"
                "Use /captcha on to enable it."
            )
            return
        
        # Check if user is in pending verification
        pending = await db.captcha_pending.find_one({
            "chat_id": chat_id,
            "user_id": user_id
        })
        
        if not pending:
            await message.reply_text(
                f"ℹ️ {target_user.mention_html()} is not awaiting verification.",
                parse_mode="HTML"
            )
            return
        
        # Remove from pending
        await db.captcha_pending.delete_one({
            "chat_id": chat_id,
            "user_id": user_id
        })
        
        # Unmute the user
        try:
            await context.bot.restrict_chat_member(
                chat_id=int(chat_id),
                user_id=target_user.id,
                permissions={
                    'can_send_messages': True,
                    'can_send_media_messages': True,
                    'can_send_polls': True,
                    'can_send_other_messages': True,
                    'can_add_web_page_previews': True,
                    'can_change_info': False,
                    'can_invite_users': True,
                    'can_pin_messages': False
                }
            )
        except Exception as e:
            logger.error(f"Error unmuting user during manual verification: {e}")
        
        # Delete captcha message if exists
        if pending.get("message_id"):
            try:
                await context.bot.delete_message(
                    chat_id=int(chat_id),
                    message_id=pending["message_id"]
                )
            except Exception:
                pass  # Message might be already deleted
        
        # Send welcome message if enabled and not sent yet
        if chat_settings.get("welcome_enabled", False):
            from middleware.greetings_handler import handle_new_member
            # Note: Welcome will be sent through normal flow, no need to manually trigger
        
        # Log the action
        await db.action_logs.insert_one({
            "chat_id": chat_id,
            "action_type": "manual_verify",
            "performed_by": str(message.from_user.id),
            "target_user": user_id,
            "timestamp": now_utc()
        })
        
        # Success message
        await message.reply_text(
            f"✅ {target_user.mention_html()} has been manually verified!\n\n"
            f"The user can now send messages in the chat.",
            parse_mode="HTML"
        )
        
        # Notify the user
        try:
            await context.bot.send_message(
                chat_id=target_user.id,
                text=f"✅ You have been manually verified in {update.effective_chat.title}!"
            )
        except Exception:
            pass  # User might have blocked the bot
        
    except Exception as e:
        logger.error(f"Error in manual verify command: {e}")
        await message.reply_text(
            f"❌ Error verifying user: {str(e)}"
        )