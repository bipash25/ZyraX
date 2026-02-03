"""
Error Handling Utilities

Centralized error handling for Pyrogram errors with retry logic and user feedback.
"""

import asyncio
from functools import wraps
from typing import Optional, Callable, Any, TypeVar, ParamSpec

from pyrogram.client import Client
from pyrogram.types import Message, CallbackQuery
from pyrogram.errors import (
    FloodWait,
    UserNotParticipant,
    ChatAdminRequired,
    MessageDeleteForbidden,
    MessageNotModified,
    MessageIdInvalid,
    MessageTooLong,
    MediaEmpty,
    MediaInvalid,
    UserIsBlocked,
    UserDeactivated,
    UserDeactivatedBan,
    PeerIdInvalid,
    ChannelInvalid,
    ChannelPrivate,
    ChatWriteForbidden,
    ChatRestricted,
    InputUserDeactivated,
    BadRequest,
    Forbidden,
    RPCError,
)

from zyrax.utils.logger import logger
from zyrax.config import Config
from zyrax.constants import Messages, Limits


# Type variables for decorator typing
P = ParamSpec('P')
T = TypeVar('T')


class BotError(Exception):
    """Base exception for bot-specific errors."""
    pass


class UserError(BotError):
    """Error caused by user input or action."""
    def __init__(self, message: str, notify_user: bool = True):
        self.message = message
        self.notify_user = notify_user
        super().__init__(message)


class PermissionError(BotError):
    """Permission-related error."""
    pass


class RateLimitError(BotError):
    """Rate limit exceeded."""
    def __init__(self, wait_seconds: int):
        self.wait_seconds = wait_seconds
        super().__init__(f"Rate limited for {wait_seconds} seconds")


