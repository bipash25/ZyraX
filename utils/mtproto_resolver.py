"""
MTProto-based user resolution
Uses Pyrogram for advanced user lookups
"""
import logging
from typing import Optional, Tuple
from telegram import User as TelegramUser
from pyrogram.types import User as PyrogramUser
from pyrogram.errors import UsernameNotOccupied, UsernameInvalid

logger = logging.getLogger(__name__)


async def resolve_username_mtproto(
    mtproto_client,
    chat_id: int,
    username: str
) -> Optional[TelegramUser]:
    """
    Resolve username using MTProto (Pyrogram)
    
    Args:
        mtproto_client: Pyrogram client instance
        chat_id: Chat ID to search in
        username: Username to resolve (without @)
        
    Returns:
        Telegram User object or None
    """
    if not mtproto_client or not mtproto_client.client:
        logger.debug("MTProto client not available")
        return None
    
    try:
        # Try to get user info by username
        pyro_user = await mtproto_client.client.get_users(username)
        
        if pyro_user:
            # Convert Pyrogram User to Telegram User
            telegram_user = convert_pyrogram_to_telegram_user(pyro_user)
            logger.debug(f"Resolved username {username} via MTProto: {telegram_user.id}")
            return telegram_user
            
    except (UsernameNotOccupied, UsernameInvalid):
        logger.debug(f"Username {username} not found")
        return None
    except Exception as e:
        logger.error(f"MTProto username resolution error: {e}")
        return None
    
    return None


async def get_chat_member_mtproto(
    mtproto_client,
    chat_id: int,
    user_id: int
) -> Optional[TelegramUser]:
    """
    Get chat member info using MTProto
    
    Args:
        mtproto_client: Pyrogram client instance
        chat_id: Chat ID
        user_id: User ID to get info for
        
    Returns:
        Telegram User object or None
    """
    if not mtproto_client or not mtproto_client.client:
        logger.debug("MTProto client not available")
        return None
    
    try:
        # Get chat member
        member = await mtproto_client.client.get_chat_member(chat_id, user_id)
        
        if member and member.user:
            telegram_user = convert_pyrogram_to_telegram_user(member.user)
            logger.debug(f"Got user {user_id} info via MTProto")
            return telegram_user
            
    except Exception as e:
        logger.debug(f"MTProto get_chat_member error: {e}")
        return None
    
    return None


def convert_pyrogram_to_telegram_user(pyro_user: PyrogramUser) -> TelegramUser:
    """
    Convert Pyrogram User object to python-telegram-bot User object
    
    Args:
        pyro_user: Pyrogram User object
        
    Returns:
        Telegram User object
    """
    return TelegramUser(
        id=pyro_user.id,
        is_bot=pyro_user.is_bot or False,
        first_name=pyro_user.first_name or f"User {pyro_user.id}",
        last_name=pyro_user.last_name,
        username=pyro_user.username,
        language_code=pyro_user.language_code,
        is_premium=pyro_user.is_premium or False
    )