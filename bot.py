#!/usr/bin/env python3
"""
ZyraX Bot - Main Entry Point
All-in-One Telegram Group Management Bot

Usage:
    python bot.py

Requirements:
    - Python 3.11+
    - MongoDB running
    - .env file with bot credentials
"""
import asyncio
import sys
import logging
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))

from core.application import ZyraXApplication
from core.logger import setup_logging
from config import settings

# Initialize logging first
setup_logging(settings.LOG_LEVEL, settings.LOG_FILE)
logger = logging.getLogger(__name__)


def print_banner():
    """Print startup banner"""
    banner = """
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║            ███████╗██╗   ██╗██████╗  █████╗ ██╗  ██╗           ║
    ║            ╚══███╔╝╚██╗ ██╔╝██╔══██╗██╔══██╗╚██╗██╔╝           ║
    ║              ███╔╝  ╚████╔╝ ██████╔╝███████║ ╚███╔╝            ║
    ║             ███╔╝    ╚██╔╝  ██╔══██╗██╔══██║ ██╔██╗            ║
    ║            ███████╗   ██║   ██║  ██║██║  ██║██╔╝ ██╗           ║
    ║            ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝           ║
    ║                                                                ║
    ║            All-in-One Telegram Group Management Bot            ║
    ║                         Version 2.0.0                          ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """
    print(banner)


async def main():
    """Main function to start the bot"""
    print_banner()
    
    # Create application instance
    app = None
    fatal_error = False
    
    try:
        logger.info("Starting ZyraX Bot v2.0.0...")
        
        # Initialize application
        app = ZyraXApplication()
        await app.initialize()
        
        # Start bot
        await app.start()
        
        # Keep running until interrupted
        logger.info("Bot is running. Press Ctrl+C to stop.")
        
        # Wait for stop signal
        try:
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Received stop signal...")
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.critical(f"Fatal error during startup: {e}", exc_info=True)
        fatal_error = True
    finally:
        # Graceful shutdown
        if app:
            try:
                await app.shutdown()
            except Exception as shutdown_error:
                logger.error(f"Error during shutdown: {shutdown_error}")
        
        # Exit with appropriate code
        if fatal_error:
            sys.exit(1)


if __name__ == "__main__":
    try:
        # Run the bot
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)