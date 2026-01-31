"""
Ping command - Check bot responsiveness
"""
import logging
from time import time
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "ping",
    "aliases": [],
    "description": "Check if bot is responsive",
    "usage": "/ping",
    "category": "misc",
    "scope": ["private", "group", "supergroup"]
}


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /ping command
    Shows bot latency
    
    Args:
        update: Telegram update
        context: PTB context
    """
    start_time = time()
    
    # Send initial message
    message = await update.message.reply_text("🏓 Pong!")
    
    # Calculate latency
    end_time = time()
    latency = (end_time - start_time) * 1000
    
    # Edit with latency info
    await message.edit_text(
        f"🏓 **Pong!**\n\n"
        f"⚡ Latency: `{latency:.2f}ms`",
        parse_mode="Markdown"
    )
    
    logger.debug(f"Ping command executed with {latency:.2f}ms latency")