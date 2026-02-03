"""
Warning Repository

Handles all warning-related database operations.
"""

import time
from typing import Optional, Dict, List
from zyrax.database.repositories.base import BaseRepository
from zyrax.constants import Limits


class WarningRepository(BaseRepository):
    """Repository for warning operations."""
    
    collection_name = "warnings"
    
    async def add(
        self, 
        chat_id: int, 
        user_id: int, 
        reason: str = "No reason"
    ) -> int:
        """
        Add a warning to a user.
        
        Args:
            chat_id: Chat ID
            user_id: User ID
            reason: Reason for warning
            
        Returns:
            New warning count
        """
        await self.collection.update_one(
            {"chat_id": chat_id, "user_id": user_id},
            {
                "$push": {"warns": {"reason": reason, "date": time.time()}},
                "$inc": {"count": 1}
            },
            upsert=True
        )
        
        doc = await self.find_one({"chat_id": chat_id, "user_id": user_id})
        return doc["count"] if doc else 1
    
    async def remove(self, chat_id: int, user_id: int) -> int:
        """
        Remove one warning from a user.
        
        Args:
            chat_id: Chat ID
            user_id: User ID
            
        Returns:
            New warning count
        """
        doc = await self.find_one({"chat_id": chat_id, "user_id": user_id})
        
        if doc and doc.get("count", 0) > 0:
            await self.collection.update_one(
                {"chat_id": chat_id, "user_id": user_id},
                {
                    "$pop": {"warns": -1},
                    "$inc": {"count": -1}
                }
            )
            return doc["count"] - 1
        return 0
    
    async def get(self, chat_id: int, user_id: int) -> Optional[Dict]:
        """
        Get warning data for a user.
        
        Args:
            chat_id: Chat ID
            user_id: User ID
            
        Returns:
            Warning document or None
        """
        return await self.find_one({"chat_id": chat_id, "user_id": user_id})
    
    async def get_count(self, chat_id: int, user_id: int) -> int:
        """Get warning count for a user."""
        doc = await self.get(chat_id, user_id)
        return doc.get("count", 0) if doc else 0
    
    async def reset(self, chat_id: int, user_id: int) -> None:
        """Reset all warnings for a user."""
        await self.delete_one({"chat_id": chat_id, "user_id": user_id})
    
    async def get_all_for_user(self, user_id: int) -> List[Dict]:
        """Get all warnings for a user across all chats."""
        return await self.find_many({"user_id": user_id})
    
    async def delete_all_for_user(self, user_id: int) -> int:
        """Delete all warnings for a user (GDPR)."""
        return await self.delete_many({"user_id": user_id})
