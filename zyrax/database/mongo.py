from motor.motor_asyncio import AsyncIOMotorClient
import time
from zyrax.config import Config

class MongoDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGO_URL)
        self.db = self.client.zyrax

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
        notes = await self.get_collection("notes")
        return await notes.find_one({"chat_id": chat_id, "name": name})

    async def delete_note(self, chat_id: int, name: str):
        notes = await self.get_collection("notes")
        result = await notes.delete_one({"chat_id": chat_id, "name": name})
        return result.deleted_count > 0

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
        settings = await self.get_collection("settings")
        doc = await settings.find_one({"chat_id": chat_id})
        return doc.get("flood_limit", 0) if doc else 0

    # Federations
    async def create_fed(self, owner_id: int, name: str, fed_id: str):
        feds = await self.get_collection("federations")
        # Check if name exists
        if await feds.find_one({"name": name}):
            return False
        
        await feds.insert_one({
            "fed_id": fed_id,
            "name": name,
            "owner_id": owner_id,
            "chats": []
        })
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

db = MongoDB()
