"""
Cache management system
Supports both in-memory (LRU) and Redis caching
"""
import logging
import json
from typing import Optional, Any, Dict
from datetime import timedelta
from utils.time_parser import now_utc
from collections import OrderedDict

logger = logging.getLogger(__name__)

# Optional Redis support
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis package not installed, falling back to memory cache only")


class LRUCache:
    """Simple LRU (Least Recently Used) cache implementation"""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize LRU cache
        
        Args:
            max_size: Maximum number of items to cache
        """
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size
        self.ttl_map: Dict[str, datetime] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        # Check if key exists
        if key not in self.cache:
            return None
        
        # Check TTL
        if key in self.ttl_map:
            if now_utc() > self.ttl_map[key]:
                # Expired
                del self.cache[key]
                del self.ttl_map[key]
                return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
        """
        # Update or add
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            self.cache[key] = value
            
            # Remove oldest if at capacity
            if len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                if oldest_key in self.ttl_map:
                    del self.ttl_map[oldest_key]
        
        self.cache[key] = value
        
        # Set TTL
        if ttl:
            self.ttl_map[key] = now_utc() + timedelta(seconds=ttl)
    
    def delete(self, key: str) -> None:
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
        if key in self.ttl_map:
            del self.ttl_map[key]
    
    def clear(self) -> None:
        """Clear all cached items"""
        self.cache.clear()
        self.ttl_map.clear()
    
    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)


class CacheManager:
    """
    Unified cache manager supporting both memory and Redis
    Falls back to memory cache if Redis is unavailable
    """
    
    def __init__(
        self,
        redis_enabled: bool = False,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        memory_cache_size: int = 1000
    ):
        """
        Initialize cache manager
        
        Args:
            redis_enabled: Whether to use Redis
            redis_host: Redis host
            redis_port: Redis port
            redis_db: Redis database number
            redis_password: Redis password (optional)
            memory_cache_size: Size of memory cache
        """
        self.redis_enabled = redis_enabled and REDIS_AVAILABLE
        self.redis_client: Optional[aioredis.Redis] = None
        self.memory_cache = LRUCache(max_size=memory_cache_size)
        
        # Redis connection params
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.redis_password = redis_password
    
    async def initialize(self) -> None:
        """Initialize cache system"""
        if self.redis_enabled:
            try:
                self.redis_client = await aioredis.from_url(
                    f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}",
                    password=self.redis_password,
                    encoding="utf-8",
                    decode_responses=True
                )
                
                # Test connection
                await self.redis_client.ping()
                logger.info(f"✓ Redis cache connected at {self.redis_host}:{self.redis_port}")
                
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using memory cache only.")
                self.redis_enabled = False
                self.redis_client = None
        else:
            logger.info("✓ Using in-memory cache (Redis disabled)")
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        # Try Redis first if enabled
        if self.redis_enabled and self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value:
                    # Try to parse JSON
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        return value
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        # Fall back to memory cache
        value = self.memory_cache.get(key)
        return value if value is not None else default
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
        """
        # Set in Redis if enabled
        if self.redis_enabled and self.redis_client:
            try:
                # Serialize complex objects to JSON
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                
                if ttl:
                    await self.redis_client.setex(key, ttl, value)
                else:
                    await self.redis_client.set(key, value)
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        
        # Always set in memory cache as backup
        self.memory_cache.set(key, value, ttl)
    
    async def delete(self, key: str) -> None:
        """Delete key from cache"""
        if self.redis_enabled and self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
        
        self.memory_cache.delete(key)
    
    async def clear(self) -> None:
        """Clear all cached items"""
        if self.redis_enabled and self.redis_client:
            try:
                await self.redis_client.flushdb()
            except Exception as e:
                logger.error(f"Redis clear error: {e}")
        
        self.memory_cache.clear()
    
    async def close(self) -> None:
        """Close cache connections"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("✓ Redis connection closed")