"""
Filter Repository

Handles filter/trigger storage and retrieval.
"""

import time
from typing import Optional, Dict, List
from zyrax.database.repositories.base import BaseRepository


class FilterRepository(BaseRepository):
    """Repository for filter operations."""
    
    collection_name = "filters"
    
    async def save(self, chat_id: int, name: str, data: Dict) -> None:
        """
        Save or update a filter.
        
        Args:
            chat_id: Chat ID
            name: Filter trigger (keyword or regex pattern)
            data: Filter data (content, type, is_regex, etc.)
        """
        await self.collection.update_one(
            {"chat_id": chat_id, "name": name},
            {"$set": {"data": data}},
            upsert=True
        )
    
    async def get(self, chat_id: int, name: str) -> Optional[Dict]:
        """
        Get a specific filter.
        
        Args:
            chat_id: Chat ID
            name: Filter trigger
            
        Returns:
            Filter document or None
        """
        return await self.find_one({"chat_id": chat_id, "name": name})
    
    async def delete(self, chat_id: int, name: str) -> bool:
        """
        Delete a filter.
        
        Args:
            chat_id: Chat ID
            name: Filter trigger
            
        Returns:
            True if filter was deleted
        """
        return await self.delete_one({"chat_id": chat_id, "name": name})
    
    async def get_all(self, chat_id: int) -> Dict[str, Dict]:
        """
        Get all filters for a chat.
        
        Args:
            chat_id: Chat ID
            
        Returns:
            Dict mapping filter names to their data
        """
        cursor = self.collection.find({"chat_id": chat_id})
        return {doc["name"]: doc["data"] async for doc in cursor}
    
    async def increment_stats(self, chat_id: int, filter_name: str) -> None:
        """
        Increment filter hit statistics.
        
        Args:
            chat_id: Chat ID
            filter_name: Filter that was triggered
        """
        stats_collection = self.db["filter_stats"]
        await stats_collection.update_one(
            {"chat_id": chat_id, "filter": filter_name},
            {"$inc": {"hits": 1}, "$set": {"last_hit": time.time()}},
            upsert=True
        )
    
    async def get_stats(self, chat_id: int) -> List[Dict]:
        """
        Get filter statistics for a chat.
        
        Args:
            chat_id: Chat ID
            
        Returns:
            List of filter stats sorted by hits
        """
        stats_collection = self.db["filter_stats"]
        cursor = stats_collection.find(
            {"chat_id": chat_id}
        ).sort("hits", -1)
        return [doc async for doc in cursor]
