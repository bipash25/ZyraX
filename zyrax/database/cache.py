import json
import redis.asyncio as redis
from typing import Optional, Any

class Cache:
    def __init__(self, r: redis.Redis):
        self.redis = r

    async def get(self, key: str) -> Optional[Any]:
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, value: Any, ttl: int = 300):
        await self.redis.setex(key, ttl, json.dumps(value))

    async def delete(self, key: str):
        await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        return await self.redis.exists(key) > 0

    async def incr(self, key: str) -> int:
        """Increment a counter and return new value"""
        return await self.redis.incr(key)

    async def incr_with_ttl(self, key: str, ttl: int = 30) -> int:
        """Increment a counter with TTL (for rate limiting)"""
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, ttl)
        results = await pipe.execute()
        return results[0]

    async def get_int(self, key: str) -> int:
        """Get an integer value"""
        data = await self.redis.get(key)
        return int(data) if data else 0

    async def setex(self, key: str, ttl: int, value: Any):
        """Set with expiration (raw value)"""
        await self.redis.setex(key, ttl, str(value))
