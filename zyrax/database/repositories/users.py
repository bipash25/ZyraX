"""
User Repository

Handles all user-related database operations.
"""

import time
from typing import Optional, Dict, List, Any
from zyrax.database.repositories.base import BaseRepository
from zyrax.constants import Limits


class UserRepository(BaseRepository):
    """Repository for user data operations."""
    
    collection_name = "users"
    
    async def register(self, user_id: int, username: Optional[str] = None) -> None:
        """
        Register or update a user.
        
        Args:
            user_id: Telegram user ID
            username: Telegram username (optional)
        """
        await self.collection.update_one(
            {"user_id": user_id},
            {
                "$set": {"username": username, "last_seen": time.time()},
                "$setOnInsert": {
                    "xp": 0, 
                    "level": 1, 
                    "balance": 0, 
                    "inventory": [], 
                    "title": None,
                    "karma": 0,
                    "language": "en",
                    "created_at": time.time()
                }
            },
            upsert=True
        )
    
    async def get(self, user_id: int) -> Optional[Dict]:
        """
        Get user data with caching.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            User document or None
        """
        cache_key = self._cache_key(user_id)
        cached = await self._get_cached(cache_key)
        if cached:
            return cached
        
        doc = await self.find_one({"user_id": user_id})
        if doc:
            serialized = self._serialize_doc(doc)
            await self._set_cached(cache_key, serialized, Limits.USER_DATA_CACHE_TTL)
            return serialized
        return None
    
    async def add_xp(self, user_id: int, amount: int) -> None:
        """Add XP to a user."""
        await self.collection.update_one(
            {"user_id": user_id},
            {"$inc": {"xp": amount}},
            upsert=True
        )
        await self._invalidate_cache(self._cache_key(user_id))
    
    async def update_level(self, user_id: int, new_level: int) -> None:
        """Update user's level."""
        await self.collection.update_one(
            {"user_id": user_id},
            {"$set": {"level": new_level}}
        )
        await self._invalidate_cache(self._cache_key(user_id))
    
    async def add_balance(self, user_id: int, amount: int) -> None:
        """Add (or subtract) from user's balance."""
        await self.collection.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": amount}},
            upsert=True
        )
        await self._invalidate_cache(self._cache_key(user_id))
    
    async def get_balance(self, user_id: int) -> int:
        """Get user's current balance."""
        doc = await self.get(user_id)
        return doc.get("balance", 0) if doc else 0
    
    async def get_top_users(
        self, 
        limit: int = 10, 
        sort_by: str = "xp"
    ) -> List[Dict]:
        """Get top users sorted by a field."""
        return await self.find_many({}, limit=limit, sort_by=sort_by, sort_order=-1)
    
    async def add_inventory_item(self, user_id: int, item_id: str) -> None:
        """Add an item to user's inventory."""
        await self.collection.update_one(
            {"user_id": user_id},
            {"$addToSet": {"inventory": item_id}}
        )
        await self._invalidate_cache(self._cache_key(user_id))
    
    async def set_title(self, user_id: int, title: str) -> None:
        """Set user's custom title."""
        await self.collection.update_one(
            {"user_id": user_id},
            {"$set": {"title": title}}
        )
        await self._invalidate_cache(self._cache_key(user_id))
    
    async def change_karma(self, user_id: int, amount: int) -> int:
        """Change user's karma and return new value."""
        await self.collection.update_one(
            {"user_id": user_id},
            {"$inc": {"karma": amount}},
            upsert=True
        )
        await self._invalidate_cache(self._cache_key(user_id))
        
        doc = await self.find_one({"user_id": user_id})
        return doc.get("karma", 0) if doc else 0
    
    async def get_karma(self, user_id: int) -> int:
        """Get user's current karma."""
        doc = await self.get(user_id)
        return doc.get("karma", 0) if doc else 0
    
    async def set_language(self, user_id: int, lang: str) -> None:
        """Set user's preferred language."""
        await self.collection.update_one(
            {"user_id": user_id},
            {"$set": {"language": lang}},
            upsert=True
        )
        await self._invalidate_cache(self._cache_key(user_id))
    
    async def get_language(self, user_id: int) -> str:
        """Get user's preferred language."""
        doc = await self.get(user_id)
        return doc.get("language", "en") if doc else "en"
    
    async def update_game_stats(
        self, 
        user_id: int, 
        game: str, 
        won: bool
    ) -> None:
        """Update game statistics for a user."""
        field = f"games.{game}"
        await self.collection.update_one(
            {"user_id": user_id},
            {
                "$inc": {
                    f"{field}.played": 1,
                    f"{field}.won": 1 if won else 0
                }
            },
            upsert=True
        )
        await self._invalidate_cache(self._cache_key(user_id))
    
    async def get_game_leaderboard(
        self, 
        game: str, 
        limit: int = 10
    ) -> List[Dict]:
        """Get game leaderboard."""
        cursor = self.collection.find(
            {f"games.{game}.won": {"$exists": True}}
        ).sort(f"games.{game}.won", -1).limit(limit)
        return [doc async for doc in cursor]
    
    async def get_full_data(self, user_id: int) -> Dict[str, Any]:
        """Get all data for a user (for GDPR export)."""
        return {
            "profile": await self.get(user_id)
        }
    
    async def delete_user_data(self, user_id: int) -> None:
        """Delete all data for a user (for GDPR)."""
        await self.delete_one({"user_id": user_id})
        await self._invalidate_cache(self._cache_key(user_id))
    
    async def track_activity(self, user_id: int) -> None:
        """Update user's last activity timestamp."""
        await self.collection.update_one(
            {"user_id": user_id},
            {
                "$inc": {"msg_count": 1},
                "$set": {"last_active": time.time()}
            },
            upsert=True
        )
