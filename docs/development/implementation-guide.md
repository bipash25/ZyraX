# ZyraX Implementation Reference

**Technical reference for code patterns and implementations used in ZyraX bot**

---

## Dependencies

### Core Dependencies

```txt
# Telegram Bot Framework
python-telegram-bot[rate-limiter]==20.7
pyrogram==2.0.106
TgCrypto==1.2.5

# Database & Caching
motor==3.3.2          # Async MongoDB driver
pymongo==4.6.1        # MongoDB sync driver (for utilities)
redis==5.0.1          # Redis client
aioredis==2.0.1       # Async Redis

# Task Scheduling
APScheduler==3.10.4

# Image Processing
Pillow==10.1.0        # Captcha generation

# Utilities
python-dotenv==1.0.0  # Environment management
pydantic==2.5.3       # Data validation
aiohttp==3.9.1        # Async HTTP client

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.12.1
flake8==6.1.0
mypy==1.7.1
```

---

## Environment Configuration

### Required Environment Variables

```env
# Bot Credentials
BOT_TOKEN=<telegram_bot_token>
BOT_USERNAME=<bot_username>
OWNER_ID=<owner_telegram_id>

# MTProto Credentials
TELEGRAM_API_ID=<api_id>
TELEGRAM_API_HASH=<api_hash>

# Database
MONGO_URI=mongodb://localhost:27017/zyrax
MONGO_DB_NAME=zyrax

# Caching (Optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Application
LOG_LEVEL=INFO
LOG_FILE=data/logs/bot.log
ENABLE_MTPROTO=true
ENABLE_REDIS=false

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MESSAGES=20
RATE_LIMIT_PERIOD=60
```

---

## Core Implementation Patterns

### Application Entry Point

`bot.py` - Main application entry point

```python
#!/usr/bin/env python3
"""ZyraX Bot - Main Entry Point"""
import asyncio
import logging
from pathlib import Path

from core.application import ZyraXApplication
from core.logger import setup_logging
from config import settings

setup_logging(settings.LOG_LEVEL, settings.LOG_FILE)
logger = logging.getLogger(__name__)


async def main():
    """Initialize and start the bot"""
    logger.info("Starting ZyraX Bot...")
    
    try:
        app = ZyraXApplication()
        await app.initialize()
        
        logger.info("Bot initialized. Starting...")
        await app.start()
        await app.idle()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal. Shutting down...")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        raise
    finally:
        if app:
            await app.shutdown()
            logger.info("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
```

### Configuration Management

`config.py` - Pydantic-based configuration

```python
"""Application configuration management"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Bot Configuration
    BOT_TOKEN: str
    BOT_USERNAME: str
    OWNER_ID: int
    
    # MTProto
    TELEGRAM_API_ID: Optional[int] = None
    TELEGRAM_API_HASH: Optional[str] = None
    ENABLE_MTPROTO: bool = True
    
    # Database
    MONGO_URI: str
    MONGO_DB_NAME: str = "zyrax"
    
    # Redis
    ENABLE_REDIS: bool = False
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "data/logs/bot.log"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_MESSAGES: int = 20
    RATE_LIMIT_PERIOD: int = 60


settings = Settings()
```

### Application Orchestrator

`core/application.py` - Main application manager

```python
"""Main application orchestrator managing all components"""
import logging
from telegram.ext import Application
from pyrogram import Client

from core.database import Database
from core.cache import CacheManager
from core.scheduler import init_scheduler
from core.loader import CommandLoader

logger = logging.getLogger(__name__)


class ZyraXApplication:
    """Main application managing bot components"""
    
    def __init__(self):
        self.ptb_app: Optional[Application] = None
        self.pyrogram_client: Optional[Client] = None
        self.db: Optional[Database] = None
        self.cache: Optional[CacheManager] = None
        self.scheduler = None
        self.loader: Optional[CommandLoader] = None
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing components...")
        
        # Database
        self.db = Database()
        await self.db.connect()
        
        # Cache
        self.cache = CacheManager()
        await self.cache.connect()
        
        # PTB Application
        self.ptb_app = Application.builder().token(settings.BOT_TOKEN).build()
        
        # Pyrogram Client
        if settings.ENABLE_MTPROTO:
            self.pyrogram_client = Client(
                "zyrax_session",
                api_id=settings.TELEGRAM_API_ID,
                api_hash=settings.TELEGRAM_API_HASH,
                bot_token=settings.BOT_TOKEN
            )
        
        # Scheduler
        self.scheduler = init_scheduler(self.db)
        
        # Command Loader
        self.loader = CommandLoader(self.ptb_app, self.db, self.cache)
        await self.loader.load_all()
        
        logger.info("All components initialized")
    
    async def start(self):
        """Start the bot"""
        if self.pyrogram_client:
            await self.pyrogram_client.start()
        
        await self.ptb_app.initialize()
        await self.ptb_app.start()
        await self.ptb_app.updater.start_polling()
        
        self.scheduler.start()
    
    async def idle(self):
        """Keep bot running until interrupted"""
        await self.ptb_app.updater.wait_until_stopped()
    
    async def shutdown(self):
        """Shutdown all components gracefully"""
        logger.info("Shutting down...")
        
        if self.scheduler:
            self.scheduler.shutdown()
        
        if self.ptb_app:
            await self.ptb_app.stop()
            await self.ptb_app.shutdown()
        
        if self.pyrogram_client:
            await self.pyrogram_client.stop()
        
        if self.cache:
            await self.cache.close()
        
        if self.db:
            await self.db.close()
```