class ErrorHandler:
    """
    Centralized error handler for Pyrogram errors.
    
    Handles common Telegram API errors with appropriate user feedback
    and logging.
    """
    
    # Errors that should be silently ignored
    SILENT_ERRORS = (
        MessageNotModified,  # Message content unchanged
    )
    
    # Errors related to user/chat not accessible
    USER_ERRORS = (
        UserNotParticipant,
        UserIsBlocked,
        UserDeactivated,
        UserDeactivatedBan,
        InputUserDeactivated,
        PeerIdInvalid,
    )
    
    # Permission-related errors
    PERMISSION_ERRORS = (
        ChatAdminRequired,
        ChatWriteForbidden,
        ChatRestricted,
        Forbidden,
    )
    
    # Chat-related errors
    CHAT_ERRORS = (
        ChannelInvalid,
        ChannelPrivate,
    )
    
    @staticmethod
    def get_error_message(error: Exception) -> str:
        """Get a user-friendly error message for an exception."""
        
        if isinstance(error, FloodWait):
            return f"Rate limited. Please wait {error.value} seconds."
        
        if isinstance(error, ChatAdminRequired):
            return Messages.BOT_NOT_ADMIN
        
        if isinstance(error, UserNotParticipant):
            return "User is not in this chat."
        
        if isinstance(error, MessageDeleteForbidden):
            return "Cannot delete that message (too old or not mine)."
        
        if isinstance(error, MessageNotModified):
            return ""  # Silent - message unchanged
        
        if isinstance(error, MessageIdInvalid):
            return "Message not found or already deleted."
        
        if isinstance(error, MessageTooLong):
            return "Message too long! Maximum is 4096 characters."
        
        if isinstance(error, (MediaEmpty, MediaInvalid)):
            return "Invalid or empty media file."
        
        if isinstance(error, (UserIsBlocked, UserDeactivated, UserDeactivatedBan)):
            return "Cannot reach this user (blocked or deactivated)."
        
        if isinstance(error, PeerIdInvalid):
            return "Invalid user or chat ID."
        
        if isinstance(error, (ChannelInvalid, ChannelPrivate)):
            return "Cannot access this chat (invalid or private)."
        
        if isinstance(error, ChatWriteForbidden):
            return "I don't have permission to send messages here."
        
        if isinstance(error, ChatRestricted):
            return "This chat is restricted."
        
        if isinstance(error, Forbidden):
            return "Action forbidden. Check bot permissions."
        
        if isinstance(error, UserError):
            return error.message
        
        if isinstance(error, BotError):
            return str(error)
        
        if isinstance(error, BadRequest):
            # Log the specific error but show generic message
            logger.warning(f"BadRequest: {error}")
            return "Invalid request. Please try again."
        
        if isinstance(error, RPCError):
            logger.error(f"RPCError: {error}")
            return Messages.ERROR_GENERIC
        
        return Messages.ERROR_GENERIC
    
    @staticmethod
    async def handle(
        client: Client, 
        message: Message, 
        error: Exception,
        notify_user: bool = True,
        notify_owner: bool = True
    ) -> None:
        """
        Handle an error that occurred during message processing.
        
        Args:
            client: Pyrogram client
            message: Original message that caused the error
            error: The exception that was raised
            notify_user: Whether to send error message to user
            notify_owner: Whether to notify bot owner of unhandled errors
        """
        # Silent errors - just log debug
        if isinstance(error, ErrorHandler.SILENT_ERRORS):
            logger.debug(f"Silent error in {message.chat.id}: {error}")
            return
        
        # FloodWait - special handling
        if isinstance(error, FloodWait):
            wait_time = error.value
            logger.warning(f"FloodWait: {wait_time}s in chat {message.chat.id}")
            
            if notify_user:
                try:
                    await message.reply(f"Rate limited. Please wait {wait_time} seconds.")
                except Exception:
                    pass
            return
        
        # Get user-friendly message
        error_message = ErrorHandler.get_error_message(error)
        
        # Log the error
        if isinstance(error, (ErrorHandler.USER_ERRORS, ErrorHandler.PERMISSION_ERRORS)):
            logger.info(f"Expected error in {message.chat.id}: {error}")
        else:
            logger.error(
                f"Error in chat {message.chat.id} from user {message.from_user.id if message.from_user else 'unknown'}: {error}",
                exc_info=True
            )
        
        # Notify user
        if notify_user and error_message:
            try:
                await message.reply(f"Error: {error_message}")
            except Exception as e:
                logger.debug(f"Could not send error message: {e}")
        
        # Notify owner for unexpected errors
        if notify_owner and not isinstance(error, (
            *ErrorHandler.SILENT_ERRORS,
            *ErrorHandler.USER_ERRORS,
            *ErrorHandler.PERMISSION_ERRORS,
            *ErrorHandler.CHAT_ERRORS,
            FloodWait,
            UserError,
        )):
            await ErrorHandler.notify_owner(client, message, error)
    
    @staticmethod
    async def handle_callback(
        client: Client,
        callback_query: CallbackQuery,
        error: Exception,
        notify_user: bool = True
    ) -> None:
        """
        Handle an error that occurred during callback query processing.
        
        Args:
            client: Pyrogram client
            callback_query: The callback query
            error: The exception that was raised
            notify_user: Whether to show error alert to user
        """
        # Silent errors
        if isinstance(error, ErrorHandler.SILENT_ERRORS):
            logger.debug(f"Silent callback error: {error}")
            return
        
        error_message = ErrorHandler.get_error_message(error)
        
        # Log the error
        logger.error(f"Callback error: {error}", exc_info=True)
        
        # Show alert to user
        if notify_user and error_message:
            try:
                await callback_query.answer(error_message, show_alert=True)
            except Exception:
                pass
    
    @staticmethod
    async def notify_owner(
        client: Client, 
        message: Message, 
        error: Exception
    ) -> None:
        """Send error notification to bot owner."""
        if not Config.OWNER_ID:
            return
        
        try:
            chat_title = message.chat.title or "Private"
            user_info = f"@{message.from_user.username}" if message.from_user and message.from_user.username else str(message.from_user.id if message.from_user else "unknown")
            
            error_text = (
                f"**Error Report**\n\n"
                f"**Chat:** {chat_title} (`{message.chat.id}`)\n"
                f"**User:** {user_info}\n"
                f"**Error:** `{type(error).__name__}`\n"
                f"**Details:** {str(error)[:500]}"
            )
            
            await client.send_message(Config.OWNER_ID, error_text)
        except Exception as e:
            logger.error(f"Failed to notify owner: {e}")


