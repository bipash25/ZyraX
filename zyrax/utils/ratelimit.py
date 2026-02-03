"""
Rate Limiting Utilities

Redis-based rate limiting for distributed deployments with fallback to in-memory.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Callable, Any, Tuple
from enum import Enum

from pyrogram.client import Client
from pyrogram.types import Message

from zyrax.constants import Limits, Messages
from zyrax.utils.logger import logger


class RateLimitResult(Enum):
    """Rate limit check result."""
    ALLOWED = "allowed"
    LIMITED = "limited"
    ERROR = "error"


class InMemoryRateLimiter:
    """
    In-memory rate limiter using sliding window.
    
    Used as fallback when Redis is unavailable.
    """
    
    def __init__(self):
        self._attempts: dict = defaultdict(list)
    
    def check(
        self, 
        key: str, 
        max_attempts: int, 
        window_seconds: int
    ) -> Tuple[bool, int]:
        """
        Check if rate limit allows the action.
        
        Args:
            key: Unique identifier for rate limit (e.g., "user:123:command")
            max_attempts: Maximum attempts allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (allowed: bool, current_count: int)
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        
        # Clean old attempts
        self._attempts[key] = [t for t in self._attempts[key] if t > cutoff]
        
        current_count = len(self._attempts[key])
        
        if current_count >= max_attempts:
            return (False, current_count)
        
        self._attempts[key].append(now)
        return (True, current_count + 1)
    
    def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        self._attempts.pop(key, None)
    
    def cleanup(self, max_age_seconds: int = 3600) -> int:
        """
        Cleanup old entries.
        
        Args:
            max_age_seconds: Maximum age of entries to keep
            
        Returns:
            Number of keys removed
        """
        cutoff = datetime.now() - timedelta(seconds=max_age_seconds)
        keys_to_remove = []
        
        for key, attempts in self._attempts.items():
            # Remove entries older than cutoff
            self._attempts[key] = [t for t in attempts if t > cutoff]
            if not self._attempts[key]:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._attempts[key]
        
        return len(keys_to_remove)


class RedisRateLimiter:
    """
    Redis-based rate limiter using sliding window algorithm.
    
    Supports distributed rate limiting across multiple bot instances.
    """
    
    def __init__(self, prefix: str = "ratelimit"):
        self._prefix = prefix
        self._cache = None
        self._fallback = InMemoryRateLimiter()
    
    def _get_cache(self):
        """Get cache instance lazily to avoid circular imports."""
        if self._cache is None:
            try:
                from zyrax.database import db
                if db._initialized:
                    self._cache = db.cache
            except Exception:
                pass
        return self._cache
    
    def _make_key(self, key: str) -> str:
        """Create a Redis key with prefix."""
        return f"{self._prefix}:{key}"
    
    async def check(
        self, 
        key: str, 
        max_attempts: int, 
        window_seconds: int
    ) -> Tuple[bool, int]:
        """
        Check if rate limit allows the action.
        
        Uses Redis if available, falls back to in-memory.
        
        Args:
            key: Unique identifier for rate limit
            max_attempts: Maximum attempts allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (allowed: bool, current_count: int)
        """
        cache = self._get_cache()
        
        if cache is None:
            # Fallback to in-memory
            return self._fallback.check(key, max_attempts, window_seconds)
        
        try:
            redis_key = self._make_key(key)
            result = await cache.check_rate_limit(
                redis_key, 
                max_attempts, 
                window_seconds
            )
            return result
        except Exception as e:
            logger.debug(f"Redis rate limit check failed, using fallback: {e}")
            return self._fallback.check(key, max_attempts, window_seconds)
    
    async def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        cache = self._get_cache()
        
        if cache:
            try:
                await cache.delete(self._make_key(key))
            except Exception:
                pass
        
        self._fallback.reset(key)
    
    async def get_remaining(
        self, 
        key: str, 
        max_attempts: int
    ) -> int:
        """
        Get remaining attempts before rate limit.
        
        Args:
            key: Rate limit key
            max_attempts: Maximum attempts allowed
            
        Returns:
            Number of remaining attempts
        """
        cache = self._get_cache()
        
        if cache:
            try:
                return await cache.get_rate_limit_remaining(
                    self._make_key(key), 
                    max_attempts
                )
            except Exception:
                pass
        
        return max_attempts  # Conservative fallback


# Global rate limiter instance
_rate_limiter = RedisRateLimiter()


