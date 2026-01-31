"""
Promote command - Promote a user to administrator
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, require_bot_admin, not_self, log_command
from utils.user_resolver import resolve_user, mention_user

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "promote",
    "aliases": ["admin"],
    "description": "Promote a user to administrator",
    "usage": "/promote <reply|@username|ID> [custom title]",
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
    Handle /promote command
    
    Promotes a user to administrator with standard permissions.
    Optional custom title can be specified.
    
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
            "❌ <b>Please specify a user to promote.</b>\n\n"
            "<b>Usage:</b>\n"
            "• Reply to user's message with /promote\n"
            "• /promote @username\n"
            "• /promote &lt;user_id&gt;\n"
            "• /promote &lt;reply&gt; [custom title]"
        )
        return
    
    # Check if target is bot
    if target_user.id == context.bot.id:
        await update.message.reply_text(
            "❌ I already have admin permissions!"
        )
        return
    
    # Extract custom title from arguments
    custom_title = None
    if resolve_method == "reply":
        # Title starts from first arg
        if context.args:
            custom_title = " ".join(context.args)
    else:
        # Title starts from second arg (first is user identifier)
        if len(context.args) > 1:
            custom_title = " ".join(context.args[1:])
    
    # Validate custom title length
    if custom_title and len(custom_title) > 16:
        await update.message.reply_text(
            "❌ Custom admin title is too long (maximum 16 characters)."
        )
        return
    
    # Check target's current status
    try:
        target_member = await context.bot.get_chat_member(chat_id, target_user.id)
        
        if target_member.status == "creator":
            await update.message.reply_text(
                "❌ This user is already the chat creator."
            )
            return
        
        if target_member.status == "administrator" and not custom_title:
            await update.message.reply_text(
                "ℹ️ This user is already an administrator."
            )
            return
            
    except Exception as e:
        logger.error(f"Error checking target member status: {e}")
        await update.message.reply_text(
            "❌ User is not in this chat."
        )
        return
    
    # Promote user with standard permissions
    try:
        await context.bot.promote_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            can_change_info=True,
            can_delete_messages=True,
            can_invite_users=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_promote_members=False,  # Don't grant promotion rights by default
            can_manage_chat=True,
            can_manage_video_chats=True
        )
        
        # Set custom title if provided
        if custom_title:
            try:
                await context.bot.set_chat_administrator_custom_title(
                    chat_id=chat_id,
                    user_id=target_user.id,
                    custom_title=custom_title
                )
            except Exception as title_error:
                logger.error(f"Error setting custom title: {title_error}")
                # Continue anyway, promotion succeeded
        
        # Success message
        target_mention = mention_user(target_user, use_html=True)
        admin_mention = mention_user(admin_user, use_html=True)
        
        message = f"✅ {target_mention} has been <b>promoted to administrator</b>"
        
        if custom_title:
            message += f' with title "<b>{custom_title}</b>"'
        
        message += f" by {admin_mention}."
        
        await update.message.reply_html(message)
        
        logger.info(
            f"User {target_user.id} promoted in chat {chat_id} "
            f"by admin {admin_user.id}"
            f"{f' with title {custom_title}' if custom_title else ''}"
        )
        
    except Exception as e:
        logger.error(f"Error promoting user {target_user.id} in chat {chat_id}: {e}")
        await update.message.reply_html(
            f"❌ <b>Failed to promote user.</b>\n\n"
            f"Error: {str(e)}"
        )