### Command Loader

`core/loader.py` - Dynamic command discovery and registration

```python
"""Dynamic command loader with metadata-driven registration"""
import logging
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Callable
from telegram.ext import CommandHandler

logger = logging.getLogger(__name__)


class CommandLoader:
    """Discovers and registers commands dynamically"""
    
    def __init__(self, app, db, cache):
        self.app = app
        self.db = db
        self.cache = cache
        self.commands: Dict[str, dict] = {}
        self.categories: Dict[str, List[str]] = {}
    
    async def load_all(self):
        """Scan handlers directory and load all commands"""
        handlers_dir = Path("handlers")
        
        for module_path in handlers_dir.rglob("*.py"):
            if module_path.name.startswith("_"):
                continue
            
            await self._load_module(module_path)
        
        logger.info(f"Loaded {len(self.commands)} commands across {len(self.categories)} categories")
    
    async def _load_module(self, module_path: Path):
        """Load a single command module"""
        module_name = str(module_path).replace("/", ".").replace("\\", ".")[:-3]
        
        try:
            module = importlib.import_module(module_name)
            
            if not hasattr(module, "COMMAND_INFO") or not hasattr(module, "handle"):
                return
            
            command_info = module.COMMAND_INFO
            handler_func = module.handle
            
            # Validate command info
            required_fields = ["name", "description", "category"]
            if not all(field in command_info for field in required_fields):
                logger.warning(f"Invalid COMMAND_INFO in {module_name}")
                return
            
            # Register command
            self._register_command(command_info, handler_func)
            
        except Exception as e:
            logger.error(f"Error loading {module_name}: {e}")
    
    def _register_command(self, info: dict, handler: Callable):
        """Register a command with PTB"""
        name = info["name"]
        aliases = info.get("aliases", [])
        
        # Create handler
        cmd_handler = CommandHandler([name] + aliases, handler)
        self.app.add_handler(cmd_handler)
        
        # Track command
        self.commands[name] = info
        category = info["category"]
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(name)
        
        logger.debug(f"Registered command: /{name}")
```

### Database Operations

`core/database.py` - MongoDB connection and operations

```python
"""Database connection and operations"""
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database manager"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=5000
            )
            
            # Verify connection
            await self.client.admin.command('ping')
            
            self.db = self.client[settings.MONGO_DB_NAME]
            logger.info(f"Connected to MongoDB: {settings.MONGO_DB_NAME}")
            
        except ConnectionFailure as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    @property
    def chats(self):
        """Access chats collection"""
        return self.db.chats
    
    @property
    def users(self):
        """Access users collection"""
        return self.db.users
    
    @property
    def federations(self):
        """Access federations collection"""
        return self.db.federations
    
    @property
    def filters(self):
        """Access filters collection"""
        return self.db.filters
    
    @property
    def notes(self):
        """Access notes collection"""
        return self.db.notes
```

### User Resolution

`utils/user_resolver.py` - Multi-source user identification

