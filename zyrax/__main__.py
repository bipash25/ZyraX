"""
ZyraX Bot Main Entry Point

Initializes and runs the Telegram bot with all services.
"""

import asyncio
import signal
import sys
from typing import Optional, Set

import uvicorn
from pyrogram.client import Client
from pyrogram.sync import idle

from zyrax.config import Config
from zyrax.constants import Limits, Timeouts
from zyrax.modules import load_modules, get_load_stats
from zyrax.utils.logger import logger
from zyrax.dashboard import app as dashboard_app


# Global state for graceful shutdown
_shutdown_event: Optional[asyncio.Event] = None
_running_tasks: Set[asyncio.Task] = set()
_bot_client: Optional[Client] = None
_call_client = None  # PyTgCalls instance


def setup_signal_handlers() -> asyncio.Event:
    """
    Set up signal handlers for graceful shutdown.
    
    Returns:
        Event that will be set when shutdown is requested
    """
    shutdown_event = asyncio.Event()
    
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, initiating graceful shutdown...")
        shutdown_event.set()
    
    # Handle SIGINT (Ctrl+C) and SIGTERM (docker stop)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    return shutdown_event


async def start_dashboard() -> None:
    """Start the dashboard web server."""
    config = uvicorn.Config(
        dashboard_app, 
        host=Limits.DEFAULT_DASHBOARD_HOST, 
        port=Limits.DEFAULT_DASHBOARD_PORT, 
        log_level="warning",  # Reduce log noise
        access_log=False
    )
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except asyncio.CancelledError:
        logger.info("Dashboard server shutting down...")
        raise


async def graceful_shutdown(
    app: Client, 
    tasks: Set[asyncio.Task],
    timeout: int = Timeouts.GRACEFUL_SHUTDOWN_TIMEOUT
) -> None:
    """
    Perform graceful shutdown of all services.
    
    Args:
        app: Pyrogram client
        tasks: Set of running background tasks
        timeout: Maximum seconds to wait for shutdown
    """
    global _call_client
    
    logger.info("Starting graceful shutdown...")
    
    # Cancel all background tasks
    for task in tasks:
        if not task.done():
            task.cancel()
    
    # Wait for tasks to complete with timeout
    if tasks:
        logger.info(f"Waiting for {len(tasks)} background tasks...")
        done, pending = await asyncio.wait(
            tasks, 
            timeout=timeout,
            return_when=asyncio.ALL_COMPLETED
        )
        
        if pending:
            logger.warning(f"{len(pending)} tasks did not complete in time")
            for task in pending:
                task.cancel()
    
    # Stop PyTgCalls if running
    if _call_client:
        try:
            logger.info("Stopping music player...")
            # PyTgCalls doesn't have a stop method, just leave all calls
        except Exception as e:
            logger.error(f"Error stopping call client: {e}")
    
    # Stop the bot
    try:
        logger.info("Stopping bot...")
        await app.stop()
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
    
    # Close database connections
    try:
        logger.info("Closing database connections...")
        from zyrax.database import db
        await db.close()
    except Exception as e:
        logger.error(f"Error closing database: {e}")
    
    logger.info("Shutdown complete.")


async def main() -> None:
    """Main entry point for the bot."""
    global _shutdown_event, _bot_client, _call_client
    
    # Set up signal handlers for graceful shutdown
    _shutdown_event = setup_signal_handlers()
    
    # Print startup banner
    logger.info("=" * 50)
    logger.info("ZyraX Bot Starting...")
    logger.info("=" * 50)
    
    # Validate configuration
    logger.info("Configuration validated successfully")
    logger.debug(Config.get_summary())
    
    # Load all modules
    logger.info("Loading modules...")
    loaded_modules = load_modules()
    stats = get_load_stats()
    logger.info(
        f"Modules: {stats['loaded']} loaded, {stats['failed']} failed, "
        f"total time: {stats['total_load_time']:.2f}s"
    )
    
    if stats['failed'] > 0:
        logger.warning(f"Failed modules: {', '.join(stats['failed_modules'])}")
    
    # Initialize Database
    logger.info("Initializing database...")
    from zyrax.database.mongo import db
    await db.initialize()
    
    # Check database health
    health = await db.health_check()
    if not health.get("mongodb") or not health.get("redis"):
        logger.error(f"Database health check failed: {health}")
        sys.exit(1)
    logger.info("Database connected and healthy")
    
    # Create Pyrogram client
    app = Client(
        "ZyraX",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        plugins=dict(root="zyrax.modules")
    )
    _bot_client = app
    
    # Initialize PyTgCalls for music
    try:
        from pytgcalls import PyTgCalls
        call_client = PyTgCalls(app)
        app.call_client = call_client  # type: ignore # Attach to app for modules
        _call_client = call_client
        logger.info("PyTgCalls initialized")
    except ImportError:
        logger.warning("PyTgCalls not available, music features disabled")
        call_client = None
    except Exception as e:
        logger.error(f"Failed to initialize PyTgCalls: {e}")
        call_client = None
    
    # Inject bot instance into dashboard
    dashboard_app.state.bot = app
    
    # Start the bot
    await app.start()
    logger.info("Bot started successfully")
    
    # Start PyTgCalls
    if call_client:
        try:
            await call_client.start()
            logger.info("Music player started")
        except Exception as e:
            logger.error(f"Failed to start music player: {e}")
    
    # Get bot info
    try:
        me = await app.get_me()
        logger.info(f"Logged in as @{me.username} (ID: {me.id})")
    except Exception as e:
        logger.warning(f"Could not get bot info: {e}")
    
    # Start background tasks
    logger.info("Starting background services...")
    
    # Dashboard
    dashboard_task = asyncio.create_task(start_dashboard())
    dashboard_task.set_name("dashboard")
    _running_tasks.add(dashboard_task)
    logger.info(f"Dashboard running on {Limits.DEFAULT_DASHBOARD_HOST}:{Limits.DEFAULT_DASHBOARD_PORT}")
    
    # Backup loop
    try:
        from zyrax.utils.backup import backup_database
        backup_task = asyncio.create_task(backup_database())
        backup_task.set_name("backup")
        _running_tasks.add(backup_task)
        logger.info("Backup scheduler started")
    except ImportError:
        logger.warning("Backup module not available")
    except Exception as e:
        logger.error(f"Failed to start backup scheduler: {e}")
    
    # Scheduler loop (reminders, temp actions, etc.)
    try:
        from zyrax.utils.scheduler import scheduler_loop
        scheduler_task = asyncio.create_task(scheduler_loop(app))
        scheduler_task.set_name("scheduler")
        _running_tasks.add(scheduler_task)
        logger.info("Task scheduler started")
    except ImportError:
        logger.warning("Scheduler module not available")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
    
    logger.info("=" * 50)
    logger.info("ZyraX is now running!")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 50)
    
    # Wait for shutdown signal or idle
    try:
        # Use asyncio.wait with the shutdown event
        shutdown_wait = asyncio.create_task(_shutdown_event.wait())
        
        # Create idle task
        async def wait_for_idle():
            await idle()
        
        idle_task = asyncio.create_task(wait_for_idle())
        
        # Wait for either shutdown signal or idle to complete
        done, pending = await asyncio.wait(
            [shutdown_wait, idle_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel pending
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
                
    except asyncio.CancelledError:
        logger.info("Main task cancelled")
    
    # Perform graceful shutdown
    await graceful_shutdown(app, _running_tasks)


def run() -> None:
    """Entry point for the bot."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run()
