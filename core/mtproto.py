"""
MTProto client wrapper using Pyrogram
Handles advanced Telegram features not available in Bot API
"""
import logging
from typing import Optional
from pathlib import Path
from pyrogram import Client
from pyrogram.errors import (
    FloodWait, 
    AuthKeyUnregistered,
    UserDeactivated,
    SessionRevoked
)
import asyncio

logger = logging.getLogger(__name__)


class MTProtoClient:
    """
    Pyrogram MTProto client wrapper
    Provides access to advanced Telegram features
    """
    
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        bot_token: str,
        session_name: str = "zyrax_bot",
        workdir: str = "data/sessions"
    ):
        """
        Initialize MTProto client
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            bot_token: Bot token from BotFather
            session_name: Name for session file
            workdir: Directory to store session files
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.bot_token = bot_token
        self.session_name = session_name
        self.workdir = Path(workdir)
        
        # Ensure session directory exists
        self.workdir.mkdir(parents=True, exist_ok=True)
        
        # Initialize client
        self.client: Optional[Client] = None
        self._is_running = False
    
    async def initialize(self) -> None:
        """Initialize Pyrogram client"""
        try:
            logger.info("Initializing Pyrogram MTProto client...")
            
            self.client = Client(
                name=self.session_name,
                api_id=self.api_id,
                api_hash=self.api_hash,
                bot_token=self.bot_token,
                workdir=str(self.workdir),
                in_memory=False  # Save session to file
            )
            
            logger.info("✓ Pyrogram client initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pyrogram client: {e}")
            raise
    
    async def start(self) -> None:
        """Start Pyrogram client"""
        if not self.client:
            raise RuntimeError("Client not initialized. Call initialize() first.")
        
        try:
            logger.info("Starting Pyrogram client...")
            await self.client.start()
            self._is_running = True
            
            # Get bot info
            me = await self.client.get_me()
            logger.info(f"✓ Pyrogram client started as @{me.username} (ID: {me.id})")
            
        except (AuthKeyUnregistered, SessionRevoked, UserDeactivated) as e:
            logger.error(f"Session error: {e}. Please delete session file and restart.")
            raise
        except FloodWait as e:
            logger.warning(f"FloodWait: Must wait {e.value} seconds")
            await asyncio.sleep(e.value)
            await self.start()  # Retry
        except OSError as e:
            if "database is locked" in str(e).lower():
                logger.error(
                    "Session database is locked. This usually means another bot instance is running.\n"
                    "Solutions:\n"
                    "  1. Stop other bot instances: pm2 stop zyrax\n"
                    "  2. Kill other processes: pkill -f 'python.*bot.py'\n"
                    "  3. Delete session file: rm -f data/sessions/zyrax_bot.session*"
                )
            raise
        except Exception as e:
            logger.error(f"Failed to start Pyrogram client: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop Pyrogram client"""
        if self.client and self._is_running:
            try:
                await self.client.stop()
                self._is_running = False
                logger.info("✓ Pyrogram client stopped")
            except Exception as e:
                logger.error(f"Error stopping Pyrogram client: {e}")
    
    def is_available(self) -> bool:
        """Check if MTProto client is available and running"""
        return self.client is not None and self._is_running
    
    async def resolve_username(self, username: str):
        """
        Resolve username to user object
        
        Args:
            username: Username (without @)
            
        Returns:
            User object or None if not found
        """
        if not self.is_available():
            logger.warning("MTProto client not available")
            return None
        
        try:
            username = username.lstrip("@")
            user = await self.client.get_users(username)
            logger.debug(f"Resolved @{username} -> ID {user.id}")
            return user
        except FloodWait as e:
            logger.warning(f"FloodWait when resolving @{username}: {e.value}s")
            return None
        except Exception as e:
            logger.debug(f"Could not resolve @{username}: {e}")
            return None
    
    async def get_user_by_id(self, user_id: int):
        """
        Get user by ID
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            User object or None if not found
        """
        if not self.is_available():
            logger.warning("MTProto client not available")
            return None
        
        try:
            user = await self.client.get_users(user_id)
            logger.debug(f"Retrieved user ID {user_id}")
            return user
        except FloodWait as e:
            logger.warning(f"FloodWait when getting user {user_id}: {e.value}s")
            return None
        except Exception as e:
            logger.debug(f"Could not get user {user_id}: {e}")
            return None
    
    async def get_chat_members_count(self, chat_id: int) -> Optional[int]:
        """
        Get accurate chat members count using MTProto
        
        Args:
            chat_id: Chat ID
            
        Returns:
            Members count or None
        """
        if not self.is_available():
            return None
        
        try:
            count = await self.client.get_chat_members_count(chat_id)
            return count
        except Exception as e:
            logger.debug(f"Could not get members count for {chat_id}: {e}")
            return None
    
    async def get_chat_admins(self, chat_id: int):
        """
        Get full admin list with permissions using MTProto
        
        Args:
            chat_id: Chat ID
            
        Returns:
            List of ChatMember objects or empty list
        """
        if not self.is_available():
            return []
        
        try:
            admins = []
            async for member in self.client.get_chat_members(
                chat_id,
                filter="administrators"
            ):
                admins.append(member)
            return admins
        except Exception as e:
            logger.debug(f"Could not get admins for {chat_id}: {e}")
            return []