"""
Note Repository

Handles note storage and retrieval.
"""

from typing import Optional, Dict, List
from zyrax.database.repositories.base import BaseRepository
from zyrax.constants import Limits


class NoteRepository(BaseRepository):
    """Repository for note operations."""
    
    collection_name = "notes"
    
    async def save(self, chat_id: int, name: str, data: Dict) -> None:
        """
        Save or update a note.
        
        Args:
            chat_id: Chat ID
            name: Note name (lowercase)
            data: Note data (content, type, media_id, etc.)
        """
        name = name.lower()
        await self.collection.update_one(
            {"chat_id": chat_id, "name": name},
            {"$set": {"data": data}},
            upsert=True
        )
        await self._invalidate_cache(self._cache_key(chat_id, name))
    
    async def get(self, chat_id: int, name: str) -> Optional[Dict]:
        """
        Get a note with caching.
        
        Args:
            chat_id: Chat ID
            name: Note name
            
        Returns:
            Note document or None
        """
        name = name.lower()
        cache_key = self._cache_key(chat_id, name)
        
        cached = await self._get_cached(cache_key)
        if cached:
            return cached
        
        doc = await self.find_one({"chat_id": chat_id, "name": name})
        
        if doc:
            serialized = self._serialize_doc(doc)
            await self._set_cached(cache_key, serialized, Limits.NOTE_CACHE_TTL)
            return serialized
        return None
    
    async def delete(self, chat_id: int, name: str) -> bool:
        """
        Delete a note.
        
        Args:
            chat_id: Chat ID
            name: Note name
            
        Returns:
            True if note was deleted
        """
        name = name.lower()
        result = await self.delete_one({"chat_id": chat_id, "name": name})
        if result:
            await self._invalidate_cache(self._cache_key(chat_id, name))
        return result
    
    async def get_all_names(self, chat_id: int) -> List[str]:
        """
        Get all note names for a chat.
        
        Args:
            chat_id: Chat ID
            
        Returns:
            List of note names
        """
        cursor = self.collection.find(
            {"chat_id": chat_id},
            {"name": 1, "_id": 0}
        )
        return [doc["name"] async for doc in cursor]
    
    async def count_for_chat(self, chat_id: int) -> int:
        """Get the number of notes in a chat."""
        return await self.count({"chat_id": chat_id})
