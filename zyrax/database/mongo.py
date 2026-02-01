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
            # Convert ObjectId to string to make it serializable for JSON/Cache
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            
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
            {
                "$set": {"username": username, "last_seen": time.time()},
                "$setOnInsert": {"xp": 0, "level": 1, "balance": 0, "inventory": [], "title": None}
            },
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

    # Economy & Levels
    async def add_xp(self, user_id: int, amount: int):
        users = await self.get_collection("users")
        await users.update_one(
            {"user_id": user_id},
            {"$inc": {"xp": amount}}
        )
        
    async def get_user_data(self, user_id: int):
        users = await self.get_collection("users")
        return await users.find_one({"user_id": user_id})

    async def update_level(self, user_id: int, new_level: int):
        users = await self.get_collection("users")
        await users.update_one(
            {"user_id": user_id},
            {"$set": {"level": new_level}}
        )

    async def add_balance(self, user_id: int, amount: int):
        users = await self.get_collection("users")
        await users.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": amount}}
        )

    async def get_top_users(self, limit: int = 10, sort_by: str = "xp"):
        users = await self.get_collection("users")
        cursor = users.find().sort(sort_by, -1).limit(limit)
        return [doc async for doc in cursor]

    # Shop / Inventory
    async def add_inventory_item(self, user_id: int, item_id: str):
        users = await self.get_collection("users")
        await users.update_one(
            {"user_id": user_id},
            {"$addToSet": {"inventory": item_id}}
        )

    async def set_title(self, user_id: int, title: str):
        users = await self.get_collection("users")
        await users.update_one(
            {"user_id": user_id},
            {"$set": {"title": title}}
        )

    # Karma
    async def change_karma(self, user_id: int, amount: int):
        users = await self.get_collection("users")
        await users.update_one(
            {"user_id": user_id},
            {"$inc": {"karma": amount}},
            upsert=True
        )
        doc = await users.find_one({"user_id": user_id})
        return doc.get("karma", 0)

    async def get_karma(self, user_id: int):
        users = await self.get_collection("users")
        doc = await users.find_one({"user_id": user_id})
        return doc.get("karma", 0) if doc else 0

    # Welcome / Goodbye / Rules
    async def set_welcome(self, chat_id: int, content: str = None, type: str = "text", media_id: str = None):
        """
        type: 'text' or 'image' (generated) or 'media' (file)
        """
        welcomes = await self.get_collection("welcomes")
        data = {}
        if content: data["content"] = content
        if type: data["type"] = type
        if media_id: data["media_id"] = media_id
        
        await welcomes.update_one(
            {"chat_id": chat_id},
            {"$set": data},
            upsert=True
        )

    async def get_welcome(self, chat_id: int):
        welcomes = await self.get_collection("welcomes")
        return await welcomes.find_one({"chat_id": chat_id})

    async def delete_welcome(self, chat_id: int):
        welcomes = await self.get_collection("welcomes")
        await welcomes.delete_one({"chat_id": chat_id})

    async def set_goodbye(self, chat_id: int, content: str = None, media_id: str = None, media_type: str = None):
        goodbyes = await self.get_collection("goodbyes")
        data = {}
        if content: data["content"] = content
        if media_id: data["media_id"] = media_id
        if media_type: data["media_type"] = media_type
        
        await goodbyes.update_one(
            {"chat_id": chat_id},
            {"$set": data},
            upsert=True
        )

    async def get_goodbye(self, chat_id: int):
        goodbyes = await self.get_collection("goodbyes")
        return await goodbyes.find_one({"chat_id": chat_id})
        
    async def delete_goodbye(self, chat_id: int):
        goodbyes = await self.get_collection("goodbyes")
        await goodbyes.delete_one({"chat_id": chat_id})

    # Captcha
    async def set_captcha(self, chat_id: int, enabled: bool = None, mode: str = None):
        settings = await self.get_collection("settings")
        data = {}
        if enabled is not None: data["captcha_enabled"] = enabled
        if mode: data["captcha_mode"] = mode
        
        await settings.update_one(
            {"chat_id": chat_id},
            {"$set": data},
            upsert=True
        )

    async def get_captcha_settings(self, chat_id: int):
        settings = await self.get_collection("settings")
        doc = await settings.find_one({"chat_id": chat_id})
        if not doc:
            return {"enabled": False, "mode": "button"}
        return {
            "enabled": doc.get("captcha_enabled", False),
            "mode": doc.get("captcha_mode", "button")
        }

    async def set_rules(self, chat_id: int, rules: str):
        settings = await self.get_collection("settings")
        await settings.update_one(
            {"chat_id": chat_id},
            {"$set": {"rules": rules}},
            upsert=True
        )

    # Blacklist
    async def add_blacklist(self, chat_id: int, word: str, action: str):
        blacklist = await self.get_collection("blacklist")
        await blacklist.update_one(
            {"chat_id": chat_id},
            {"$set": {f"words.{word}": action}},
            upsert=True
        )

    async def remove_blacklist(self, chat_id: int, word: str):
        blacklist = await self.get_collection("blacklist")
        await blacklist.update_one(
            {"chat_id": chat_id},
            {"$unset": {f"words.{word}": ""}}
        )

    async def get_blacklist(self, chat_id: int):
        blacklist = await self.get_collection("blacklist")
        doc = await blacklist.find_one({"chat_id": chat_id})
        return doc.get("words", {}) if doc else {}

    async def get_rules(self, chat_id: int):
        settings = await self.get_collection("settings")
        doc = await settings.find_one({"chat_id": chat_id})
        return doc.get("rules") if doc else None

    # Logging & Analytics
    async def log_admin_action(self, action: str, user_id: int, chat_id: int, target_id: int = None, details: str = None):
        logs = await self.get_collection("audit_logs")
        await logs.insert_one({
            "action": action,
            "user_id": user_id,
            "chat_id": chat_id,
            "target_id": target_id,
            "details": details,
            "timestamp": time.time()
        })

    async def get_audit_logs(self, limit: int = 50):
        logs = await self.get_collection("audit_logs")
        cursor = logs.find().sort("timestamp", -1).limit(limit)
        return [doc async for doc in cursor]

    async def track_activity(self, user_id: int, chat_id: int):
        # 1. Increment total messages for User
        # 2. Increment total messages for Chat
        # 3. Aggregation data (e.g. hourly bucket) - Simplified for MVP
        
        users = await self.get_collection("users")
        chats = await self.get_collection("chats")
        
        # User activity
        await users.update_one(
            {"user_id": user_id},
            {"$inc": {"msg_count": 1}, "$set": {"last_active": time.time()}},
            upsert=True
        )
        
        # Chat activity
        await chats.update_one(
            {"chat_id": chat_id},
            {"$inc": {"msg_count": 1}, "$set": {"last_active": time.time()}},
            upsert=True
        )
        
        # Heatmap Data (Stored in separate collection for analytics)
        # Key: "YYYY-MM-DD-HH"
        analytics = await self.get_collection("analytics")
        hour_key = time.strftime("%Y-%m-%d-%H")
        day_key = time.strftime("%Y-%m-%d")
        
        await analytics.update_one(
            {"key": hour_key, "type": "hourly"},
            {"$inc": {"count": 1}},
            upsert=True
        )
        
        await analytics.update_one(
            {"key": day_key, "type": "daily"},
            {"$inc": {"count": 1}},
            upsert=True
        )

    async def get_activity_stats(self):
        analytics = await self.get_collection("analytics")
        
        # Get last 7 days
        cursor = analytics.find({"type": "daily"}).sort("key", -1).limit(7)
        daily_data = [doc async for doc in cursor]
        
        # Get last 24 hours
        cursor = analytics.find({"type": "hourly"}).sort("key", -1).limit(24)
        hourly_data = [doc async for doc in cursor]
        
        return {
            "daily": sorted(daily_data, key=lambda x: x["key"]),
            "hourly": sorted(hourly_data, key=lambda x: x["key"])
        }

    # RSS
    async def add_rss(self, chat_id: int, url: str):
        settings = await self.get_collection("settings")
        await settings.update_one(
            {"chat_id": chat_id},
            {"$addToSet": {"rss_feeds": url}},
            upsert=True
        )

    async def get_chat_rss(self, chat_id: int):
        settings = await self.get_collection("settings")
        doc = await settings.find_one({"chat_id": chat_id})
        return doc.get("rss_feeds", []) if doc else []

    async def remove_rss(self, chat_id: int, url: str):
        settings = await self.get_collection("settings")
        await settings.update_one(
            {"chat_id": chat_id},
            {"$pull": {"rss_feeds": url}}
        )

    async def get_chat_settings(self, chat_id: int):
        settings = await self.get_collection("settings")
        doc = await settings.find_one({"chat_id": chat_id})
        return doc if doc else {}

    # Privacy / GDPR
    async def get_user_full_data(self, user_id: int):
        data = {}
        users = await self.get_collection("users")
        warnings = await self.get_collection("warnings")
        
        # Profile
        data["profile"] = await users.find_one({"user_id": user_id})
        
        # Warnings
        # Find all documents in warnings where user_id matches
        warn_cursor = warnings.find({"user_id": user_id})
        data["warnings"] = [doc async for doc in warn_cursor]
        
        return data

    async def delete_user_data(self, user_id: int):
        users = await self.get_collection("users")
        warnings = await self.get_collection("warnings")
        
        await users.delete_one({"user_id": user_id})
        await warnings.delete_many({"user_id": user_id})

    # Anti-Spam Settings
    async def set_antispam_setting(self, chat_id: int, key: str, value):
        settings = await self.get_collection("settings")
        await settings.update_one(
            {"chat_id": chat_id},
            {"$set": {f"antispam.{key}": value}},
            upsert=True
        )

    async def get_antispam_settings(self, chat_id: int):
        settings = await self.get_chat_settings(chat_id)
        return settings.get("antispam", {})

    # Raid Mode
    async def set_raid_mode(self, chat_id: int, enabled: bool, expires: float):
        settings = await self.get_collection("settings")
        await settings.update_one(
            {"chat_id": chat_id},
            {"$set": {"raid": {"enabled": enabled, "expires": expires}}},
            upsert=True
        )

    async def get_raid_mode(self, chat_id: int):
        settings = await self.get_chat_settings(chat_id)
        return settings.get("raid", {"enabled": False, "expires": 0})

    # Link Whitelist
    async def add_whitelist_domain(self, chat_id: int, domain: str):
        settings = await self.get_collection("settings")
        await settings.update_one(
            {"chat_id": chat_id},
            {"$addToSet": {"whitelist_domains": domain}},
            upsert=True
        )

    async def remove_whitelist_domain(self, chat_id: int, domain: str):
        settings = await self.get_collection("settings")
        await settings.update_one(
            {"chat_id": chat_id},
            {"$pull": {"whitelist_domains": domain}}
        )

    async def get_whitelist_domains(self, chat_id: int):
        settings = await self.get_chat_settings(chat_id)
        return settings.get("whitelist_domains", [])

    # Reminders
    async def add_reminder(self, user_id: int, chat_id: int, text: str, remind_at: float):
        reminders = await self.get_collection("reminders")
        await reminders.insert_one({
            "user_id": user_id,
            "chat_id": chat_id,
            "text": text,
            "remind_at": remind_at,
            "created_at": time.time()
        })

    async def get_due_reminders(self, current_time: float):
        reminders = await self.get_collection("reminders")
        cursor = reminders.find({"remind_at": {"$lte": current_time}})
        return [doc async for doc in cursor]

    async def delete_reminder(self, reminder_id):
        reminders = await self.get_collection("reminders")
        await reminders.delete_one({"_id": reminder_id})

    # Polls
    async def create_poll(self, chat_id: int, creator_id: int, question: str, options: list, anonymous: bool = False):
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

    async def vote_poll(self, poll_id, user_id: int, option_index: str):
        polls = await self.get_collection("polls")
        # Remove previous vote
        poll = await polls.find_one({"_id": poll_id})
        if poll:
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

    async def get_poll(self, poll_id):
        polls = await self.get_collection("polls")
        return await polls.find_one({"_id": poll_id})

    async def close_poll(self, poll_id):
        polls = await self.get_collection("polls")
        await polls.update_one({"_id": poll_id}, {"$set": {"active": False}})

    # Todo Lists (per user)
    async def add_todo(self, user_id: int, task: str):
        todos = await self.get_collection("todos")
        await todos.insert_one({
            "user_id": user_id,
            "task": task,
            "done": False,
            "created_at": time.time()
        })

    async def get_todos(self, user_id: int):
        todos = await self.get_collection("todos")
        cursor = todos.find({"user_id": user_id, "done": False})
        return [doc async for doc in cursor]

    async def complete_todo(self, user_id: int, task_index: int):
        todos = await self.get_collection("todos")
        user_todos = await self.get_todos(user_id)
        if 0 <= task_index < len(user_todos):
            await todos.update_one(
                {"_id": user_todos[task_index]["_id"]},
                {"$set": {"done": True}}
            )
            return True
        return False

    async def clear_todos(self, user_id: int):
        todos = await self.get_collection("todos")
        await todos.delete_many({"user_id": user_id})

    # Filter Stats
    async def increment_filter_stats(self, chat_id: int, filter_name: str):
        stats = await self.get_collection("filter_stats")
        await stats.update_one(
            {"chat_id": chat_id, "filter": filter_name},
            {"$inc": {"hits": 1}, "$set": {"last_hit": time.time()}},
            upsert=True
        )

    async def get_filter_stats(self, chat_id: int):
        stats = await self.get_collection("filter_stats")
        cursor = stats.find({"chat_id": chat_id}).sort("hits", -1)
        return [doc async for doc in cursor]

    # Game Stats
    async def update_game_stats(self, user_id: int, game: str, won: bool):
        users = await self.get_collection("users")
        field = f"games.{game}"
        await users.update_one(
            {"user_id": user_id},
            {
                "$inc": {
                    f"{field}.played": 1,
                    f"{field}.won": 1 if won else 0
                }
            },
            upsert=True
        )

    async def get_game_leaderboard(self, game: str, limit: int = 10):
        users = await self.get_collection("users")
        cursor = users.find({f"games.{game}.won": {"$exists": True}}).sort(f"games.{game}.won", -1).limit(limit)
        return [doc async for doc in cursor]

    # AI Moderation
    async def set_aimod(self, chat_id: int, enabled: bool):
        settings = await self.get_collection("settings")
        await settings.update_one(
            {"chat_id": chat_id},
            {"$set": {"aimod.enabled": enabled}},
            upsert=True
        )

    async def set_aimod_sensitivity(self, chat_id: int, level: str):
        settings = await self.get_collection("settings")
        await settings.update_one(
            {"chat_id": chat_id},
            {"$set": {"aimod.sensitivity": level}},
            upsert=True
        )

    async def get_aimod_settings(self, chat_id: int):
        settings = await self.get_chat_settings(chat_id)
        return settings.get("aimod", {"enabled": False, "sensitivity": "medium"})

    # Temp Actions (for temp bans/mutes)
    async def add_temp_action(self, chat_id: int, user_id: int, action_type: str, expires_at: float):
        temp_actions = await self.get_collection("temp_actions")
        await temp_actions.update_one(
            {"chat_id": chat_id, "user_id": user_id, "type": action_type},
            {"$set": {"expires_at": expires_at}},
            upsert=True
        )

    # Multi-language
    async def set_user_language(self, user_id: int, lang: str):
        users = await self.get_collection("users")
        await users.update_one(
            {"user_id": user_id},
            {"$set": {"language": lang}},
            upsert=True
        )

    async def get_user_language(self, user_id: int):
        user = await self.get_user_data(user_id)
        return user.get("language", "en") if user else "en"

    async def set_chat_language(self, chat_id: int, lang: str):
        settings = await self.get_collection("settings")
        await settings.update_one(
            {"chat_id": chat_id},
            {"$set": {"language": lang}},
            upsert=True
        )

    async def get_chat_language(self, chat_id: int):
        settings = await self.get_chat_settings(chat_id)
        return settings.get("language", "en")

    # Analytics Export
    async def export_chat_analytics(self, chat_id: int):
        """Export chat analytics as JSON-serializable dict"""
        analytics = await self.get_collection("analytics")
        logs = await self.get_collection("audit_logs")
        
        # Get analytics data
        daily_cursor = analytics.find({"type": "daily"}).sort("key", -1).limit(30)
        daily = [{"date": d["key"], "messages": d["count"]} async for d in daily_cursor]
        
        # Get logs
        log_cursor = logs.find({"chat_id": chat_id}).sort("timestamp", -1).limit(100)
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

db = MongoDB()
