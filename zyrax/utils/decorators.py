"""
Command Decorators

Decorators for command handlers including admin checks, rate limiting, and permissions.
"""

from functools import wraps
from typing import Optional, List, Callable, Any, Set
from cachetools import TTLCache

from pyrogram.client import Client
from pyrogram.types import Message, CallbackQuery, ChatMember
from pyrogram.enums import ChatMemberStatus, ChatType

from zyrax.config import Config
from zyrax.constants import Limits, Messages
from zyrax.utils.logger import logger


# Cache for admin status - key: (chat_id, user_id), value: ChatMember
_admin_cache: TTLCache = TTLCache(maxsize=1000, ttl=Limits.ADMIN_CACHE_TTL)

# Cache for bot admin status in chats
_bot_admin_cache: TTLCache = TTLCache(maxsize=500, ttl=Limits.ADMIN_CACHE_TTL)


async def get_chat_member_cached(
    client: Client, 
    chat_id: int, 
    user_id: int, 
    use_cache: bool = True
) -> Optional[ChatMember]:
    """
    Get chat member with caching.
    
    Args:
        client: Pyrogram client
        chat_id: Chat ID
        user_id: User ID
        use_cache: Whether to use cache (default True)
        
    Returns:
        ChatMember or None if user not found
    """
    cache_key = (chat_id, user_id)
    
    if use_cache and cache_key in _admin_cache:
        return _admin_cache[cache_key]
    
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if use_cache:
            _admin_cache[cache_key] = member
        return member
    except Exception as e:
        logger.debug(f"Error getting chat member {user_id} in {chat_id}: {e}")
        return None


async def is_user_admin(
    client: Client, 
    chat_id: int, 
    user_id: int,
    use_cache: bool = True
) -> bool:
    """
    Check if a user is admin in a chat.
    
    Args:
        client: Pyrogram client
        chat_id: Chat ID
        user_id: User ID
        use_cache: Whether to use cache
        
    Returns:
        True if user is admin or owner
    """
    # Bot owner is admin everywhere
    if Config.is_owner(user_id):
        return True
    
    member = await get_chat_member_cached(client, chat_id, user_id, use_cache)
    if member is None:
        return False
    
    return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)


async def is_user_owner(
    client: Client, 
    chat_id: int, 
    user_id: int,
    use_cache: bool = True
) -> bool:
    """
    Check if a user is the chat owner.
    
    Args:
        client: Pyrogram client
        chat_id: Chat ID
        user_id: User ID
        use_cache: Whether to use cache
        
    Returns:
        True if user is chat owner
    """
    member = await get_chat_member_cached(client, chat_id, user_id, use_cache)
    if member is None:
        return False
    
    return member.status == ChatMemberStatus.OWNER


async def check_permission(
    client: Client,
    chat_id: int,
    user_id: int,
    permission: str,
    use_cache: bool = True
) -> bool:
    """
    Check if a user has a specific permission.
    
    Args:
        client: Pyrogram client
        chat_id: Chat ID
        user_id: User ID
        permission: Permission name (e.g., 'can_delete_messages')
        use_cache: Whether to use cache
        
    Returns:
        True if user has the permission
    """
    # Bot owner has all permissions
    if Config.is_owner(user_id):
        return True
    
    member = await get_chat_member_cached(client, chat_id, user_id, use_cache)
    if member is None:
        return False
    
    # Owner has all permissions
    if member.status == ChatMemberStatus.OWNER:
        return True
    
    # Check specific permission for admins
    if member.status == ChatMemberStatus.ADMINISTRATOR:
        if member.privileges is None:
            return False
        return getattr(member.privileges, permission, False)
    
    return False


async def is_bot_admin(client: Client, chat_id: int) -> bool:
    """
    Check if the bot has admin privileges in a chat.
    
    Args:
        client: Pyrogram client
        chat_id: Chat ID
        
    Returns:
        True if bot is admin
    """
    if chat_id in _bot_admin_cache:
        return _bot_admin_cache[chat_id]
    
    try:
        bot_member = await client.get_chat_member(chat_id, "me")
        is_admin = bot_member.status in (
            ChatMemberStatus.ADMINISTRATOR, 
            ChatMemberStatus.OWNER
        )
        _bot_admin_cache[chat_id] = is_admin
        return is_admin
    except Exception as e:
        logger.debug(f"Error checking bot admin status in {chat_id}: {e}")
        return False


def invalidate_admin_cache(chat_id: int, user_id: Optional[int] = None) -> None:
    """
    Invalidate admin cache for a chat/user.
    
    Args:
        chat_id: Chat ID
        user_id: User ID (optional, if None invalidates all for chat)
    """
    if user_id:
        cache_key = (chat_id, user_id)
        _admin_cache.pop(cache_key, None)
    else:
        # Remove all entries for this chat
        keys_to_remove = [k for k in _admin_cache.keys() if k[0] == chat_id]
        for key in keys_to_remove:
            _admin_cache.pop(key, None)
    
    # Also invalidate bot admin cache for this chat
    _bot_admin_cache.pop(chat_id, None)


