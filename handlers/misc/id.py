"""
ID command - Show user and chat IDs
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import log_command
from utils.user_resolver import resolve_user, mention_user, format_user_info

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "id",
    "aliases": ["info"],
    "description": "Get user and chat ID information",
    "usage": "/id [reply|@username|ID]",
    "category": "misc",
    "scope": ["private", "group", "supergroup"]
}


@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /id command
    
    Shows user ID, chat ID, and other information.
    If used as reply or with user argument, shows that user's info.
    
    Args:
        update: Telegram update
        context: PTB context
    """
    chat = update.effective_chat
    user = update.effective_user
    
    # Try to resolve target user (defaults to self if no args)
    target_user, resolve_method = await resolve_user(update, context, allow_self=True)
    
    # If user resolution failed and args were provided, show error
    if not target_user and context.args:
        await update.message.reply_html(
            f"❌ <b>Could not find user:</b> <code>{context.args[0]}</code>\n\n"
            "Make sure the user is a member of this chat."
        )
        return
    
    # If still no target user, use command sender
    if not target_user:
        target_user = user
    
    # Build information message
    message = "<b>📊 Information</b>\n\n"
    
    # User information
    message += format_user_info(target_user)
    
    # Chat information
    if chat.type != "private":
        message += f"\n\n<b>💬 Chat Information</b>\n"
        message += f"📝 Title: {chat.title}\n"
        message += f"🆔 Chat ID: <code>{chat.id}</code>\n"
        message += f"📂 Type: {chat.type.title()}"
        
        if chat.username:
            message += f"\n🔗 Username: @{chat.username}"
        
        # Get member count if possible
        try:
            member_count = await context.bot.get_chat_member_count(chat.id)
            message += f"\n👥 Members: {member_count:,}"
        except Exception:
            pass
    
    # Show if user is different from command sender
    if target_user and target_user.id != user.id:
        sender_mention = mention_user(user, use_html=True)
        message += f"\n\n<i>Requested by {sender_mention}</i>"
    
    await update.message.reply_html(message)
    
    logger.debug(
        f"ID command used by {user.id} in chat {chat.id}, "
        f"target user {target_user.id if target_user else 'self'}"
    )