```python
"""User resolution from multiple sources with caching"""
import logging
from typing import Optional, Union
from telegram import Update, User

logger = logging.getLogger(__name__)


class UserResolver:
    """Resolve users from various input formats"""
    
    def __init__(self, db, cache, mtproto_client=None):
        self.db = db
        self.cache = cache
        self.mtproto = mtproto_client
    
    async def resolve(
        self,
        update: Update,
        identifier: Optional[Union[str, int]] = None
    ) -> Optional[User]:
        """
        Resolve user from identifier or update context
        
        Resolution priority:
        1. Reply to message
        2. Text mention entity
        3. Username/ID with cache lookup
        4. MTProto fallback
        5. Command sender
        """
        
        # Check reply
        if update.message and update.message.reply_to_message:
            return update.message.reply_to_message.from_user
        
        # Check text mention
        if update.message and update.message.entities:
            for entity in update.message.entities:
                if entity.type == "text_mention":
                    return entity.user
        
        # No identifier provided - return sender
        if not identifier:
            return update.effective_user
        
        # Resolve from identifier
        if isinstance(identifier, int):
            return await self._resolve_by_id(identifier)
        
        if isinstance(identifier, str):
            if identifier.startswith("@"):
                identifier = identifier[1:]
            return await self._resolve_by_username(identifier)
        
        return None
    
    async def _resolve_by_id(self, user_id: int) -> Optional[User]:
        """Resolve user by ID with caching"""
        # Check cache
        cached = await self.cache.get(f"user:{user_id}")
        if cached:
            return User.de_json(cached, None)
        
        # Check database
        user_doc = await self.db.users.find_one({"_id": user_id})
        if user_doc:
            user = self._user_from_doc(user_doc)
            await self.cache.set(f"user:{user_id}", user.to_dict(), ttl=900)
            return user
        
        # MTProto fallback
        if self.mtproto:
            try:
                user = await self.mtproto.get_users(user_id)
                await self._cache_user(user)
                return user
            except Exception as e:
                logger.warning(f"MTProto resolution failed for {user_id}: {e}")
        
        return None
    
    async def _resolve_by_username(self, username: str) -> Optional[User]:
        """Resolve user by username with caching"""
        # Check cache
        cached = await self.cache.get(f"username:{username}")
        if cached:
            return User.de_json(cached, None)
        
        # Check database
        user_doc = await self.db.users.find_one({"username": username})
        if user_doc:
            user = self._user_from_doc(user_doc)
            await self.cache.set(f"username:{username}", user.to_dict(), ttl=900)
            return user
        
        # MTProto fallback
        if self.mtproto:
            try:
                user = await self.mtproto.get_users(username)
                await self._cache_user(user)
                return user
            except Exception as e:
                logger.warning(f"MTProto resolution failed for @{username}: {e}")
        
        return None
    
    def _user_from_doc(self, doc: dict) -> User:
        """Convert database document to User object"""
        return User(
            id=doc["_id"],
            is_bot=doc.get("is_bot", False),
            first_name=doc.get("first_name", ""),
            last_name=doc.get("last_name"),
            username=doc.get("username"),
            language_code=doc.get("language")
        )
    
    async def _cache_user(self, user: User):
        """Cache user in both database and cache"""
        user_doc = {
            "_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_bot": user.is_bot,
            "language": user.language_code
        }
        
        await self.db.users.update_one(
            {"_id": user.id},
            {"$set": user_doc},
            upsert=True
        )
        
        await self.cache.set(f"user:{user.id}", user.to_dict(), ttl=900)
        if user.username:
            await self.cache.set(f"username:{user.username}", user.to_dict(), ttl=900)
```

---

## Command Handler Pattern

### Standard Handler Structure

```python
"""Example command handler"""
from telegram import Update
from telegram.ext import ContextTypes

# Command metadata
COMMAND_INFO = {
    "name": "example",
    "aliases": ["ex"],
    "description": "Example command description",
    "usage": "/example <argument>",
    "category": "misc",
    "permissions": {
        "user": ["can_send_messages"],
        "bot": []
    },
    "scope": ["group", "supergroup"],
    "admin_only": False,
    "owner_only": False
}


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command handler implementation"""
    # Get database and cache from context
    db = context.application.bot_data["database"]
    cache = context.application.bot_data["cache"]
    
    # Command logic
    await update.message.reply_text("Example response")
```

### Permission-Protected Handler

```python
"""Admin command with permission checks"""
from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import require_admin, require_bot_permission, log_command

COMMAND_INFO = {
    "name": "ban",
    "description": "Ban a user from the chat",
    "usage": "/ban <user> [reason]",
    "category": "moderation",
    "permissions": {
        "user": ["can_restrict_members"],
        "bot": ["can_restrict_members"]
    },
    "scope": ["group", "supergroup"],
    "admin_only": True
}


@log_command
@require_admin(permissions=["can_restrict_members"])
@require_bot_permission(permissions=["can_restrict_members"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban user handler"""
    # Resolve target user
    resolver = context.application.bot_data["user_resolver"]
    target_user = await resolver.resolve(update, context.args[0] if context.args else None)
    
    if not target_user:
        await update.message.reply_text("❌ User not found")
        return
    
    # Perform ban
    await update.effective_chat.ban_member(target_user.id)
    
    # Log action
    db = context.application.bot_data["database"]
    await db.action_logs.insert_one({
        "action": "ban",
        "chat_id": update.effective_chat.id,
        "user_id": target_user.id,
        "admin_id": update.effective_user.id,
        "timestamp": datetime.now(UTC)
    })
    
    await update.message.reply_text(f"✅ {target_user.mention_html()} has been banned")
```

---

## Middleware Implementation

### Permission Checker

