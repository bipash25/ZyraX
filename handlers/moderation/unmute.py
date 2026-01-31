"""
Unmute command - Restore user's messaging permissions
"""
import logging
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, require_bot_admin, log_command
from utils.user_resolver import resolve_user, mention_user
from utils.time_parser import now_utc

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "unmute",
    "aliases": [],
    "description": "Unmute a user in the chat",
    "usage": "/unmute <reply|@username|ID>",
    "category": "moderation",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_restrict_members"])
@require_bot_admin(permissions=["can_restrict_members"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /unmute command
    
    Args:
        update: Telegram update
        context: PTB context
    """
    chat_id = update.effective_chat.id
    admin_user = update.effective_user
    message = update.effective_message
    
    # Resolve target user
    target_user, resolve_method = await resolve_user(update, context)
    
    if not target_user:
        await message.reply_html(
            "❌ <b>Please specify a user to unmute.</b>\n\n"
            "<b>Usage:</b>\n"
            "• /unmute @username\n"
            "• /unmute &lt;user_id&gt;"
        )
        return
    
    # Unmute the user (restore all permissions)
    try:
        # Full permissions for regular members
        # Note: PTB v20+ uses different permission structure
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=False,  # Usually only admins
            can_invite_users=True,
            can_pin_messages=False  # Usually only admins
        )
        
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            permissions=permissions
        )
        
        # Send confirmation
        target_mention = mention_user(target_user, use_html=True)
        admin_mention = mention_user(admin_user, use_html=True)
        
        await message.reply_html(
            f"✅ {target_mention} has been <b>unmuted</b> by {admin_mention}."
        )
        
        # Log to database
        try:
            db = context.application.bot_data.get('database')
            if db is not None:
                await db.action_logs.insert_one({
                    "chat_id": str(chat_id),
                    "action_type": "unmute",
                    "performed_by": str(admin_user.id),
                    "target_user": str(target_user.id),
                    "timestamp": now_utc()
                })
        except Exception as e:
            logger.error(f"Error logging unmute action: {e}")
        
        logger.info(f"User {target_user.id} unmuted in chat {chat_id} by admin {admin_user.id}")
        
    except Exception as e:
        logger.error(f"Error unmuting user {target_user.id} in chat {chat_id}: {e}")
        await message.reply_html(
            f"❌ <b>Failed to unmute user.</b>\n\n"
            f"Error: {str(e)}"
        )