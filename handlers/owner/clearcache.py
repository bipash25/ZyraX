"""
Clear bot cache
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import owner_only, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "clearcache",
    "aliases": ["cc", "flushcache"],
    "description": "Clear bot cache",
    "usage": "/clearcache",
    "category": "owner",
    "scope": ["private"]
}


@log_command
@owner_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Clear all cached data
    """
    cache = context.application.bot_data.get('cache')
    if not cache:
        await update.message.reply_text("❌ Cache not available")
        return
    
    msg = await update.message.reply_text("⏳ Clearing cache...")
    
    try:
        # Get size before clearing
        old_size = cache.memory_cache.size() if hasattr(cache.memory_cache, 'size') else 0
        
        # Clear cache
        await cache.clear()
        
        await msg.edit_text(
            f"✅ <b>Cache Cleared</b>\n\n"
            f"Cleared {old_size} entries from memory cache\n"
            f"Redis cache also cleared (if enabled)",
            parse_mode='HTML'
        )
        
        logger.info(f"Cache cleared by owner (cleared {old_size} entries)")
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        await msg.edit_text(f"❌ Error: {str(e)}")

