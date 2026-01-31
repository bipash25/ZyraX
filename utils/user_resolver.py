"""
User resolution utility
Resolves users from various sources: reply, mention, username, ID
"""
import logging
from typing import Optional, Tuple
from telegram import Update, User
from telegram.ext import ContextTypes
from utils.mtproto_resolver import resolve_username_mtproto

logger = logging.getLogger(__name__)


async def resolve_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    allow_self: bool = False
) -> Tuple[Optional[User], Optional[str]]:
    """
    Resolve user from multiple sources with priority order:
    1. Reply to message
    2. Text mention entity
    3. Username argument
    4. User ID argument
    5. Self (if allow_self=True)
    
    Args:
        update: Telegram update
        context: PTB context
        allow_self: Allow resolving to command sender
        
    Returns:
        Tuple of (User object or None, resolution method)
    """
    message = update.effective_message
    user_obj = update.effective_user
    
    # 1. Check reply to message
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
        logger.debug(f"Resolved user {target_user.id} via reply")
        return target_user, "reply"
    
    # 2. Check text mentions (entities)
    if message.entities:
        for entity in message.entities:
            if entity.type == "text_mention" and entity.user:
                logger.debug(f"Resolved user {entity.user.id} via text mention")
                return entity.user, "text_mention"
    
    # 3. Check arguments
    if not context.args:
        # No args provided
        if allow_self:
            logger.debug(f"Resolved to self: {user_obj.id}")
            return user_obj, "self"
        return None, None
    
    target_arg = context.args[0]
    
    # 4. Check if it's a user ID
    if target_arg.isdigit():
        user_id = int(target_arg)
        try:
            # Try to get user from chat members
            chat_id = update.effective_chat.id
            member = await context.bot.get_chat_member(chat_id, user_id)
            if member and member.user:
                logger.debug(f"Resolved user {user_id} via ID from chat member")
                return member.user, "user_id"
        except Exception as e:
            logger.debug(f"Could not resolve user ID {user_id}: {e}")
            # Create a minimal User object with just the ID
            # This is a fallback for when we can't fetch full user info
            from telegram import User as TelegramUser
            user = TelegramUser(
                id=user_id,
                is_bot=False,
                first_name=f"User {user_id}"
            )
            return user, "user_id_minimal"
    
    # 5. Check if it's a username
    if target_arg.startswith("@"):
        username = target_arg[1:]
    else:
        username = target_arg
    
    # Try to find user by username
    try:
        chat_id = update.effective_chat.id
        
        # First check in admins (most efficient)
        try:
            admins = await context.bot.get_chat_administrators(chat_id)
            for admin in admins:
                if admin.user.username and admin.user.username.lower() == username.lower():
                    logger.debug(f"Resolved user {admin.user.id} via username from admins")
                    return admin.user, "username_admin"
        except Exception as e:
            logger.debug(f"Could not check admins: {e}")
        
        # Try MTProto resolution (most reliable for usernames)
        mtproto_client = context.application.bot_data.get('mtproto_client')
        if mtproto_client:
            mtproto_user = await resolve_username_mtproto(mtproto_client, chat_id, username)
            if mtproto_user:
                return mtproto_user, "username_mtproto"
        
    except Exception as e:
        logger.debug(f"Error resolving username {username}: {e}")
    
    # Could not resolve
    logger.debug(f"Could not resolve user from: {target_arg}")
    return None, None


def mention_user(user: User, use_html: bool = True) -> str:
    """
    Create a mention link for a user
    
    Args:
        user: User object
        use_html: Use HTML format (True) or Markdown (False)
        
    Returns:
        Formatted mention string
    """
    if not user:
        return "Unknown User"
    
    name = user.first_name or f"User {user.id}"
    
    if use_html:
        return f'<a href="tg://user?id={user.id}">{name}</a>'
    else:
        # Markdown format
        return f"[{name}](tg://user?id={user.id})"


def get_user_link(user: User) -> str:
    """
    Get tg:// link to user
    
    Args:
        user: User object
        
    Returns:
        tg:// link string
    """
    if not user:
        return ""
    return f"tg://user?id={user.id}"


def format_user_info(user: User) -> str:
    """
    Format user information for display
    
    Args:
        user: User object
        
    Returns:
        Formatted user info string
    """
    if not user:
        return "Unknown User"
    
    info = f"<b>User Information</b>\n\n"
    info += f"👤 Name: {user.first_name}"
    
    if user.last_name:
        info += f" {user.last_name}"
    
    info += f"\n🆔 ID: <code>{user.id}</code>"
    
    if user.username:
        info += f"\n📝 Username: @{user.username}"
    
    if user.is_bot:
        info += f"\n🤖 Bot: Yes"
    
    if user.is_premium:
        info += f"\n⭐ Premium: Yes"
    
    return info