def require_admin(
    permissions: Optional[List[str]] = None,
    allow_owner_bypass: bool = True,
    check_bot_admin: bool = True,
    silent: bool = False
) -> Callable:
    """
    Decorator to require admin privileges for a command.
    
    Args:
        permissions: List of required permissions (e.g., ['can_restrict_members'])
        allow_owner_bypass: Allow bot owner to bypass checks
        check_bot_admin: Also check if bot is admin
        silent: Don't send error messages
        
    Returns:
        Decorated function
        
    Example:
        @require_admin()
        async def ban_user(client, message):
            ...
            
        @require_admin(permissions=['can_delete_messages'])
        async def purge(client, message):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(client: Client, message: Message, *args: Any, **kwargs: Any) -> Any:
            # Skip for private chats
            if message.chat.type == ChatType.PRIVATE:
                return await func(client, message, *args, **kwargs)
            
            if not message.from_user:
                return
            
            user_id = message.from_user.id
            chat_id = message.chat.id
            
            # Bot owner bypass
            if allow_owner_bypass and Config.is_owner(user_id):
                # Still check bot admin if required
                if check_bot_admin:
                    if not await is_bot_admin(client, chat_id):
                        if not silent:
                            await message.reply_text(Messages.BOT_NOT_ADMIN)
                        return
                return await func(client, message, *args, **kwargs)
            
            # Check if user is admin
            member = await get_chat_member_cached(client, chat_id, user_id)
            if member is None:
                if not silent:
                    await message.reply_text(Messages.ADMIN_REQUIRED)
                return
            
            is_admin = member.status in (
                ChatMemberStatus.ADMINISTRATOR, 
                ChatMemberStatus.OWNER
            )
            
            if not is_admin:
                if not silent:
                    await message.reply_text(Messages.ADMIN_REQUIRED)
                return
            
            # Check specific permissions (if not owner)
            if permissions and member.status != ChatMemberStatus.OWNER:
                if member.privileges is None:
                    if not silent:
                        await message.reply_text(Messages.PERMISSION_DENIED)
                    return
                
                missing = []
                for perm in permissions:
                    if not getattr(member.privileges, perm, False):
                        missing.append(perm.replace('can_', '').replace('_', ' '))
                
                if missing:
                    if not silent:
                        await message.reply_text(
                            f"You need these permissions: {', '.join(missing)}"
                        )
                    return
            
            # Check bot admin status
            if check_bot_admin:
                if not await is_bot_admin(client, chat_id):
                    if not silent:
                        await message.reply_text(Messages.BOT_NOT_ADMIN)
                    return
            
            return await func(client, message, *args, **kwargs)
        return wrapper
    return decorator


def require_owner(silent: bool = False) -> Callable:
    """
    Decorator to require bot owner privileges.
    
    Args:
        silent: Don't send error messages
        
    Returns:
        Decorated function
        
    Example:
        @require_owner()
        async def broadcast(client, message):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(client: Client, message: Message, *args: Any, **kwargs: Any) -> Any:
            if not message.from_user:
                return
            
            if not Config.is_owner(message.from_user.id):
                if not silent:
                    await message.reply_text(Messages.OWNER_REQUIRED)
                return
            
            return await func(client, message, *args, **kwargs)
        return wrapper
    return decorator


def require_chat_owner(silent: bool = False) -> Callable:
    """
    Decorator to require chat owner privileges.
    
    Args:
        silent: Don't send error messages
        
    Returns:
        Decorated function
        
    Example:
        @require_chat_owner()
        async def transfer_ownership(client, message):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(client: Client, message: Message, *args: Any, **kwargs: Any) -> Any:
            if message.chat.type == ChatType.PRIVATE:
                return await func(client, message, *args, **kwargs)
            
            if not message.from_user:
                return
            
            is_owner = await is_user_owner(
                client, 
                message.chat.id, 
                message.from_user.id
            )
            
            # Also allow bot owner
            if not is_owner and not Config.is_owner(message.from_user.id):
                if not silent:
                    await message.reply_text("Only the chat owner can use this command!")
                return
            
            return await func(client, message, *args, **kwargs)
        return wrapper
    return decorator


def require_private(silent: bool = False) -> Callable:
    """
    Decorator to require command to be used in private chat.
    
    Args:
        silent: Don't send error messages
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(client: Client, message: Message, *args: Any, **kwargs: Any) -> Any:
            if message.chat.type != ChatType.PRIVATE:
                if not silent:
                    await message.reply_text("This command can only be used in private chat!")
                return
            return await func(client, message, *args, **kwargs)
        return wrapper
    return decorator


def require_group(silent: bool = False) -> Callable:
    """
    Decorator to require command to be used in a group.
    
    Args:
        silent: Don't send error messages
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(client: Client, message: Message, *args: Any, **kwargs: Any) -> Any:
            if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
                if not silent:
                    await message.reply_text("This command can only be used in groups!")
                return
            return await func(client, message, *args, **kwargs)
        return wrapper
    return decorator


def log_command(func: Callable) -> Callable:
    """
    Decorator to log command usage.
    
    Example:
        @log_command
        async def start(client, message):
            ...
    """
    @wraps(func)
    async def wrapper(client: Client, message: Message, *args: Any, **kwargs: Any) -> Any:
        user_id = message.from_user.id if message.from_user else 0
        chat_id = message.chat.id
        command = message.command[0] if message.command else func.__name__
        
        logger.info(f"Command /{command} by {user_id} in {chat_id}")
        
        return await func(client, message, *args, **kwargs)
    return wrapper


def handle_callback(func: Callable) -> Callable:
    """
    Decorator for callback query handlers.
    Ensures callback query is answered and handles errors.
    
    Example:
        @handle_callback
        async def button_handler(client, callback_query):
            ...
    """
    @wraps(func)
    async def wrapper(
        client: Client, 
        callback_query: CallbackQuery, 
        *args: Any, 
        **kwargs: Any
    ) -> Any:
        try:
            result = await func(client, callback_query, *args, **kwargs)
            # Try to answer callback if not already answered
            try:
                await callback_query.answer()
            except Exception:
                pass  # Already answered or expired
            return result
        except Exception as e:
            logger.error(f"Error in callback handler {func.__name__}: {e}")
            try:
                await callback_query.answer("An error occurred!", show_alert=True)
            except Exception:
                pass
            raise
    return wrapper