```python
"""Permission checking middleware"""
from telegram import Update
from telegram.ext import ContextTypes

async def check_permissions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify user and bot permissions"""
    if not update.effective_chat or update.effective_chat.type == "private":
        return True
    
    # Get required permissions from command metadata
    command = context.matches[0].group() if context.matches else None
    if not command:
        return True
    
    loader = context.application.bot_data["loader"]
    cmd_info = loader.commands.get(command[1:])  # Remove / prefix
    
    if not cmd_info:
        return True
    
    # Check admin requirement
    if cmd_info.get("admin_only"):
        member = await update.effective_chat.get_member(update.effective_user.id)
        if member.status not in ["creator", "administrator"]:
            await update.message.reply_text("❌ This command requires admin privileges")
            return False
    
    # Check specific permissions
    required_perms = cmd_info.get("permissions", {}).get("user", [])
    if required_perms:
        member = await update.effective_chat.get_member(update.effective_user.id)
        for perm in required_perms:
            if not getattr(member, perm, False):
                await update.message.reply_text(f"❌ Missing permission: {perm}")
                return False
    
    return True
```

---

## Database Schema Patterns

### Chat Settings

```python
"""Chat configuration document structure"""
{
    "_id": chat_id,  # Primary key
    "chat_type": "supergroup",
    "title": "Chat Title",
    "language": "en",
    
    "antiflood": {
        "enabled": False,
        "limit": 10,
        "mode": "mute",
        "time": 3600
    },
    
    "captcha": {
        "enabled": False,
        "mode": "button",
        "kick_enabled": False,
        "kick_time": 300
    },
    
    "locks": {
        "sticker": False,
        "url": False,
        # ...other lock types
    },
    
    "created_at": datetime.now(UTC),
    "updated_at": datetime.now(UTC)
}
```

### User Data

```python
"""User data document structure"""
{
    "_id": user_id,  # Primary key
    "username": "username",
    "first_name": "First",
    "language": "en",
    
    "chats": {
        str(chat_id): {
            "warnings": 0,
            "approved": False,
            "flood_count": 0,
            "xp": 0,
            "level": 0,
            "balance": 0
        }
    },
    
    "created_at": datetime.now(UTC)
}
```

---

## Testing Patterns

### Command Handler Test

```python
"""Example command handler test"""
import pytest
from telegram import Update, Message, Chat, User
from telegram.ext import ContextTypes

@pytest.mark.asyncio
async def test_example_command():
    """Test example command handler"""
    # Create mock update
    update = Update(
        update_id=1,
        message=Message(
            message_id=1,
            date=datetime.now(),
            chat=Chat(id=-1001234567890, type="supergroup"),
            from_user=User(id=123, first_name="Test", is_bot=False),
            text="/example test"
        )
    )
    
    # Create mock context
    context = ContextTypes.DEFAULT_TYPE()
    context.args = ["test"]
    
    # Execute handler
    from handlers.misc.example import handle
    await handle(update, context)
    
    # Assertions
    assert update.message.reply_text.called
```

---

## Performance Optimization Patterns

### Database Query Optimization

```python
"""Optimized database queries"""

# Use projection to fetch only needed fields
chat_doc = await db.chats.find_one(
    {"_id": chat_id},
    {"antiflood": 1, "language": 1}
)

# Use indexes for frequent queries
await db.chats.create_index("language")
await db.users.create_index("username")

# Batch operations for bulk updates
await db.users.update_many(
    {"chats.{}.warnings": {"$gte": 3}},
    {"$set": {"chats.{}.banned": True}}
)
```

### Caching Strategy

```python
"""Multi-tier caching implementation"""

async def get_chat_settings(chat_id):
    """Get chat settings with caching"""
    cache_key = f"chat:{chat_id}"
    
    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # Fetch from database
    doc = await db.chats.find_one({"_id": chat_id})
    if doc:
        await cache.set(cache_key, doc, ttl=900)
        return doc
    
    # Return default settings
    return default_chat_settings()
```

---

## Error Handling

### Global Error Handler

```python
"""Global error handler"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle all uncaught errors"""
    logger.error("Exception while handling update:", exc_info=context.error)
    
    # Send user-friendly error message
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "❌ An error occurred while processing your request. "
            "The issue has been logged."
        )
    
    # Notify admins (optional)
    if hasattr(context, 'application'):
        db = context.application.bot_data.get('database')
        if db:
            await db.error_logs.insert_one({
                "error": str(context.error),
                "update": str(update),
                "timestamp": datetime.now(UTC)
            })
```

---

## Deployment Configuration

### systemd Service

```ini
[Unit]
Description=ZyraX Telegram Bot
After=network.target mongodb.service

[Service]
Type=simple
User=zyrax
WorkingDirectory=/opt/zyrax
ExecStart=/opt/zyrax/venv/bin/python bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Docker Configuration

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run bot
CMD ["python", "bot.py"]
```

---

**Document Version:** 2.0  
**Last Updated:** October 2025