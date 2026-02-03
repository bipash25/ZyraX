"""
Settings Repository

Handles chat settings and configurations.
"""

import time
from typing import Optional, Dict, List, Any
from zyrax.database.repositories.base import BaseRepository
from zyrax.constants import Limits


class SettingsRepository(BaseRepository):
    """Repository for chat settings operations."""
    
    collection_name = "settings"
    
    async def get(self, chat_id: int) -> Dict:
        """
        Get chat settings with caching.
        
        Args:
            chat_id: Chat ID
            
        Returns:
            Settings dict (empty dict if not found)
        """
        cache_key = self._cache_key(chat_id)
        cached = await self._get_cached(cache_key)
        if cached:
            return cached
        
        doc = await self.find_one({"chat_id": chat_id})
        result = self._serialize_doc(doc) if doc else {}
        await self._set_cached(cache_key, result, Limits.SETTINGS_CACHE_TTL)
        return result
    
    async def _update(self, chat_id: int, data: Dict) -> None:
        """Internal update with cache invalidation."""
        await self.collection.update_one(
            {"chat_id": chat_id},
            {"$set": data},
            upsert=True
        )
        await self._invalidate_cache(self._cache_key(chat_id))
    
    # =========================================================================
    # Flood Settings
    # =========================================================================
    
    async def set_flood_limit(self, chat_id: int, limit: int) -> None:
        """Set flood limit for a chat."""
        await self._update(chat_id, {"flood_limit": limit})
    
    async def get_flood_limit(self, chat_id: int) -> int:
        """Get flood limit for a chat."""
        cache_key = f"flood_limit:{chat_id}"
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        settings = await self.get(chat_id)
        limit = settings.get("flood_limit", 0)
        await self._set_cached(cache_key, limit, Limits.FLOOD_LIMIT_CACHE_TTL)
        return limit
    
    # =========================================================================
    # Language Settings
    # =========================================================================
    
    async def set_language(self, chat_id: int, lang: str) -> None:
        """Set chat language."""
        await self._update(chat_id, {"language": lang})
    
    async def get_language(self, chat_id: int) -> str:
        """Get chat language."""
        settings = await self.get(chat_id)
        return settings.get("language", "en")
    
    # =========================================================================
    # Rules
    # =========================================================================
    
    async def set_rules(self, chat_id: int, rules: str) -> None:
        """Set chat rules."""
        await self._update(chat_id, {"rules": rules})
    
    async def get_rules(self, chat_id: int) -> Optional[str]:
        """Get chat rules."""
        settings = await self.get(chat_id)
        return settings.get("rules")
    
    # =========================================================================
    # Captcha Settings
    # =========================================================================
    
    async def set_captcha(
        self, 
        chat_id: int, 
        enabled: Optional[bool] = None, 
        mode: Optional[str] = None
    ) -> None:
        """Set captcha settings."""
        data = {}
        if enabled is not None:
            data["captcha_enabled"] = enabled
        if mode is not None:
            data["captcha_mode"] = mode
        
        if data:
            await self._update(chat_id, data)
    
    async def get_captcha_settings(self, chat_id: int) -> Dict:
        """Get captcha settings."""
        settings = await self.get(chat_id)
        return {
            "enabled": settings.get("captcha_enabled", False),
            "mode": settings.get("captcha_mode", "button")
        }
    
    # =========================================================================
    # Anti-Spam Settings
    # =========================================================================
    
    async def set_antispam(self, chat_id: int, key: str, value: Any) -> None:
        """Set an anti-spam setting."""
        await self._update(chat_id, {f"antispam.{key}": value})
    
    async def get_antispam_settings(self, chat_id: int) -> Dict:
        """Get anti-spam settings."""
        settings = await self.get(chat_id)
        return settings.get("antispam", {})
    
    # =========================================================================
    # Raid Mode
    # =========================================================================
    
    async def set_raid_mode(
        self, 
        chat_id: int, 
        enabled: bool, 
        expires: float = 0
    ) -> None:
        """Set raid mode."""
        await self._update(chat_id, {
            "raid": {"enabled": enabled, "expires": expires}
        })
    
    async def get_raid_mode(self, chat_id: int) -> Dict:
        """Get raid mode settings."""
        settings = await self.get(chat_id)
        return settings.get("raid", {"enabled": False, "expires": 0})
    
    # =========================================================================
    # Link Whitelist
    # =========================================================================
    
    async def add_whitelist_domain(self, chat_id: int, domain: str) -> None:
        """Add a domain to the whitelist."""
        await self.collection.update_one(
            {"chat_id": chat_id},
            {"$addToSet": {"whitelist_domains": domain}},
            upsert=True
        )
        await self._invalidate_cache(self._cache_key(chat_id))
    
    async def remove_whitelist_domain(self, chat_id: int, domain: str) -> None:
        """Remove a domain from the whitelist."""
        await self.collection.update_one(
            {"chat_id": chat_id},
            {"$pull": {"whitelist_domains": domain}}
        )
        await self._invalidate_cache(self._cache_key(chat_id))
    
    async def get_whitelist_domains(self, chat_id: int) -> List[str]:
        """Get whitelisted domains."""
        settings = await self.get(chat_id)
        return settings.get("whitelist_domains", [])
    
    # =========================================================================
    # RSS Feeds
    # =========================================================================
    
    async def add_rss(self, chat_id: int, url: str) -> None:
        """Add an RSS feed."""
        await self.collection.update_one(
            {"chat_id": chat_id},
            {"$addToSet": {"rss_feeds": url}},
            upsert=True
        )
        await self._invalidate_cache(self._cache_key(chat_id))
    
    async def remove_rss(self, chat_id: int, url: str) -> None:
        """Remove an RSS feed."""
        await self.collection.update_one(
            {"chat_id": chat_id},
            {"$pull": {"rss_feeds": url}}
        )
        await self._invalidate_cache(self._cache_key(chat_id))
    
    async def get_rss_feeds(self, chat_id: int) -> List[str]:
        """Get RSS feeds for a chat."""
        settings = await self.get(chat_id)
        return settings.get("rss_feeds", [])
    
    async def get_all_with_rss(self) -> List[Dict]:
        """Get all chats with RSS feeds configured."""
        cursor = self.collection.find({
            "rss_feeds": {"$exists": True, "$not": {"$size": 0}}
        })
        return [doc async for doc in cursor]
    
    # =========================================================================
    # AI Moderation
    # =========================================================================
    
    async def set_aimod(self, chat_id: int, enabled: bool) -> None:
        """Enable/disable AI moderation."""
        await self._update(chat_id, {"aimod.enabled": enabled})
    
    async def set_aimod_sensitivity(self, chat_id: int, level: str) -> None:
        """Set AI moderation sensitivity."""
        await self._update(chat_id, {"aimod.sensitivity": level})
    
    async def get_aimod_settings(self, chat_id: int) -> Dict:
        """Get AI moderation settings."""
        settings = await self.get(chat_id)
        return settings.get("aimod", {"enabled": False, "sensitivity": "medium"})
    
    # =========================================================================
    # Federation
    # =========================================================================
    
    async def set_federation(self, chat_id: int, fed_id: str) -> None:
        """Set federation for a chat."""
        await self._update(chat_id, {"fed_id": fed_id})
    
    async def get_federation(self, chat_id: int) -> Optional[str]:
        """Get federation ID for a chat."""
        settings = await self.get(chat_id)
        return settings.get("fed_id")
    
    async def leave_federation(self, chat_id: int) -> None:
        """Remove chat from federation."""
        await self.collection.update_one(
            {"chat_id": chat_id},
            {"$unset": {"fed_id": ""}}
        )
        await self._invalidate_cache(self._cache_key(chat_id))
