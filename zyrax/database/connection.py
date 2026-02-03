"""
Database Connection Management

Centralized database connection handling with proper configuration.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import redis.asyncio as redis
from typing import Optional
from zyrax.config import Config
from zyrax.constants import Limits
from zyrax.utils.logger import logger


class DatabaseConnection:
    """
    Manages MongoDB and Redis connections.
    
    Usage:
        connection = DatabaseConnection()
        await connection.initialize()
        db = connection.database
        redis = connection.redis
    """
    
    _instance: Optional['DatabaseConnection'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_mongo_client'):
            self._mongo_client: Optional[AsyncIOMotorClient] = None
            self._database: Optional[AsyncIOMotorDatabase] = None
            self._redis: Optional[redis.Redis] = None
    
    @property
    def database(self) -> AsyncIOMotorDatabase:
        """Get the MongoDB database instance."""
        if self._database is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._database
    
    @property
    def redis_client(self) -> redis.Redis:
        """Get the Redis client instance."""
        if self._redis is None:
            raise RuntimeError("Redis not initialized. Call initialize() first.")
        return self._redis
    
    @property
    def is_connected(self) -> bool:
        """Check if database connections are established."""
        return self._initialized and self._database is not None
    
    async def initialize(self) -> None:
        """
        Initialize database connections.
        
        Creates MongoDB client with proper pool configuration and Redis connection.
        Also creates necessary indexes.
        """
        if self._initialized:
            logger.debug("Database already initialized")
            return
        
        try:
            # Initialize MongoDB
            logger.info("Connecting to MongoDB...")
            self._mongo_client = AsyncIOMotorClient(
                Config.MONGO_URL,
                maxPoolSize=Limits.MONGO_MAX_POOL_SIZE,
                minPoolSize=Limits.MONGO_MIN_POOL_SIZE,
                maxIdleTimeMS=Limits.MONGO_MAX_IDLE_TIME_MS,
            )
            self._database = self._mongo_client.zyrax
            
            # Test MongoDB connection
            await self._database.command('ping')
            logger.info("MongoDB connection established")
            
            # Initialize Redis
            logger.info("Connecting to Redis...")
            self._redis = redis.from_url(
                Config.REDIS_URL,
                decode_responses=True,
                max_connections=20
            )
            
            # Test Redis connection
            await self._redis.ping()
            logger.info("Redis connection established")
            
            # Create indexes
            await self._create_indexes()
            
            self._initialized = True
            logger.info("Database initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _create_indexes(self) -> None:
        """Create database indexes for optimized queries."""
        try:
            # Warnings collection
            await self._database.warnings.create_index(
                [("user_id", 1), ("chat_id", 1)],
                unique=True
            )
            
            # Federations
            await self._database.fed_bans.create_index(
                [("fed_id", 1), ("user_id", 1)],
                unique=True
            )
            await self._database.federations.create_index("fed_id", unique=True)
            
            # Users
            await self._database.users.create_index("user_id", unique=True)
            await self._database.users.create_index("username")
            
            # Chats
            await self._database.chats.create_index("chat_id", unique=True)
            
            # Settings
            await self._database.settings.create_index("chat_id", unique=True)
            
            # Notes
            await self._database.notes.create_index(
                [("chat_id", 1), ("name", 1)],
                unique=True
            )
            
            # Filters
            await self._database.filters.create_index(
                [("chat_id", 1), ("name", 1)],
                unique=True
            )
            
            # Audit logs
            await self._database.audit_logs.create_index("timestamp")
            await self._database.audit_logs.create_index("chat_id")
            
            # Analytics
            await self._database.analytics.create_index([("key", 1), ("type", 1)])
            
            # Reminders
            await self._database.reminders.create_index("remind_at")
            
            # Temp actions
            await self._database.temp_actions.create_index("expires_at")
            
            logger.info("Database indexes created")
            
        except Exception as e:
            logger.warning(f"Error creating indexes (may already exist): {e}")
    
    async def close(self) -> None:
        """Close all database connections gracefully."""
        logger.info("Closing database connections...")
        
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.debug("Redis connection closed")
        
        if self._mongo_client:
            self._mongo_client.close()
            self._mongo_client = None
            self._database = None
            logger.debug("MongoDB connection closed")
        
        self._initialized = False
        logger.info("All database connections closed")
    
    async def health_check(self) -> dict:
        """
        Check health of database connections.
        
        Returns:
            dict with 'mongodb' and 'redis' status
        """
        status = {
            "mongodb": False,
            "redis": False,
            "initialized": self._initialized
        }
        
        try:
            if self._database is not None:
                await self._database.command('ping')
                status["mongodb"] = True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
        
        try:
            if self._redis is not None:
                await self._redis.ping()
                status["redis"] = True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
        
        return status


# Global connection instance
connection = DatabaseConnection()