def make_rate_limit_key(
    user_id: int, 
    command: Optional[str] = None, 
    chat_id: Optional[int] = None
) -> str:
    """
    Create a rate limit key.
    
    Args:
        user_id: User ID
        command: Command name (optional)
        chat_id: Chat ID for per-chat limits (optional)
        
    Returns:
        Rate limit key string
    """
    parts = [str(user_id)]
    if chat_id:
        parts.append(str(chat_id))
    if command:
        parts.append(command)
    return ":".join(parts)


def rate_limit(
    max_attempts: int = Limits.DEFAULT_RATE_LIMIT_MAX,
    window: int = Limits.DEFAULT_RATE_LIMIT_WINDOW,
    per_chat: bool = False,
    silent: bool = False,
    message: Optional[str] = None
) -> Callable:
    """
    Decorator to rate limit a command handler.
    
    Args:
        max_attempts: Maximum attempts allowed in window
        window: Time window in seconds
        per_chat: Apply limit per chat instead of globally per user
        silent: Don't send rate limit message
        message: Custom rate limit message
        
    Returns:
        Decorated function
        
    Example:
        @rate_limit(max_attempts=5, window=60)
        async def expensive_command(client, message):
            ...
            
        @rate_limit(max_attempts=3, window=30, per_chat=True)
        async def per_chat_command(client, message):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(client: Client, msg: Message, *args: Any, **kwargs: Any) -> Any:
            if not msg.from_user:
                return await func(client, msg, *args, **kwargs)
            
            # Build rate limit key
            key = make_rate_limit_key(
                msg.from_user.id,
                func.__name__,
                msg.chat.id if per_chat else None
            )
            
            # Check rate limit
            allowed, count = await _rate_limiter.check(key, max_attempts, window)
            
            if not allowed:
                if not silent:
                    limit_message = message or Messages.RATE_LIMITED
                    await msg.reply(limit_message)
                return
            
            return await func(client, msg, *args, **kwargs)
        return wrapper
    return decorator


def admin_rate_limit(
    max_attempts: int = Limits.ADMIN_COMMAND_RATE_LIMIT,
    window: int = Limits.DEFAULT_RATE_LIMIT_WINDOW
) -> Callable:
    """
    Rate limit decorator for admin commands.
    
    Uses default limits suitable for admin operations.
    """
    return rate_limit(max_attempts=max_attempts, window=window, per_chat=True)


def game_rate_limit(
    max_attempts: int = Limits.GAME_COMMAND_RATE_LIMIT,
    window: int = Limits.DEFAULT_RATE_LIMIT_WINDOW
) -> Callable:
    """
    Rate limit decorator for game commands.
    
    Uses default limits suitable for games.
    """
    return rate_limit(max_attempts=max_attempts, window=window, per_chat=True)


def ai_rate_limit(
    max_attempts: int = Limits.AI_COMMAND_RATE_LIMIT,
    window: int = Limits.DEFAULT_RATE_LIMIT_WINDOW
) -> Callable:
    """
    Rate limit decorator for AI commands.
    
    Uses default limits suitable for AI operations.
    """
    return rate_limit(max_attempts=max_attempts, window=window)


async def check_rate_limit(
    user_id: int,
    action: str,
    max_attempts: int = Limits.DEFAULT_RATE_LIMIT_MAX,
    window: int = Limits.DEFAULT_RATE_LIMIT_WINDOW,
    chat_id: Optional[int] = None
) -> bool:
    """
    Programmatic rate limit check.
    
    Args:
        user_id: User ID
        action: Action identifier
        max_attempts: Maximum attempts
        window: Time window
        chat_id: Chat ID for per-chat limits
        
    Returns:
        True if action is allowed
    """
    key = make_rate_limit_key(user_id, action, chat_id)
    allowed, _ = await _rate_limiter.check(key, max_attempts, window)
    return allowed


async def reset_rate_limit(
    user_id: int,
    action: str,
    chat_id: Optional[int] = None
) -> None:
    """
    Reset rate limit for a user/action.
    
    Args:
        user_id: User ID
        action: Action identifier
        chat_id: Chat ID for per-chat limits
    """
    key = make_rate_limit_key(user_id, action, chat_id)
    await _rate_limiter.reset(key)


# Backward compatibility
class CommandRateLimit:
    """Backward compatible rate limiter class."""
    
    def __init__(self):
        self._limiter = InMemoryRateLimiter()
    
    def check(
        self, 
        user_id: int, 
        command: str, 
        max_attempts: int = 10, 
        window: int = 60
    ) -> bool:
        """Check rate limit (sync version for backward compat)."""
        key = make_rate_limit_key(user_id, command)
        allowed, _ = self._limiter.check(key, max_attempts, window)
        return allowed


# Backward compatibility instance
rate_limiter = CommandRateLimit()
