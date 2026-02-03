"""
Base Repository

Abstract base class for all database repositories.
"""

from abc import ABC
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from typing import Optional, Any, Dict, List
from zyrax.database.cache import Cache


class BaseRepository(ABC):
    """
    Base class for database repositories.
    
    Provides common functionality for:
        - Collection access
        - Caching
        - Common CRUD operations
    """
    
    collection_name: str = ""
    
    def __init__(self, database: AsyncIOMotorDatabase, cache: Cache):
        self.db = database
        self.cache = cache
        
        if not self.collection_name:
            raise ValueError(f"{self.__class__.__name__} must define collection_name")
    
    @property
    def collection(self) -> AsyncIOMotorCollection:
        """Get the MongoDB collection for this repository."""
        return self.db[self.collection_name]
    
    def _cache_key(self, *args) -> str:
        """Generate a cache key from arguments."""
        return f"{self.collection_name}:{':'.join(str(a) for a in args)}"
    
    async def _get_cached(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        return await self.cache.get(key)
    
    async def _set_cached(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set a value in cache."""
        await self.cache.set(key, value, ttl)
    
    async def _invalidate_cache(self, key: str) -> None:
        """Invalidate a cache entry."""
        await self.cache.delete(key)
    
    async def find_one(self, query: Dict) -> Optional[Dict]:
        """Find a single document."""
        return await self.collection.find_one(query)
    
    async def find_many(
        self, 
        query: Dict, 
        limit: int = 100,
        sort_by: Optional[str] = None,
        sort_order: int = -1
    ) -> List[Dict]:
        """Find multiple documents."""
        cursor = self.collection.find(query)
        
        if sort_by:
            cursor = cursor.sort(sort_by, sort_order)
        
        cursor = cursor.limit(limit)
        
        return [doc async for doc in cursor]
    
    async def count(self, query: Dict = None) -> int:
        """Count documents matching query."""
        if query is None:
            query = {}
        return await self.collection.count_documents(query)
    
    async def insert_one(self, document: Dict) -> Any:
        """Insert a single document."""
        result = await self.collection.insert_one(document)
        return result.inserted_id
    
    async def update_one(
        self, 
        query: Dict, 
        update: Dict, 
        upsert: bool = False
    ) -> bool:
        """Update a single document."""
        result = await self.collection.update_one(query, update, upsert=upsert)
        return result.modified_count > 0 or result.upserted_id is not None
    
    async def delete_one(self, query: Dict) -> bool:
        """Delete a single document."""
        result = await self.collection.delete_one(query)
        return result.deleted_count > 0
    
    async def delete_many(self, query: Dict) -> int:
        """Delete multiple documents."""
        result = await self.collection.delete_many(query)
        return result.deleted_count
    
    def _serialize_doc(self, doc: Optional[Dict]) -> Optional[Dict]:
        """
        Serialize a MongoDB document for caching.
        Converts ObjectId to string.
        """
        if doc is None:
            return None
        
        result = dict(doc)
        if "_id" in result:
            result["_id"] = str(result["_id"])
        return result
