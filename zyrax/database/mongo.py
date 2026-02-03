"""
MongoDB Database Facade

This module provides backward compatibility while using the new repository pattern.
All existing code importing `db` from this module will continue to work.

New code should import repositories directly from `zyrax.database.repositories`.
"""

from __future__ import annotations

import time
from typing import List, Optional, Dict, Any, TYPE_CHECKING

from pydantic import BaseModel, Field

from zyrax.database.connection import connection
from zyrax.database.cache import Cache
from zyrax.database.repositories import (
    UserRepository,
    WarningRepository,
    SettingsRepository,
    NoteRepository,
    FilterRepository,
    AnalyticsRepository,
)


# Pydantic models for validation (kept for backward compatibility)
class WarnDocument(BaseModel):
    user_id: int
    chat_id: int
    count: int = Field(default=0, ge=0)
    warns: List[dict] = []


class FederationDocument(BaseModel):
    fed_id: str
    name: str = Field(min_length=3)
    owner_id: int
    chats: List[int] = []


class MongoDB:
    """
    MongoDB facade that provides backward compatibility.
    
    This class delegates to specialized repositories while maintaining
    the same interface that existing code expects.
    
    Usage:
        from zyrax.database.mongo import db
        await db.initialize()
        await db.add_warn(chat_id, user_id, reason)
    
    New code should prefer:
        from zyrax.database import warnings
        await warnings.add(chat_id, user_id, reason)
    """
    
    # Type hints for initialized repositories
    _users: UserRepository
    _warnings: WarningRepository
    _settings: SettingsRepository
    _notes: NoteRepository
    _filters: FilterRepository
    _analytics: AnalyticsRepository
    _cache: Cache
    
    def __init__(self) -> None:
        self._initialized = False

    def _check_initialized(self) -> None:
        """Raise if database not initialized."""
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize() first.")

    async def initialize(self) -> None:
        """Initialize database connections and repositories."""
        if self._initialized:
            return
        
        # Initialize connection
        await connection.initialize()
        
        # Create cache wrapper
        self._cache = Cache(connection.redis_client)
        
        # Initialize repositories
        database = connection.database
        self._users = UserRepository(database, self._cache)
        self._warnings = WarningRepository(database, self._cache)
        self._settings = SettingsRepository(database, self._cache)
        self._notes = NoteRepository(database, self._cache)
        self._filters = FilterRepository(database, self._cache)
        self._analytics = AnalyticsRepository(database, self._cache)
        
        self._initialized = True
        print("Database initialized with repository pattern.")

    @property
    def client(self) -> Any:
        """Get MongoDB client (backward compat)."""
        return connection._mongo_client
    
    @property
    def db(self) -> Any:
        """Get MongoDB database (backward compat)."""
        return connection.database
    
    @property
    def redis(self) -> Any:
        """Get Redis client (backward compat)."""
        return connection.redis_client
    
    @property
    def cache(self) -> Cache:
        """Get cache wrapper."""
        if self._cache is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._cache
    
    # =========================================================================
    # Repository accessors (for new code)
    # =========================================================================
    
    @property
    def users(self) -> UserRepository:
        """Get user repository."""
        self._check_initialized()
        assert self._users is not None
        return self._users
    
    @property
    def warnings(self) -> WarningRepository:
        """Get warning repository."""
        self._check_initialized()
        assert self._warnings is not None
        return self._warnings
    
    @property
    def settings(self) -> SettingsRepository:
        """Get settings repository."""
        self._check_initialized()
        assert self._settings is not None
        return self._settings
    
    @property
    def notes(self) -> NoteRepository:
        """Get notes repository."""
        self._check_initialized()
        assert self._notes is not None
        return self._notes
    
    @property
    def filters(self) -> FilterRepository:
        """Get filters repository."""
        self._check_initialized()
        assert self._filters is not None
        return self._filters
    
    @property
    def analytics(self) -> AnalyticsRepository:
        """Get analytics repository."""
        self._check_initialized()
        assert self._analytics is not None
        return self._analytics

    async def get_collection(self, name: str) -> Any:
        """Get a collection by name (backward compat)."""
        return self.db[name]

    async def close(self) -> None:
        """Close all database connections."""
        await connection.close()
        self._initialized = False

    async def health_check(self) -> dict:
        """Check database health."""
        return await connection.health_check()

    # =========================================================================
    # Warning Methods (delegate to WarningRepository)
    # =========================================================================

    async def add_warn(self, chat_id: int, user_id: int, reason: Optional[str] = None) -> int:
        """Add a warning. Returns new count."""
        return await self.warnings.add(chat_id, user_id, reason or "No reason")

    async def remove_warn(self, chat_id: int, user_id: int) -> int:
        """Remove one warning. Returns new count."""
        return await self.warnings.remove(chat_id, user_id)

    async def get_warns(self, chat_id: int, user_id: int) -> Optional[Dict]:
        """Get warning data for a user."""
        return await self.warnings.get(chat_id, user_id)

    async def reset_warns(self, chat_id: int, user_id: int) -> None:
        """Reset all warnings for a user."""
        await self.warnings.reset(chat_id, user_id)

    # =========================================================================
    # Notes Methods (delegate to NoteRepository)
    # =========================================================================

    async def save_note(self, chat_id: int, name: str, data: dict) -> None:
        """Save a note."""
        await self.notes.save(chat_id, name, data)

    async def get_note(self, chat_id: int, name: str) -> Optional[Dict]:
        """Get a note."""
        return await self.notes.get(chat_id, name)

    async def delete_note(self, chat_id: int, name: str) -> bool:
        """Delete a note."""
        return await self.notes.delete(chat_id, name)

    async def get_all_notes(self, chat_id: int) -> List[str]:
        """Get all note names for a chat."""
        return await self.notes.get_all_names(chat_id)

    # =========================================================================
    # Filter Methods (delegate to FilterRepository)
    # =========================================================================

    async def save_filter(self, chat_id: int, name: str, data: dict) -> None:
        """Save a filter."""
        await self.filters.save(chat_id, name, data)

    async def get_filter(self, chat_id: int, name: str) -> Optional[Dict]:
        """Get a filter."""
        return await self.filters.get(chat_id, name)

    async def delete_filter(self, chat_id: int, name: str) -> bool:
        """Delete a filter."""
        return await self.filters.delete(chat_id, name)

    async def get_chat_filters(self, chat_id: int) -> Dict[str, Dict]:
        """Get all filters for a chat."""
        return await self.filters.get_all(chat_id)

    async def increment_filter_stats(self, chat_id: int, filter_name: str) -> None:
        """Increment filter hit statistics."""
        await self.filters.increment_stats(chat_id, filter_name)

    async def get_filter_stats(self, chat_id: int) -> List[Dict]:
        """Get filter statistics for a chat."""
        return await self.filters.get_stats(chat_id)

    # =========================================================================
    # Settings Methods (delegate to SettingsRepository)
    # =========================================================================

    async def set_flood(self, chat_id: int, limit: int) -> None:
        """Set flood limit for a chat."""
        await self.settings.set_flood_limit(chat_id, limit)

    async def get_flood_limit(self, chat_id: int) -> int:
        """Get flood limit for a chat."""
        return await self.settings.get_flood_limit(chat_id)

    async def set_rules(self, chat_id: int, rules: str) -> None:
        """Set chat rules."""
        await self.settings.set_rules(chat_id, rules)

    async def get_rules(self, chat_id: int) -> Optional[str]:
        """Get chat rules."""
        return await self.settings.get_rules(chat_id)

    async def set_captcha(
        self, 
        chat_id: int, 
        enabled: Optional[bool] = None, 
        mode: Optional[str] = None
    ) -> None:
        """Set captcha settings."""
        await self.settings.set_captcha(chat_id, enabled, mode)

    async def get_captcha_settings(self, chat_id: int) -> Dict:
        """Get captcha settings."""
        return await self.settings.get_captcha_settings(chat_id)

    async def get_chat_settings(self, chat_id: int) -> Dict:
        """Get all settings for a chat."""
        return await self.settings.get(chat_id)

    async def set_antispam_setting(self, chat_id: int, key: str, value: Any) -> None:
        """Set an anti-spam setting."""
        await self.settings.set_antispam(chat_id, key, value)

    async def get_antispam_settings(self, chat_id: int) -> Dict:
        """Get anti-spam settings."""
        return await self.settings.get_antispam_settings(chat_id)

    async def set_raid_mode(self, chat_id: int, enabled: bool, expires: float) -> None:
        """Set raid mode."""
        await self.settings.set_raid_mode(chat_id, enabled, expires)

    async def get_raid_mode(self, chat_id: int) -> Dict:
        """Get raid mode settings."""
        return await self.settings.get_raid_mode(chat_id)

    async def add_whitelist_domain(self, chat_id: int, domain: str) -> None:
        """Add a domain to the whitelist."""
        await self.settings.add_whitelist_domain(chat_id, domain)

    async def remove_whitelist_domain(self, chat_id: int, domain: str) -> None:
        """Remove a domain from the whitelist."""
        await self.settings.remove_whitelist_domain(chat_id, domain)

    async def get_whitelist_domains(self, chat_id: int) -> List[str]:
        """Get whitelisted domains."""
        return await self.settings.get_whitelist_domains(chat_id)

    async def add_rss(self, chat_id: int, url: str) -> None:
        """Add an RSS feed."""
        await self.settings.add_rss(chat_id, url)

    async def get_chat_rss(self, chat_id: int) -> List[str]:
        """Get RSS feeds for a chat."""
        return await self.settings.get_rss_feeds(chat_id)

    async def remove_rss(self, chat_id: int, url: str) -> None:
        """Remove an RSS feed."""
        await self.settings.remove_rss(chat_id, url)

    async def set_aimod(self, chat_id: int, enabled: bool) -> None:
        """Enable/disable AI moderation."""
        await self.settings.set_aimod(chat_id, enabled)

    async def set_aimod_sensitivity(self, chat_id: int, level: str) -> None:
        """Set AI moderation sensitivity."""
        await self.settings.set_aimod_sensitivity(chat_id, level)

    async def get_aimod_settings(self, chat_id: int) -> Dict:
        """Get AI moderation settings."""
        return await self.settings.get_aimod_settings(chat_id)

    async def set_chat_language(self, chat_id: int, lang: str) -> None:
        """Set chat language."""
        await self.settings.set_language(chat_id, lang)

    async def get_chat_language(self, chat_id: int) -> str:
        """Get chat language."""
        return await self.settings.get_language(chat_id)

    # =========================================================================
    # User Methods (delegate to UserRepository)
    # =========================================================================

    async def register_user(self, user_id: int, username: Optional[str] = None) -> None:
        """Register or update a user."""
        await self.users.register(user_id, username)

    async def get_user_data(self, user_id: int) -> Optional[Dict]:
        """Get user data."""
        return await self.users.get(user_id)

    async def add_xp(self, user_id: int, amount: int) -> None:
        """Add XP to a user."""
        await self.users.add_xp(user_id, amount)

    async def update_level(self, user_id: int, new_level: int) -> None:
        """Update user's level."""
        await self.users.update_level(user_id, new_level)

    async def add_balance(self, user_id: int, amount: int) -> None:
        """Add balance to a user."""
        await self.users.add_balance(user_id, amount)

    async def get_top_users(self, limit: int = 10, sort_by: str = "xp") -> List[Dict]:
        """Get top users."""
        return await self.users.get_top_users(limit, sort_by)

    async def add_inventory_item(self, user_id: int, item_id: str) -> None:
        """Add an item to user's inventory."""
        await self.users.add_inventory_item(user_id, item_id)

    async def set_title(self, user_id: int, title: str) -> None:
        """Set user's custom title."""
        await self.users.set_title(user_id, title)

    async def change_karma(self, user_id: int, amount: int) -> int:
        """Change user's karma."""
        return await self.users.change_karma(user_id, amount)

    async def get_karma(self, user_id: int) -> int:
        """Get user's karma."""
        return await self.users.get_karma(user_id)

    async def set_user_language(self, user_id: int, lang: str) -> None:
        """Set user's language preference."""
        await self.users.set_language(user_id, lang)

    async def get_user_language(self, user_id: int) -> str:
        """Get user's language preference."""
        return await self.users.get_language(user_id)

    async def update_game_stats(self, user_id: int, game: str, won: bool) -> None:
        """Update game statistics for a user."""
        await self.users.update_game_stats(user_id, game, won)

    async def get_game_leaderboard(self, game: str, limit: int = 10) -> List[Dict]:
        """Get game leaderboard."""
        return await self.users.get_game_leaderboard(game, limit)

    async def get_user_full_data(self, user_id: int) -> Dict:
        """Get all data for a user (GDPR export)."""
        data = await self.users.get_full_data(user_id)
        # Include warnings
        data["warnings"] = await self.warnings.get_all_for_user(user_id)
        return data

    async def delete_user_data(self, user_id: int) -> None:
        """Delete all data for a user (GDPR)."""
        await self.users.delete_user_data(user_id)
        await self.warnings.delete_all_for_user(user_id)

    # =========================================================================
    # Analytics Methods (delegate to AnalyticsRepository)
    # =========================================================================

    async def register_chat(self, chat_id: int, title: Optional[str] = None) -> None:
        """Register or update a chat."""
        await self.analytics.register_chat(chat_id, title)

    async def get_stats(self) -> Dict:
        """Get overall bot statistics."""
        return await self.analytics.get_stats()

    async def track_command_usage(self) -> None:
        """Track a command execution."""
        await self.analytics.track_command()

    async def track_activity(self, user_id: int, chat_id: int) -> None:
        """Track user activity in a chat."""
        await self.users.track_activity(user_id)
        await self.analytics.track_chat_activity(chat_id)
        await self.analytics.track_activity(user_id, chat_id)

    async def log_admin_action(
        self, 
        action: str, 
        user_id: int, 
        chat_id: int, 
        target_id: Optional[int] = None, 
        details: Optional[str] = None
    ) -> None:
        """Log an admin action."""
        await self.analytics.log_admin_action(action, user_id, chat_id, target_id, details)

    async def get_audit_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent audit logs."""
        return await self.analytics.get_audit_logs(limit)

    async def get_activity_stats(self) -> Dict:
        """Get activity statistics."""
        return await self.analytics.get_activity_stats()

    async def export_chat_analytics(self, chat_id: int) -> Dict:
        """Export chat analytics."""
        return await self.analytics.export_chat_analytics(chat_id)

    # =========================================================================
    # Welcome/Goodbye (direct collection access for now)
    # =========================================================================

    async def set_welcome(
        self, 
        chat_id: int, 
        content: Optional[str] = None, 
        type: str = "text", 
        media_id: Optional[str] = None
    ) -> None:
        """Set welcome message."""
        welcomes = await self.get_collection("welcomes")
        data: Dict[str, Any] = {}
        if content:
            data["content"] = content
        if type:
            data["type"] = type
        if media_id:
            data["media_id"] = media_id
        
        await welcomes.update_one(
            {"chat_id": chat_id},
            {"$set": data},
            upsert=True
        )

    async def get_welcome(self, chat_id: int) -> Optional[Dict]:
        """Get welcome message."""
        welcomes = await self.get_collection("welcomes")
        return await welcomes.find_one({"chat_id": chat_id})

    async def delete_welcome(self, chat_id: int) -> None:
        """Delete welcome message."""
        welcomes = await self.get_collection("welcomes")
        await welcomes.delete_one({"chat_id": chat_id})

    async def set_goodbye(
        self, 
        chat_id: int, 
        content: Optional[str] = None, 
        media_id: Optional[str] = None, 
        media_type: Optional[str] = None
    ) -> None:
        """Set goodbye message."""
        goodbyes = await self.get_collection("goodbyes")
        data: Dict[str, Any] = {}
        if content:
            data["content"] = content
        if media_id:
            data["media_id"] = media_id
        if media_type:
            data["media_type"] = media_type
        
        await goodbyes.update_one(
            {"chat_id": chat_id},
            {"$set": data},
            upsert=True
        )

    async def get_goodbye(self, chat_id: int) -> Optional[Dict]:
        """Get goodbye message."""
        goodbyes = await self.get_collection("goodbyes")
        return await goodbyes.find_one({"chat_id": chat_id})

    async def delete_goodbye(self, chat_id: int) -> None:
        """Delete goodbye message."""
        goodbyes = await self.get_collection("goodbyes")
        await goodbyes.delete_one({"chat_id": chat_id})

    # =========================================================================
    # Blacklist (direct collection access)
    # =========================================================================

    async def add_blacklist(self, chat_id: int, word: str, action: str) -> None:
        """Add a word to blacklist."""
        blacklist = await self.get_collection("blacklist")
        await blacklist.update_one(
            {"chat_id": chat_id},
            {"$set": {f"words.{word}": action}},
            upsert=True
        )

    async def remove_blacklist(self, chat_id: int, word: str) -> None:
        """Remove a word from blacklist."""
        blacklist = await self.get_collection("blacklist")
        await blacklist.update_one(
            {"chat_id": chat_id},
            {"$unset": {f"words.{word}": ""}}
        )

    async def get_blacklist(self, chat_id: int) -> Dict:
        """Get blacklist for a chat."""
        blacklist = await self.get_collection("blacklist")
        doc = await blacklist.find_one({"chat_id": chat_id})
        return doc.get("words", {}) if doc else {}

    # =========================================================================
    # Federation (direct collection access)
    # =========================================================================

    async def create_fed(self, owner_id: int, name: str, fed_id: str) -> bool:
        """Create a federation."""
        feds = await self.get_collection("federations")
        if await feds.find_one({"name": name}):
            return False
        
        fed = FederationDocument(fed_id=fed_id, name=name, owner_id=owner_id)
        await feds.insert_one(fed.model_dump())
        return True

    async def get_fed(self, fed_id: str) -> Optional[Dict]:
        """Get a federation."""
        feds = await self.get_collection("federations")
        return await feds.find_one({"fed_id": fed_id})

    async def join_fed(self, fed_id: str, chat_id: int) -> bool:
        """Join a federation."""
        feds = await self.get_collection("federations")
        result = await feds.update_one(
            {"fed_id": fed_id},
            {"$addToSet": {"chats": chat_id}}
        )
        if result.modified_count > 0:
            await self.settings.set_federation(chat_id, fed_id)
            return True
        return False

    async def leave_fed(self, chat_id: int) -> bool:
        """Leave a federation."""
        fed_id = await self.settings.get_federation(chat_id)
        if not fed_id:
            return False
        
        feds = await self.get_collection("federations")
        await feds.update_one(
            {"fed_id": fed_id},
            {"$pull": {"chats": chat_id}}
        )
        await self.settings.leave_federation(chat_id)
        return True

    async def get_chat_fed_id(self, chat_id: int) -> Optional[str]:
        """Get federation ID for a chat."""
        return await self.settings.get_federation(chat_id)

    async def fed_ban(self, fed_id: str, user_id: int, reason: str) -> None:
        """Ban a user from federation."""
        bans = await self.get_collection("fed_bans")
        await bans.update_one(
            {"fed_id": fed_id, "user_id": user_id},
            {"$set": {"reason": reason, "date": time.time()}},
            upsert=True
        )

    async def fed_unban(self, fed_id: str, user_id: int) -> bool:
        """Unban a user from federation."""
        bans = await self.get_collection("fed_bans")
        result = await bans.delete_one({"fed_id": fed_id, "user_id": user_id})
        return result.deleted_count > 0

    async def is_user_fedor_banned(self, fed_id: str, user_id: int) -> Optional[Dict]:
        """Check if user is banned from federation."""
        bans = await self.get_collection("fed_bans")
        return await bans.find_one({"fed_id": fed_id, "user_id": user_id})

    # =========================================================================
    # Tournaments (direct collection access)
    # =========================================================================

    async def create_tournament(self, chat_id: int, name: str, size: int) -> bool:
        """Create a tournament."""
        tourneys = await self.get_collection("tournaments")
        if await tourneys.find_one({"chat_id": chat_id, "status": "active"}):
            return False
        
        await tourneys.insert_one({
            "chat_id": chat_id,
            "name": name,
            "size": size,
            "participants": [],
            "status": "registration",
            "round": 0,
            "matches": []
        })
        return True

    async def get_active_tournament(self, chat_id: int) -> Optional[Dict]:
        """Get active tournament for a chat."""
        tourneys = await self.get_collection("tournaments")
        return await tourneys.find_one({"chat_id": chat_id, "status": {"$ne": "completed"}})

    async def join_tournament(self, chat_id: int, user_id: int, user_name: str) -> str:
        """Join a tournament."""
        tourneys = await self.get_collection("tournaments")
        doc = await tourneys.find_one({"chat_id": chat_id, "status": "registration"})
        
        if not doc:
            return "no_tournament"
        if len(doc["participants"]) >= doc["size"]:
            return "full"
        if any(p["user_id"] == user_id for p in doc["participants"]):
            return "already_joined"
        
        await tourneys.update_one(
            {"_id": doc["_id"]},
            {"$push": {"participants": {"user_id": user_id, "name": user_name}}}
        )
        return "joined"

    async def start_tournament(self, chat_id: int) -> bool:
        """Start a tournament."""
        import random
        
        tourneys = await self.get_collection("tournaments")
        doc = await tourneys.find_one({"chat_id": chat_id, "status": "registration"})
        if not doc:
            return False
        
        participants = doc["participants"]
        random.shuffle(participants)
        
        matches = []
        for i in range(0, len(participants), 2):
            p1 = participants[i]
            p2 = participants[i+1] if i+1 < len(participants) else None
            matches.append({"p1": p1, "p2": p2, "winner": None})
        
        await tourneys.update_one(
            {"_id": doc["_id"]},
            {"$set": {"status": "active", "round": 1, "matches": matches}}
        )
        return True

    # =========================================================================
    # Reminders (direct collection access)
    # =========================================================================

    async def add_reminder(
        self, 
        user_id: int, 
        chat_id: int, 
        text: str, 
        remind_at: float
    ) -> None:
        """Add a reminder."""
        reminders = await self.get_collection("reminders")
        await reminders.insert_one({
            "user_id": user_id,
            "chat_id": chat_id,
            "text": text,
            "remind_at": remind_at,
            "created_at": time.time()
        })

    async def get_due_reminders(self, current_time: float) -> List[Dict]:
        """Get due reminders."""
        reminders = await self.get_collection("reminders")
        cursor = reminders.find({"remind_at": {"$lte": current_time}})
        return [doc async for doc in cursor]

    async def delete_reminder(self, reminder_id: Any) -> None:
        """Delete a reminder."""
        reminders = await self.get_collection("reminders")
        await reminders.delete_one({"_id": reminder_id})

    # =========================================================================
    # Polls (direct collection access)
    # =========================================================================

    async def create_poll(
        self, 
        chat_id: int, 
        creator_id: int, 
        question: str, 
        options: list, 
        anonymous: bool = False
    ) -> Any:
        """Create a poll."""
        polls = await self.get_collection("polls")
        result = await polls.insert_one({
            "chat_id": chat_id,
            "creator_id": creator_id,
            "question": question,
            "options": {str(i): {"text": opt, "votes": []} for i, opt in enumerate(options)},
            "anonymous": anonymous,
            "active": True,
            "created_at": time.time()
        })
        return result.inserted_id

    async def vote_poll(self, poll_id: Any, user_id: int, option_index: str) -> None:
        """Vote in a poll."""
        polls = await self.get_collection("polls")
        poll = await polls.find_one({"_id": poll_id})
        
        if poll:
            # Remove previous votes
            for opt_idx in poll["options"]:
                await polls.update_one(
                    {"_id": poll_id},
                    {"$pull": {f"options.{opt_idx}.votes": user_id}}
                )
        
        # Add new vote
        await polls.update_one(
            {"_id": poll_id},
            {"$addToSet": {f"options.{option_index}.votes": user_id}}
        )

    async def get_poll(self, poll_id: Any) -> Optional[Dict]:
        """Get a poll."""
        polls = await self.get_collection("polls")
        return await polls.find_one({"_id": poll_id})

    async def close_poll(self, poll_id: Any) -> None:
        """Close a poll."""
        polls = await self.get_collection("polls")
        await polls.update_one({"_id": poll_id}, {"$set": {"active": False}})

    # =========================================================================
    # Todo Lists (direct collection access)
    # =========================================================================

    async def add_todo(self, user_id: int, task: str) -> None:
        """Add a todo item."""
        todos = await self.get_collection("todos")
        await todos.insert_one({
            "user_id": user_id,
            "task": task,
            "done": False,
            "created_at": time.time()
        })

    async def get_todos(self, user_id: int) -> List[Dict]:
        """Get todos for a user."""
        todos = await self.get_collection("todos")
        cursor = todos.find({"user_id": user_id, "done": False})
        return [doc async for doc in cursor]

    async def complete_todo(self, user_id: int, task_index: int) -> bool:
        """Complete a todo item."""
        todos = await self.get_collection("todos")
        user_todos = await self.get_todos(user_id)
        
        if 0 <= task_index < len(user_todos):
            await todos.update_one(
                {"_id": user_todos[task_index]["_id"]},
                {"$set": {"done": True}}
            )
            return True
        return False

    async def clear_todos(self, user_id: int) -> None:
        """Clear all todos for a user."""
        todos = await self.get_collection("todos")
        await todos.delete_many({"user_id": user_id})

    # =========================================================================
    # Temp Actions (direct collection access)
    # =========================================================================

    async def add_temp_action(
        self, 
        chat_id: int, 
        user_id: int, 
        action_type: str, 
        expires_at: float
    ) -> None:
        """Add a temporary action."""
        temp_actions = await self.get_collection("temp_actions")
        await temp_actions.update_one(
            {"chat_id": chat_id, "user_id": user_id, "type": action_type},
            {"$set": {"expires_at": expires_at}},
            upsert=True
        )


# Global database instance (backward compatibility)
db = MongoDB()
