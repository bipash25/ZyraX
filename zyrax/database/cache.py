"""
Redis Cache Wrapper

Provides a clean interface for caching operations with JSON serialization.
"""

import json
import redis.asyncio as redis
from typing import Optional, Any, Union
from zyrax.utils.logger import logger


class Cache:
    """
    Redis cache wrapper with JSON serialization support.
    
    Features:
        - Automatic JSON serialization/deserialization
        - TTL support for all operations
        - Rate limiting helpers
        - Pipeline support for batch operations
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Deserialized value or None if not found
        """
        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except json.JSONDecodeError:
            logger.warning(f"Failed to decode cache value for key: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: int = 300,
        nx: bool = False
    ) -> bool:
        """
        Set a value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (default 5 minutes)
            nx: Only set if key doesn't exist
            
        Returns:
            True if set successfully
        """
        try:
            serialized = json.dumps(value, default=str)
            if nx:
                result = await self.redis.set(key, serialized, ex=ttl, nx=True)
                return result is not None
            else:
                await self.redis.setex(key, ttl, serialized)
                return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted
        """
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def incr(self, key: str) -> int:
        """
        Increment a counter.
        
        Args:
            key: Cache key
            
        Returns:
            New value after increment
        """
        try:
            return await self.redis.incr(key)
        except Exception as e:
            logger.error(f"Cache incr error for key {key}: {e}")
            return 0
    
    async def incr_with_ttl(self, key: str, ttl: int = 30) -> int:
        """
        Increment a counter with TTL (useful for rate limiting).
        
        If the key doesn't exist, it will be created with the TTL.
        If it exists, only the value is incremented (TTL not reset).
        
        Args:
            key: Cache key
            ttl: TTL in seconds for new keys
            
        Returns:
            New value after increment
        """
        try:
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, ttl, nx=True)  # Only set expire if not exists
            results = await pipe.execute()
            return results[0]  # Return the incremented value
        except Exception as e:
            logger.error(f"Cache incr_with_ttl error for key {key}: {e}")
            return 0
    
    async def get_int(self, key: str, default: int = 0) -> int:
        """
        Get an integer value from cache.
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Integer value or default
        """
        try:
            data = await self.redis.get(key)
            if data is not None:
                return int(data)
            return default
        except (ValueError, TypeError):
            return default
        except Exception as e:
            logger.error(f"Cache get_int error for key {key}: {e}")
            return default
    
    async def setex(self, key: str, ttl: int, value: Any) -> bool:
        """
        Set with expiration (raw value, not JSON).
        
        Args:
            key: Cache key
            ttl: TTL in seconds
            value: Value to store (converted to string)
            
        Returns:
            True if set successfully
        """
        try:
            await self.redis.setex(key, ttl, str(value))
            return True
        except Exception as e:
            logger.error(f"Cache setex error for key {key}: {e}")
            return False
    
    async def get_or_set(
        self, 
        key: str, 
        factory, 
        ttl: int = 300
    ) -> Optional[Any]:
        """
        Get a value from cache, or compute and store it.
        
        Args:
            key: Cache key
            factory: Async function to compute value if not cached
            ttl: TTL in seconds
            
        Returns:
            Cached or computed value
        """
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        try:
            value = await factory()
            if value is not None:
                await self.set(key, value, ttl)
            return value
        except Exception as e:
            logger.error(f"Cache get_or_set error for key {key}: {e}")
            return None
    
    async def mget(self, keys: list) -> dict:
        """
        Get multiple values at once.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dict mapping keys to values (None for missing keys)
        """
        try:
            values = await self.redis.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = None
                else:
                    result[key] = None
            return result
        except Exception as e:
            logger.error(f"Cache mget error: {e}")
            return {key: None for key in keys}
    
    async def ttl(self, key: str) -> int:
        """
        Get remaining TTL for a key.
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds, -1 if no TTL, -2 if key doesn't exist
        """
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.error(f"Cache ttl error for key {key}: {e}")
            return -2
    
    # =========================================================================
    # Rate Limiting Helpers
    # =========================================================================
    
    async def check_rate_limit(
        self, 
        key: str, 
        max_requests: int, 
        window: int
    ) -> tuple[bool, int]:
        """
        Check if a rate limit has been exceeded.
        
        Args:
            key: Rate limit key (e.g., "ratelimit:user:123:command")
            max_requests: Maximum requests allowed in window
            window: Time window in seconds
            
        Returns:
            Tuple of (allowed: bool, current_count: int)
        """
        current = await self.incr_with_ttl(key, window)
        return (current <= max_requests, current)
    
    async def get_rate_limit_remaining(
        self, 
        key: str, 
        max_requests: int
    ) -> int:
        """
        Get remaining requests before rate limit.
        
        Args:
            key: Rate limit key
            max_requests: Maximum requests allowed
            
        Returns:
            Number of remaining requests
        """
        current = await self.get_int(key, 0)
        return max(0, max_requests - current)
