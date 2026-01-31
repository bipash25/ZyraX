"""
Demote command - Remove administrator privileges from a user
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, require_bot_admin, not_self, log_command
from utils.user_resolver import resolve_user, mention_user

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "demote",
    "aliases": [],
    "description": "Remove administrator privileges from a user",
    "usage": "/demote <reply|@username|ID>",
    "category": "admin",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_promote_members"])
@require_bot_admin(permissions=["can_promote_members"])
@not_self
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /demote command
    
    Removes administrator privileges from a user.
    
    Args:
        update: Telegram update
        context: PTB context
    """
    chat_id = update.effective_chat.id
    admin_user = update.effective_user
    
    # Resolve target user
    target_user, resolve_method = await resolve_user(update, context)
    
    if not target_user:
        await update.message.reply_html(
            "❌ <b>Please specify a user to demote.</b>\n\n"
            "<b>Usage:</b>\n"
            "• Reply to user's message with /demote\n"
            "• /demote @username\n"
            "• /demote &lt;user_id&gt;"
        )
        return
    
    # Check if target is bot
    if target_user.id == context.bot.id:
        await update.message.reply_text(
            "❌ I cannot demote myself!"
        )
        return
    
    # Check target's current status
    try:
        target_member = await context.bot.get_chat_member(chat_id, target_user.id)
        
        if target_member.status == "creator":
            await update.message.reply_text(
                "❌ Cannot demote the chat creator."
            )
            return
        
        if target_member.status not in ["administrator", "creator"]:
            await update.message.reply_text(
                "ℹ️ This user is not an administrator."
            )
            return
            
    except Exception as e:
        logger.error(f"Error checking target member status: {e}")
        await update.message.reply_text(
            "❌ User is not in this chat."
        )
        return
    
    # Demote user (remove all admin rights)
    try:
        await context.bot.promote_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            can_change_info=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
            can_manage_chat=False,
            can_manage_video_chats=False
        )
        
        # Success message
        target_mention = mention_user(target_user, use_html=True)
        admin_mention = mention_user(admin_user, use_html=True)
        
        message = (
            f"✅ {target_mention} has been <b>demoted</b> "
            f"and no longer has administrator privileges.\n\n"
            f"Demoted by {admin_mention}."
        )
        
        await update.message.reply_html(message)
        
        logger.info(
            f"User {target_user.id} demoted in chat {chat_id} "
            f"by admin {admin_user.id}"
        )
        
    except Exception as e:
        logger.error(f"Error demoting user {target_user.id} in chat {chat_id}: {e}")
        await update.message.reply_html(
            f"❌ <b>Failed to demote user.</b>\n\n"
            f"Error: {str(e)}"
        )