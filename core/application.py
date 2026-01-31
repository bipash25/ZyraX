"""
Main application class managing all bot components
Coordinates PTB, Pyrogram, Database, Cache, Scheduler, and Loader
"""
import logging
from typing import Optional
from telegram.ext import Application, ApplicationBuilder, MessageHandler, filters, TypeHandler
from pyrogram import Client

from core.database import Database
from core.cache import CacheManager
from core.scheduler import SchedulerManager
from core.loader import CommandLoader
from core.mtproto import MTProtoClient
from middleware.antiflood_check import antiflood_middleware
from middleware.antiraid_check import handle_new_member
from middleware.captcha_handler import handle_new_member_captcha
from middleware.permapin_enforcer import periodic_permapin_check
from middleware.filter_trigger import check_filter_trigger
from middleware.note_hashtag import check_note_hashtag
from middleware.blocklist_checker import check_blocklist
from middleware.federation_checker import check_federation_ban
from middleware.locks_enforcer import check_locks
from middleware.xp_tracker import track_xp
from middleware.greetings_handler import register_handlers as register_greetings_handlers
from handlers.captcha.verify_handler import get_message_handler, get_callback_handler
from handlers.reports.commands import get_report_handlers
from config import settings

logger = logging.getLogger(__name__)


class ZyraXApplication:
    """
    Main application managing all bot components
    Handles initialization, startup, and shutdown
    """
    
    def __init__(self):
        """Initialize application components"""
        self.ptb_app: Optional[Application] = None
        self.mtproto: Optional[MTProtoClient] = None
        self.db: Optional[Database] = None
        self.cache: Optional[CacheManager] = None
        self.scheduler: Optional[SchedulerManager] = None
        self.loader: Optional[CommandLoader] = None
        
        # Bot info (populated after initialization)
        self.bot_id: Optional[int] = None
        self.bot_username: Optional[str] = None
    
    async def initialize(self) -> None:
        """Initialize all components"""
        logger.info("=" * 70)
        logger.info("Initializing ZyraX Application...")
        logger.info("=" * 70)
        
        # 1. Database
        logger.info("[1/7] Connecting to MongoDB...")
        self.db = Database(settings.MONGO_URI, settings.MONGO_DB_NAME)
        await self.db.connect()
        
        # 2. Cache
        logger.info("[2/7] Initializing cache system...")
        self.cache = CacheManager(
            redis_enabled=settings.redis_enabled,
            redis_host=settings.REDIS_HOST,
            redis_port=settings.REDIS_PORT,
            redis_db=settings.REDIS_DB,
            redis_password=settings.REDIS_PASSWORD
        )
        await self.cache.initialize()
        
        # 3. PTB Application
        logger.info("[3/7] Building PTB application...")
        self.ptb_app = (
            ApplicationBuilder()
            .token(settings.BOT_TOKEN)
            .concurrent_updates(True)
            .build()
        )
        
        # Get bot info
        bot_info = await self.ptb_app.bot.get_me()
        self.bot_id = bot_info.id
        self.bot_username = bot_info.username
        
        logger.info(f"    Bot: @{self.bot_username} (ID: {self.bot_id})")
        
        # Update settings if not set
        if not settings.BOT_USERNAME:
            settings.BOT_USERNAME = self.bot_username
        
        # 4. Pyrogram (MTProto)
        if settings.mtproto_enabled:
            logger.info("[4/7] Initializing Pyrogram MTProto client...")
            self.mtproto = MTProtoClient(
                api_id=settings.TELEGRAM_API_ID,
                api_hash=settings.TELEGRAM_API_HASH,
                bot_token=settings.BOT_TOKEN
            )
            await self.mtproto.initialize()
        else:
            logger.info("[4/7] MTProto disabled (set ENABLE_MTPROTO=true to enable)")
            logger.warning("    Some advanced features will be limited without MTProto")
        
        # 5. Scheduler
        logger.info("[5/7] Starting scheduler...")
        self.scheduler = SchedulerManager(self.db)
        await self.scheduler.start()
        
        # Store shared resources in bot_data for handler access
        self.ptb_app.bot_data['mtproto_client'] = self.mtproto
        self.ptb_app.bot_data['database'] = self.db
        self.ptb_app.bot_data['cache'] = self.cache
        self.ptb_app.bot_data['scheduler'] = self.scheduler
        
        # 6. Middleware (must be registered before command handlers)
        logger.info("[6/9] Registering middleware...")
        # Antiflood middleware - TypeHandler runs for all updates
        self.ptb_app.add_handler(
            TypeHandler(type=object, callback=antiflood_middleware),
            group=-10  # High priority, runs before everything
        )
        # Antiraid middleware - ChatMemberHandler for new joins
        from telegram.ext import ChatMemberHandler
        self.ptb_app.add_handler(
            ChatMemberHandler(handle_new_member, ChatMemberHandler.CHAT_MEMBER),
            group=-9
        )
        # Captcha middleware - ChatMemberHandler for new joins
        self.ptb_app.add_handler(
            ChatMemberHandler(handle_new_member_captcha, ChatMemberHandler.CHAT_MEMBER),
            group=-8
        )
        # Federation ban checker - ChatMemberHandler for new joins
        self.ptb_app.add_handler(
            ChatMemberHandler(check_federation_ban, ChatMemberHandler.CHAT_MEMBER),
            group=-7
        )
        # Greetings middleware - MessageHandler for join/leave events
        register_greetings_handlers(self.ptb_app)
        # Captcha verification handlers
        self.ptb_app.add_handler(get_message_handler(), group=5)
        self.ptb_app.add_handler(get_callback_handler(), group=5)
        
        # Trivia game callback handler
        from handlers.fun.trivia import get_trivia_handler
        self.ptb_app.add_handler(get_trivia_handler(), group=5)
        
        # Report handlers
        for handler in get_report_handlers():
            self.ptb_app.add_handler(handler, group=6)
        
        # Locks enforcer middleware - Check for locked content types
        self.ptb_app.add_handler(
            TypeHandler(type=object, callback=check_locks),
            group=7  # After reports, before blocklist
        )
        
        # Blocklist checker middleware - Check messages for blocked words
        self.ptb_app.add_handler(
            TypeHandler(type=object, callback=check_blocklist),
            group=8  # Before filters but after commands
        )
        
        # Filter trigger middleware - TypeHandler for text messages
        self.ptb_app.add_handler(
            TypeHandler(type=object, callback=check_filter_trigger),
            group=10  # Lower priority, runs after command handlers
        )
        # Note hashtag middleware - TypeHandler for #notename
        self.ptb_app.add_handler(
            TypeHandler(type=object, callback=check_note_hashtag),
            group=11  # After filters
        )
        
        # XP tracker middleware - Track message activity for leveling
        self.ptb_app.add_handler(
            TypeHandler(type=object, callback=track_xp),
            group=12  # Lowest priority - runs last
        )
        
        # 7. Command Loader
        logger.info("[7/9] Loading command handlers...")
        self.loader = CommandLoader(self.ptb_app, self.db, self.cache)
        await self.loader.load_all_handlers()
        
        # 8. Post-initialization tasks
        logger.info("[8/9] Running post-initialization tasks...")
        # Schedule antiraid expiry checks
        if self.scheduler:
            await self._schedule_antiraid_checks()
            # Schedule periodic permapin check
            self.scheduler.schedule_periodic_permapin_check(
                periodic_permapin_check,
                self.ptb_app
            )
            # Schedule flood tracker cleanup (every 5 minutes)
            from middleware.antiflood_check import cleanup_flood_tracker
            self.scheduler.scheduler.add_job(
                cleanup_flood_tracker,
                'interval',
                minutes=5,
                id='flood_tracker_cleanup',
                replace_existing=True
            )
            logger.info("✓ Scheduled flood tracker cleanup (every 5 minutes)")
        
        # 9. Error Handler
        logger.info("[9/9] Registering error handler...")
        self.ptb_app.add_error_handler(self._error_handler)
        
        logger.info("=" * 70)
        logger.info("✓ Application initialized successfully")
        logger.info("=" * 70)
    
    async def start(self) -> None:
        """Start the bot"""
        logger.info("Starting ZyraX bot...")
        
        # Start MTProto client if enabled
        if self.mtproto:
            try:
                await self.mtproto.start()
            except Exception as e:
                logger.error(f"Failed to start MTProto client: {e}")
                logger.warning("Continuing without MTProto - some features will be limited")
                self.mtproto = None  # Disable MTProto to prevent further errors
        
        # Initialize and start PTB
        await self.ptb_app.initialize()
        await self.ptb_app.start()
        await self.ptb_app.updater.start_polling(
            allowed_updates=["message", "callback_query", "chat_member", "my_chat_member"],
            drop_pending_updates=False
        )
        
        logger.info("=" * 70)
        logger.info(f"🚀 @{self.bot_username} is now ONLINE!")
        logger.info("=" * 70)
    
    async def idle(self) -> None:
        """Keep the bot running until stopped"""
        # PTB will handle keeping the application running
        await self.ptb_app.updater.stop()
    
    async def shutdown(self) -> None:
        """Graceful shutdown of all components"""
        logger.info("=" * 70)
        logger.info("Shutting down ZyraX bot...")
        logger.info("=" * 70)
        
        # Stop scheduler
        if self.scheduler:
            try:
                logger.info("[1/5] Stopping scheduler...")
                await self.scheduler.shutdown()
            except Exception as e:
                logger.error(f"Error stopping scheduler: {e}")
        
        # Stop MTProto
        if self.mtproto:
            try:
                logger.info("[2/5] Stopping Pyrogram client...")
                await self.mtproto.stop()
            except Exception as e:
                logger.error(f"Error stopping Pyrogram client: {e}")
        
        # Stop PTB
        if self.ptb_app:
            try:
                logger.info("[3/5] Stopping PTB application...")
                # Stop updater first if running
                if self.ptb_app.updater and self.ptb_app.updater.running:
                    await self.ptb_app.updater.stop()
                    logger.debug("Updater stopped")
                # Then stop the application if running
                if self.ptb_app.running:
                    await self.ptb_app.stop()
                    await self.ptb_app.shutdown()
                else:
                    logger.debug("PTB application was not running, skipping stop")
            except Exception as e:
                logger.error(f"Error stopping PTB application: {e}")
        
        # Close cache
        if self.cache:
            try:
                logger.info("[4/5] Closing cache connections...")
                await self.cache.close()
            except Exception as e:
                logger.error(f"Error closing cache: {e}")
        
        # Disconnect database
        if self.db:
            try:
                logger.info("[5/5] Disconnecting from database...")
                await self.db.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting database: {e}")
        
        logger.info("=" * 70)
        logger.info("✓ Shutdown complete. Goodbye!")
        logger.info("=" * 70)
    
    async def _schedule_antiraid_checks(self):
        """Schedule checks for expired antiraid modes"""
        try:
            # Find all chats with active antiraid
            cursor = self.db.chats.find({
                "antiraid_enabled": True,
                "antiraid_expires": {"$exists": True}
            })
            
            scheduled_count = 0
            async for chat_doc in cursor:
                chat_id = chat_doc['_id']
                expires = chat_doc.get('antiraid_expires')
                
                if expires:
                    await self.scheduler.schedule_action(
                        chat_id=int(chat_id),
                        action_type='disable_antiraid',
                        execute_at=expires
                    )
                    scheduled_count += 1
            
            if scheduled_count > 0:
                logger.info(f"    Scheduled {scheduled_count} antiraid expiry checks")
        except Exception as e:
            logger.error(f"Error scheduling antiraid checks: {e}")
    
    async def _error_handler(self, update, context):
        """
        Global error handler for PTB
        
        Args:
            update: Telegram update that caused the error
            context: PTB context containing error info
        """
        logger.error(f"Update {update} caused error: {context.error}", exc_info=context.error)
        
        # Send user-friendly message if possible
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ An unexpected error occurred. Please try again later."
                )
            except Exception:
                pass  # Failed to send error message, ignore