from motor.motor_asyncio import AsyncIOMotorClient
import time
import redis.asyncio as redis
from pydantic import BaseModel, Field
from typing import List, Optional
from zyrax.config import Config
from zyrax.database.cache import Cache

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
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGO_URL)
        self.db = self.client.zyrax
        self.redis = redis.from_url(Config.REDIS_URL, decode_responses=True)
        self.cache = Cache(self.redis)

    async def initialize(self):
        # Create Indexes
        await self.db.warnings.create_index([("user_id", 1), ("chat_id", 1)], unique=True)
        await self.db.fed_bans.create_index([("fed_id", 1), ("user_id", 1)], unique=True)
        await self.db.federations.create_index("fed_id", unique=True)
        print("Database indexes created.")

    async def get_collection(self, name):
        return self.db[name]

    async def add_warn(self, chat_id: int, user_id: int, reason: str = None):
        warnings = await self.get_collection("warnings")
        await warnings.update_one(
            {"chat_id": chat_id, "user_id": user_id},
            {"$push": {"warns": {"reason": reason, "date": time.time()}}, "$inc": {"count": 1}},
            upsert=True
        )
        doc = await warnings.find_one({"chat_id": chat_id, "user_id": user_id})
        return doc["count"]

    async def remove_warn(self, chat_id: int, user_id: int):
        warnings = await self.get_collection("warnings")
        doc = await warnings.find_one({"chat_id": chat_id, "user_id": user_id})
        if doc and doc["count"] > 0:
            await warnings.update_one(
                {"chat_id": chat_id, "user_id": user_id},
                {"$pop": {"warns": -1}, "$inc": {"count": -1}}
            )
            return doc["count"] - 1
        return 0

    async def get_warns(self, chat_id: int, user_id: int):
        warnings = await self.get_collection("warnings")
        doc = await warnings.find_one({"chat_id": chat_id, "user_id": user_id})
        return doc if doc else None

    async def reset_warns(self, chat_id: int, user_id: int):
        warnings = await self.get_collection("warnings")
        await warnings.delete_one({"chat_id": chat_id, "user_id": user_id})

    # Notes / Filters
    async def save_note(self, chat_id: int, name: str, data: dict):
        notes = await self.get_collection("notes")
        await notes.update_one(
            {"chat_id": chat_id, "name": name},
            {"$set": {"data": data}},
            upsert=True
        )

    async def get_note(self, chat_id: int, name: str):
        # Try Cache First
        cache_key = f"note:{chat_id}:{name}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        notes = await self.get_collection("notes")
        doc = await notes.find_one({"chat_id": chat_id, "name": name})
        
        if doc:
            await self.cache.set(cache_key, doc, ttl=600)
            return doc
        return None

    async def delete_note(self, chat_id: int, name: str):
        notes = await self.get_collection("notes")
        result = await notes.delete_one({"chat_id": chat_id, "name": name})
        if result.deleted_count > 0:
            await self.cache.delete(f"note:{chat_id}:{name}")
            return True
        return False

    async def get_all_notes(self, chat_id: int):
        notes = await self.get_collection("notes")
        cursor = notes.find({"chat_id": chat_id})
        return [doc["name"] async for doc in cursor]

    # Filters
    async def save_filter(self, chat_id: int, name: str, data: dict):
        filters = await self.get_collection("filters")
        await filters.update_one(
            {"chat_id": chat_id, "name": name},
            {"$set": {"data": data}},
            upsert=True
        )

    async def get_filter(self, chat_id: int, name: str):
        filters = await self.get_collection("filters")
        return await filters.find_one({"chat_id": chat_id, "name": name})

    async def delete_filter(self, chat_id: int, name: str):
        filters = await self.get_collection("filters")
        result = await filters.delete_one({"chat_id": chat_id, "name": name})
        return result.deleted_count > 0

    async def get_chat_filters(self, chat_id: int):
        filters = await self.get_collection("filters")
        cursor = filters.find({"chat_id": chat_id})
        return {doc["name"]: doc["data"] async for doc in cursor}

    # Anti-Flood
    async def set_flood(self, chat_id: int, limit: int):
        settings = await self.get_collection("settings")
        await settings.update_one(
            {"chat_id": chat_id},
            {"$set": {"flood_limit": limit}},
            upsert=True
        )

    async def get_flood_limit(self, chat_id: int):
        # Cache this?
        cache_key = f"flood_limit:{chat_id}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached

        settings = await self.get_collection("settings")
        doc = await settings.find_one({"chat_id": chat_id})
        limit = doc.get("flood_limit", 0) if doc else 0
        
        await self.cache.set(cache_key, limit, ttl=300)
        return limit

    # Federations
    async def create_fed(self, owner_id: int, name: str, fed_id: str):
        feds = await self.get_collection("federations")
        if await feds.find_one({"name": name}):
            return False
            
        # Pydantic Validation
        fed = FederationDocument(fed_id=fed_id, name=name, owner_id=owner_id)
        
        await feds.insert_one(fed.model_dump())
        return True

    async def get_fed(self, fed_id: str):
        feds = await self.get_collection("federations")
        return await feds.find_one({"fed_id": fed_id})

    async def join_fed(self, fed_id: str, chat_id: int):
        feds = await self.get_collection("federations")
        result = await feds.update_one(
            {"fed_id": fed_id},
            {"$addToSet": {"chats": chat_id}}
        )
        if result.modified_count > 0:
            settings = await self.get_collection("settings")
            await settings.update_one(
                {"chat_id": chat_id},
                {"$set": {"fed_id": fed_id}},
                upsert=True
            )
            return True
        return False

    async def leave_fed(self, chat_id: int):
        settings = await self.get_collection("settings")
        doc = await settings.find_one({"chat_id": chat_id})
        if not doc or "fed_id" not in doc:
            return False
        
        fed_id = doc["fed_id"]
        feds = await self.get_collection("federations")
        await feds.update_one(
            {"fed_id": fed_id},
            {"$pull": {"chats": chat_id}}
        )
        await settings.update_one(
            {"chat_id": chat_id},
            {"$unset": {"fed_id": ""}}
        )
        return True

    async def get_chat_fed_id(self, chat_id: int):
        settings = await self.get_collection("settings")
        doc = await settings.find_one({"chat_id": chat_id})
        return doc.get("fed_id") if doc else None

    async def fed_ban(self, fed_id: str, user_id: int, reason: str):
        bans = await self.get_collection("fed_bans")
        await bans.update_one(
            {"fed_id": fed_id, "user_id": user_id},
            {"$set": {"reason": reason, "date": time.time()}},
            upsert=True
        )

    async def fed_unban(self, fed_id: str, user_id: int):
        bans = await self.get_collection("fed_bans")
        result = await bans.delete_one({"fed_id": fed_id, "user_id": user_id})
        return result.deleted_count > 0

    async def is_user_fedor_banned(self, fed_id: str, user_id: int):
        bans = await self.get_collection("fed_bans")
        return await bans.find_one({"fed_id": fed_id, "user_id": user_id})

    # Tournaments
    async def create_tournament(self, chat_id: int, name: str, size: int):
        tourneys = await self.get_collection("tournaments")
        # Check if active tournament exists for this chat
        if await tourneys.find_one({"chat_id": chat_id, "status": "active"}):
            return False
            
        await tourneys.insert_one({
            "chat_id": chat_id,
            "name": name,
            "size": size,
            "participants": [],
            "status": "registration", # registration, active, completed
            "round": 0,
            "matches": []
        })
        return True

    async def get_active_tournament(self, chat_id: int):
        tourneys = await self.get_collection("tournaments")
        return await tourneys.find_one({"chat_id": chat_id, "status": {"$ne": "completed"}})

    async def join_tournament(self, chat_id: int, user_id: int, user_name: str):
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

    async def start_tournament(self, chat_id: int):
        tourneys = await self.get_collection("tournaments")
        doc = await tourneys.find_one({"chat_id": chat_id, "status": "registration"})
        if not doc:
            return False
        
        # Simple shuffling and pairing logic
        import random
        participants = doc["participants"]
        random.shuffle(participants)
        
        # Create matches for Round 1
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

    # Stats Tracking
    async def register_user(self, user_id: int, username: str = None):
        users = await self.get_collection("users")
        await users.update_one(
            {"user_id": user_id},
            {"$set": {"username": username, "last_seen": time.time()}},
            upsert=True
        )

    async def register_chat(self, chat_id: int, title: str = None):
        chats = await self.get_collection("chats")
        await chats.update_one(
            {"chat_id": chat_id},
            {"$set": {"title": title, "last_active": time.time()}},
            upsert=True
        )

    async def get_stats(self):
        users = await self.get_collection("users")
        chats = await self.get_collection("chats")
        
        user_count = await users.count_documents({})
        chat_count = await chats.count_documents({})
        
        # Get today's commands from Redis
        today = time.strftime("%Y-%m-%d")
        cmd_count = await self.redis.get(f"stats:commands:{today}")
        
        return {
            "users": user_count,
            "chats": chat_count,
            "commands_today": int(cmd_count) if cmd_count else 0
        }

    async def track_command_usage(self):
        today = time.strftime("%Y-%m-%d")
        await self.redis.incr(f"stats:commands:{today}")

db = MongoDB()
