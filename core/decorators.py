"""
Decorators for permission checking and validation
Used to enforce access control on commands
"""
import logging
from functools import wraps
from typing import List, Callable, Optional
from telegram import Update
from telegram.ext import ContextTypes
from config import settings

logger = logging.getLogger(__name__)


def group_only(func: Callable):
    """
    Decorator to restrict command to groups only
    
    Usage:
        @group_only
        async def my_command(update, context):
            pass
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type == "private":
            await update.message.reply_text(
                "❌ This command only works in groups and supergroups."
            )
            return
        return await func(update, context)
    return wrapper


def private_only(func: Callable):
    """
    Decorator to restrict command to private chats only
    
    Usage:
        @private_only
        async def my_command(update, context):
            pass
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type != "private":
            await update.message.reply_text(
                "❌ This command only works in private chats."
            )
            return
        return await func(update, context)
    return wrapper


def owner_only(func: Callable):
    """
    Decorator to restrict command to bot owner only
    
    Usage:
        @owner_only
        async def my_command(update, context):
            pass
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if user_id != settings.OWNER_ID:
            await update.message.reply_text(
                "❌ This command is restricted to the bot owner only."
            )
            return
            
        return await func(update, context)
    return wrapper


def require_admin(permissions: Optional[List[str]] = None):
    """
    Decorator to require user to be admin with specific permissions
    
    Args:
        permissions: List of required permissions (e.g., ["can_restrict_members"])
    
    Usage:
        @require_admin(permissions=["can_restrict_members"])
        async def ban_command(update, context):
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id
            
            # Owner always has permission
            if user_id == settings.OWNER_ID:
                return await func(update, context)
            
            try:
                # Get user's chat member status
                member = await context.bot.get_chat_member(chat_id, user_id)
                
                # Check if user is admin or creator
                if member.status not in ["administrator", "creator"]:
                    await update.message.reply_text(
                        "❌ You need to be an administrator to use this command."
                    )
                    return
                
                # Check specific permissions (if creator, has all permissions)
                if permissions and member.status != "creator":
                    missing_perms = []
                    for perm in permissions:
                        if not getattr(member, perm, False):
                            missing_perms.append(perm)
                    
                    if missing_perms:
                        perms_text = ", ".join(missing_perms)
                        await update.message.reply_text(
                            f"❌ You need the following permissions to use this command:\n"
                            f"• {perms_text.replace('_', ' ').title()}"
                        )
                        return
                
                return await func(update, context)
                
            except Exception as e:
                logger.error(f"Error checking admin permissions: {e}")
                await update.message.reply_text(
                    "❌ Error checking your permissions. Please try again."
                )
                return
                
        return wrapper
    return decorator


def require_bot_admin(permissions: Optional[List[str]] = None):
    """
    Decorator to require bot to be admin with specific permissions
    
    Args:
        permissions: List of required bot permissions
    
    Usage:
        @require_bot_admin(permissions=["can_restrict_members"])
        async def ban_command(update, context):
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            chat_id = update.effective_chat.id
            bot_id = context.bot.id
            
            try:
                # Get bot's chat member status
                bot_member = await context.bot.get_chat_member(chat_id, bot_id)
                
                # Check if bot is admin
                if bot_member.status not in ["administrator", "creator"]:
                    await update.message.reply_text(
                        "❌ I need to be an administrator to execute this command."
                    )
                    return
                
                # Check specific permissions
                if permissions:
                    missing_perms = []
                    for perm in permissions:
                        if not getattr(bot_member, perm, False):
                            missing_perms.append(perm)
                    
                    if missing_perms:
                        perms_text = ", ".join(missing_perms)
                        await update.message.reply_text(
                            f"❌ I need the following permissions to execute this command:\n"
                            f"• {perms_text.replace('_', ' ').title()}\n\n"
                            f"Please grant me these permissions and try again."
                        )
                        return
                
                return await func(update, context)
                
            except Exception as e:
                logger.error(f"Error checking bot permissions: {e}")
                await update.message.reply_text(
                    "❌ Error checking my permissions. Please try again."
                )
                return
                
        return wrapper
    return decorator


def not_self(func: Callable):
    """
    Decorator to prevent user from targeting themselves
    Checks context.args or replied message
    
    Usage:
        @not_self
        async def ban_command(update, context):
            pass
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        target_id = None
        
        # Check reply
        if update.message.reply_to_message:
            target_id = update.message.reply_to_message.from_user.id
        # Check args
        elif context.args and context.args[0].isdigit():
            target_id = int(context.args[0])
        
        if target_id and target_id == user_id:
            await update.message.reply_text(
                "❌ You cannot use this command on yourself."
            )
            return
            
        return await func(update, context)
    return wrapper


def log_command(func: Callable):
    """
    Decorator to log command usage
    
    Usage:
        @log_command
        async def my_command(update, context):
            pass
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat
        command = update.message.text.split()[0] if update.message.text else "unknown"
        
        logger.info(
            f"Command: {command} | "
            f"User: {user.id} ({user.first_name}) | "
            f"Chat: {chat.id} ({chat.title or 'Private'})"
        )
        
        return await func(update, context)
    return wrapper