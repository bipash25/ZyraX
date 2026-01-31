"""
Check bot latency and responsiveness
"""
import logging
from time import time
from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import owner_only, log_command
from utils.time_parser import now_utc

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "ownerping",
    "aliases": ["opping", "botlatency"],
    "description": "Check bot latency (owner)",
    "usage": "/ownerping",
    "category": "owner",
    "scope": ["private", "group", "supergroup"]
}


@log_command
@owner_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Check bot latency
    """
    start_time = time()
    msg = await update.message.reply_text("🏓 Pinging...")
    end_time = time()
    
    latency = (end_time - start_time) * 1000  # Convert to ms
    
    # Get database latency
    db_latency = "N/A"
    db = context.application.bot_data.get('database')
    if db:
        try:
            db_start = time()
            await db.chats.find_one({"_id": "ping_test"})
            db_end = time()
            db_latency = f"{(db_end - db_start) * 1000:.2f}ms"
        except:
            db_latency = "Error"
    
    await msg.edit_text(
        f"🏓 <b>Pong!</b>\n\n"
        f"⚡ Bot Latency: <code>{latency:.2f}ms</code>\n"
        f"🗄️ Database: <code>{db_latency}</code>\n"
        f"⏰ Server Time: {now_utc().strftime('%H:%M:%S')} UTC",
        parse_mode='HTML'
    )

