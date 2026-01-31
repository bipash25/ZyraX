"""
Adminlist command - Show list of chat administrators
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, log_command
from utils.user_resolver import mention_user

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "adminlist",
    "aliases": ["admins", "staff"],
    "description": "Show list of chat administrators",
    "usage": "/adminlist",
    "category": "admin",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /adminlist command
    
    Shows all administrators in the chat with their titles and permissions.
    
    Args:
        update: Telegram update
        context: PTB context
    """
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    
    try:
        # Get all administrators
        admins = await context.bot.get_chat_administrators(chat_id)
        
        if not admins:
            await update.message.reply_text("No administrators found.")
            return
        
        # Separate creator and admins
        creator = None
        admin_list = []
        bot_admins = []
        
        for admin in admins:
            if admin.status == "creator":
                creator = admin
            elif admin.user.is_bot:
                bot_admins.append(admin)
            else:
                admin_list.append(admin)
        
        # Build message
        message = f"<b>👥 Administrators of {chat.title}</b>\n\n"
        
        # Creator
        if creator:
            creator_mention = mention_user(creator.user, use_html=True)
            title = f" ({creator.custom_title})" if creator.custom_title else ""
            message += f"<b>👑 Creator</b>\n• {creator_mention}{title}\n\n"
        
        # Human admins
        if admin_list:
            message += f"<b>⭐ Administrators ({len(admin_list)})</b>\n"
            for admin in admin_list:
                admin_mention = mention_user(admin.user, use_html=True)
                title = f" ({admin.custom_title})" if admin.custom_title else ""
                
                # Add key permissions
                perms = []
                if admin.can_promote_members:
                    perms.append("promote")
                if admin.can_restrict_members:
                    perms.append("restrict")
                if admin.can_delete_messages:
                    perms.append("delete")
                
                perm_text = f" [{', '.join(perms)}]" if perms else ""
                message += f"• {admin_mention}{title}{perm_text}\n"
            message += "\n"
        
        # Bot admins
        if bot_admins:
            message += f"<b>🤖 Bot Administrators ({len(bot_admins)})</b>\n"
            for bot_admin in bot_admins:
                bot_mention = mention_user(bot_admin.user, use_html=True)
                message += f"• {bot_mention}\n"
        
        # Total count
        total = len(admins)
        message += f"\n<b>Total:</b> {total} administrator{'s' if total != 1 else ''}"
        
        await update.message.reply_html(message)
        
        logger.info(f"Admin list requested in chat {chat_id}, found {total} admins")
        
    except Exception as e:
        logger.error(f"Error getting admin list for chat {chat_id}: {e}")
        await update.message.reply_text(
            "❌ Failed to retrieve administrator list. "
            "Make sure I have permission to access chat members."
        )