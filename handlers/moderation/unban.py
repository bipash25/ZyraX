"""
Unban command - Unban users from the chat
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, require_bot_admin, log_command
from utils.user_resolver import resolve_user, mention_user
from utils.time_parser import now_utc

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "unban",
    "aliases": ["pardon"],
    "description": "Unban a user from the chat",
    "usage": "/unban <reply|@username|ID>",
    "category": "moderation",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_restrict_members"])
@require_bot_admin(permissions=["can_restrict_members"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /unban command
    
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
            "❌ <b>Please specify a user to unban.</b>\n\n"
            "<b>Usage:</b>\n"
            "• /unban @username\n"
            "• /unban &lt;user_id&gt;"
        )
        return
    
    # Unban the user
    try:
        await context.bot.unban_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            only_if_banned=True
        )
        
        # Send confirmation
        target_mention = mention_user(target_user, use_html=True)
        admin_mention = mention_user(admin_user, use_html=True)
        
        await message.reply_html(
            f"✅ {target_mention} has been <b>unbanned</b> by {admin_mention}."
        )
        
        # Log to database
        try:
            db = context.application.bot_data.get('database')
            if db is not None:
                await db.action_logs.insert_one({
                    "chat_id": str(chat_id),
                    "action_type": "unban",
                    "performed_by": str(admin_user.id),
                    "target_user": str(target_user.id),
                    "timestamp": now_utc()
                })
        except Exception as e:
            logger.error(f"Error logging unban action: {e}")
        
        logger.info(f"User {target_user.id} unbanned in chat {chat_id} by admin {admin_user.id}")
        
    except Exception as e:
        logger.error(f"Error unbanning user {target_user.id} in chat {chat_id}: {e}")
        await message.reply_html(
            f"❌ <b>Failed to unban user.</b>\n\n"
            f"Error: {str(e)}"
        )