async def retry_on_flood(
    coro_func: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    max_wait: int = 60,
    **kwargs: Any
) -> Any:
    """
    Retry a coroutine on FloodWait errors.
    
    Args:
        coro_func: Async function to call
        *args: Arguments to pass to function
        max_retries: Maximum number of retries
        max_wait: Maximum seconds to wait (will skip if FloodWait exceeds this)
        **kwargs: Keyword arguments to pass to function
        
    Returns:
        Result of the coroutine
        
    Raises:
        The original exception if retries exhausted or wait too long
    """
    last_exception: Optional[Exception] = None
    
    for attempt in range(max_retries + 1):
        try:
            return await coro_func(*args, **kwargs)
        except FloodWait as e:
            last_exception = e
            wait_time = int(e.value) if hasattr(e, 'value') else 30
            
            if wait_time > max_wait:
                logger.warning(f"FloodWait {wait_time}s exceeds max_wait {max_wait}s")
                raise
            
            if attempt < max_retries:
                logger.info(f"FloodWait: sleeping {wait_time}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                raise
    
    if last_exception:
        raise last_exception
    raise RuntimeError("Unexpected state in retry_on_flood")


def error_handler(
    func: Optional[Callable[P, T]] = None,
    *,
    notify_user: bool = True,
    notify_owner: bool = True,
    reraise: bool = False
) -> Callable:
    """
    Decorator to handle errors in command handlers.
    
    Can be used with or without parentheses:
        @error_handler
        async def my_command(client, message):
            ...
            
        @error_handler()
        async def my_command(client, message):
            ...
            
        @error_handler(notify_owner=False)
        async def less_important_command(client, message):
            ...
    
    Args:
        func: The function being decorated (when used without parentheses)
        notify_user: Send error message to user
        notify_owner: Notify bot owner of unexpected errors
        reraise: Re-raise the exception after handling
        
    Returns:
        Decorated function
    """
    def decorator(f: Callable[P, T]) -> Callable[P, T]:
        @wraps(f)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Find client and message in args
            client = None
            message = None
            callback_query = None
            
            for arg in args:
                if isinstance(arg, Client):
                    client = arg
                elif isinstance(arg, Message):
                    message = arg
                elif isinstance(arg, CallbackQuery):
                    callback_query = arg
            
            try:
                return await f(*args, **kwargs)
            except Exception as e:
                if client and message:
                    await ErrorHandler.handle(
                        client, message, e,
                        notify_user=notify_user,
                        notify_owner=notify_owner
                    )
                elif client and callback_query:
                    await ErrorHandler.handle_callback(
                        client, callback_query, e,
                        notify_user=notify_user
                    )
                else:
                    logger.error(f"Error in {f.__name__}: {e}", exc_info=True)
                
                if reraise:
                    raise
        
        return wrapper  # type: ignore
    
    # If called without parentheses, func is the decorated function
    if func is not None:
        return decorator(func)
    # If called with parentheses, return the decorator
    return decorator


def silent_error_handler(func: Callable[P, T]) -> Callable[P, T]:
    """
    Decorator that silently handles all errors (just logs them).
    
    Useful for background tasks where you don't want errors to propagate.
    
    Example:
        @silent_error_handler
        async def background_cleanup():
            ...
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Silent error in {func.__name__}: {e}", exc_info=True)
            return None
    
    return wrapper  # type: ignore
