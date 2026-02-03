"""
Analytics Repository

Handles analytics, audit logs, and statistics.
"""

import time
from typing import Dict, List, Optional, Any
from zyrax.database.repositories.base import BaseRepository


class AnalyticsRepository(BaseRepository):
    """Repository for analytics and logging operations."""
    
    collection_name = "analytics"
    
    # =========================================================================
    # Activity Tracking
    # =========================================================================
    
    async def track_activity(self, user_id: int, chat_id: int) -> None:
        """
        Track user activity in a chat.
        
        Updates hourly and daily buckets for analytics.
        """
        current_time = time.time()
        hour_key = time.strftime("%Y-%m-%d-%H")
        day_key = time.strftime("%Y-%m-%d")
        
        # Update hourly stats
        await self.collection.update_one(
            {"key": hour_key, "type": "hourly"},
            {"$inc": {"count": 1}},
            upsert=True
        )
        
        # Update daily stats
        await self.collection.update_one(
            {"key": day_key, "type": "daily"},
            {"$inc": {"count": 1}},
            upsert=True
        )
    
    async def get_activity_stats(self) -> Dict[str, List[Dict]]:
        """
        Get activity statistics.
        
        Returns:
            Dict with 'daily' and 'hourly' activity data
        """
        # Get last 7 days
        daily_cursor = self.collection.find(
            {"type": "daily"}
        ).sort("key", -1).limit(7)
        daily_data = [doc async for doc in daily_cursor]
        
        # Get last 24 hours
        hourly_cursor = self.collection.find(
            {"type": "hourly"}
        ).sort("key", -1).limit(24)
        hourly_data = [doc async for doc in hourly_cursor]
        
        return {
            "daily": sorted(daily_data, key=lambda x: x["key"]),
            "hourly": sorted(hourly_data, key=lambda x: x["key"])
        }
    
    # =========================================================================
    # Audit Logging
    # =========================================================================
    
    async def log_admin_action(
        self,
        action: str,
        user_id: int,
        chat_id: int,
        target_id: Optional[int] = None,
        details: Optional[str] = None
    ) -> None:
        """
        Log an admin action.
        
        Args:
            action: Action type (ban, kick, warn, etc.)
            user_id: Admin who performed the action
            chat_id: Chat where action occurred
            target_id: Target user (optional)
            details: Additional details (optional)
        """
        logs_collection = self.db["audit_logs"]
        await logs_collection.insert_one({
            "action": action,
            "user_id": user_id,
            "chat_id": chat_id,
            "target_id": target_id,
            "details": details,
            "timestamp": time.time()
        })
    
    async def get_audit_logs(
        self, 
        limit: int = 50,
        chat_id: int = None
    ) -> List[Dict]:
        """
        Get recent audit logs.
        
        Args:
            limit: Maximum logs to return
            chat_id: Filter by chat (optional)
            
        Returns:
            List of audit log entries
        """
        logs_collection = self.db["audit_logs"]
        query = {}
        if chat_id:
            query["chat_id"] = chat_id
        
        cursor = logs_collection.find(query).sort("timestamp", -1).limit(limit)
        return [doc async for doc in cursor]
    
    # =========================================================================
    # Bot Statistics
    # =========================================================================
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get overall bot statistics.
        
        Returns:
            Dict with user count, chat count, and today's commands
        """
        users_collection = self.db["users"]
        chats_collection = self.db["chats"]
        
        user_count = await users_collection.count_documents({})
        chat_count = await chats_collection.count_documents({})
        
        # Get today's commands from Redis via cache
        today = time.strftime("%Y-%m-%d")
        cmd_count = await self.cache.get_int(f"stats:commands:{today}", 0)
        
        return {
            "users": user_count,
            "chats": chat_count,
            "commands_today": cmd_count
        }
    
    async def track_command(self) -> None:
        """Track a command execution for statistics."""
        today = time.strftime("%Y-%m-%d")
        await self.cache.incr(f"stats:commands:{today}")
    
    # =========================================================================
    # Chat Registration
    # =========================================================================
    
    async def register_chat(self, chat_id: int, title: Optional[str] = None) -> None:
        """Register or update a chat."""
        chats_collection = self.db["chats"]
        await chats_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"title": title, "last_active": time.time()}},
            upsert=True
        )
    
    async def track_chat_activity(self, chat_id: int) -> None:
        """Update chat activity."""
        chats_collection = self.db["chats"]
        await chats_collection.update_one(
            {"chat_id": chat_id},
            {
                "$inc": {"msg_count": 1},
                "$set": {"last_active": time.time()}
            },
            upsert=True
        )
    
    # =========================================================================
    # Export
    # =========================================================================
    
    async def export_chat_analytics(self, chat_id: int) -> Dict[str, Any]:
        """
        Export chat analytics as JSON-serializable dict.
        
        Args:
            chat_id: Chat ID
            
        Returns:
            Dict with daily activity and audit logs
        """
        # Get analytics data
        daily_cursor = self.collection.find(
            {"type": "daily"}
        ).sort("key", -1).limit(30)
        daily = [
            {"date": d["key"], "messages": d["count"]} 
            async for d in daily_cursor
        ]
        
        # Get logs
        logs_collection = self.db["audit_logs"]
        log_cursor = logs_collection.find(
            {"chat_id": chat_id}
        ).sort("timestamp", -1).limit(100)
        
        audit_logs = []
        async for log in log_cursor:
            audit_logs.append({
                "action": log["action"],
                "user_id": log.get("user_id"),
                "target_id": log.get("target_id"),
                "details": log.get("details"),
                "timestamp": log["timestamp"]
            })
        
        return {
            "chat_id": chat_id,
            "daily_activity": daily,
            "audit_logs": audit_logs
        }
