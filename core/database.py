"""
MongoDB database connection and management using Motor (async)
"""
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class Database:
    """
    MongoDB database manager
    Handles connection, initialization, and basic operations
    """
    
    def __init__(self, uri: str, db_name: str):
        """
        Initialize database manager
        
        Args:
            uri: MongoDB connection URI
            db_name: Database name
        """
        self.uri = uri
        self.db_name = db_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        
    async def connect(self) -> None:
        """Establish database connection"""
        try:
            logger.info(f"Connecting to MongoDB at {self.uri}")
            
            # Create client
            self.client = AsyncIOMotorClient(
                self.uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=20000,
            )
            
            # Test connection
            await self.client.admin.command('ping')
            
            # Get database
            self.db = self.client[self.db_name]
            
            # Create indexes
            await self._create_indexes()
            
            logger.info(f"✓ Connected to MongoDB database: {self.db_name}")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise
    
    async def _create_indexes(self) -> None:
        """Create database indexes for better performance"""
        try:
            # Note: _id is automatically indexed by MongoDB, no need to create explicitly
            
            # Users collection indexes
            await self.db.users.create_index("username")
            
            # Filters collection indexes
            await self.db.filters.create_index([("chat_id", 1), ("trigger", 1)])
            
            # Notes collection indexes
            await self.db.notes.create_index([("chat_id", 1), ("name", 1)])
            
            # Warnings collection indexes
            await self.db.warnings.create_index([("chat_id", 1), ("user_id", 1)])
            
            # Federations collection indexes
            await self.db.federations.create_index("owner_id")
            
            # Captcha attempts collection indexes (for rate limiting)
            await self.db.captcha_attempts.create_index([("chat_id", 1), ("user_id", 1)])
            await self.db.captcha_attempts.create_index("timestamp")
            
            # User indexes for XP/Economy leaderboards
            await self.db.users.create_index([("xp", -1)])  # Descending for leaderboard
            await self.db.users.create_index([("currency", -1)])  # For economy leaderboard
            
            # Scheduled actions collection indexes
            await self.db.scheduled_actions.create_index("execute_at")
            await self.db.scheduled_actions.create_index([("chat_id", 1), ("user_id", 1)])
            
            logger.info("✓ Database indexes created")
            
        except Exception as e:
            logger.warning(f"Error creating indexes (non-critical): {e}")
    
    async def disconnect(self) -> None:
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("✓ MongoDB connection closed")
    
    def get_collection(self, collection_name: str):
        """
        Get a collection from the database
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection object
        """
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db[collection_name]
    
    # Convenience properties for common collections
    @property
    def chats(self):
        """Chats collection"""
        return self.get_collection("chats")
    
    @property
    def users(self):
        """Users collection"""
        return self.get_collection("users")
    
    @property
    def federations(self):
        """Federations collection"""
        return self.get_collection("federations")
    
    @property
    def filters(self):
        """Filters collection"""
        return self.get_collection("filters")
    
    @property
    def notes(self):
        """Notes collection"""
        return self.get_collection("notes")
    
    @property
    def warnings(self):
        """Warnings collection"""
        return self.get_collection("warnings")
    
    @property
    def blocklists(self):
        """Blocklists collection"""
        return self.get_collection("blocklists")
    
    @property
    def scheduled_actions(self):
        """Scheduled actions collection"""
        return self.get_collection("scheduled_actions")
    
    @property
    def action_logs(self):
        """Action logs collection"""
        return self.get_collection("action_logs")
    
    @property
    def captcha_pending(self):
        """Captcha pending collection"""
        return self.get_collection("captcha_pending")
    
    @property
    def captcha_attempts(self):
        """Captcha attempts collection (for rate limiting)"""
        return self.get_collection("captcha_attempts")