"""
Bot statistics - Total users, chats, commands used, etc.
"""
import logging
from datetime import timedelta
from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import owner_only, log_command
from utils.time_parser import now_utc

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "stats",
    "aliases": ["botstats", "statistics"],
    "description": "Get detailed bot statistics",
    "usage": "/stats",
    "category": "owner",
    "scope": ["private", "group", "supergroup"]
}


@log_command
@owner_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Get comprehensive bot statistics
    """
    db = context.application.bot_data.get('database')
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    msg = await update.message.reply_text("📊 Gathering statistics...")
    
    try:
        # Count documents in collections
        total_users = await db.users.count_documents({})
        total_chats = await db.chats.count_documents({})
        total_federations = await db.federations.count_documents({})
        total_filters = await db.filters.count_documents({})
        total_notes = await db.notes.count_documents({})
        total_warnings = await db.warnings.count_documents({})
        total_blocklists = await db.blocklists.count_documents({})
        total_actions = await db.action_logs.count_documents({})
        total_captcha_pending = await db.captcha_pending.count_documents({})
        total_scheduled = await db.scheduled_actions.count_documents({})
        
        # Get active chats (chats with recent activity)
        one_week_ago = now_utc() - timedelta(days=7)
        active_chats = await db.action_logs.distinct("chat_id", {
            "timestamp": {"$gte": one_week_ago}
        })
        
        # Count different chat types
        group_chats = await db.chats.count_documents({
            "_id": {"$regex": "^-"}
        })
        
        # Get command registry
        command_registry = context.application.bot_data.get('command_registry', {})
        total_commands = len(command_registry)
        
        # Get cache stats
        cache = context.application.bot_data.get('cache')
        cache_size = 0
        if cache and hasattr(cache.memory_cache, 'size'):
            cache_size = cache.memory_cache.size()
        
        # Build response
        response = (
            "📊 <b>Bot Statistics</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            
            "👥 <b>Users & Chats:</b>\n"
            f"  • Total Users: <code>{total_users:,}</code>\n"
            f"  • Total Chats: <code>{total_chats:,}</code>\n"
            f"  • Group Chats: <code>{group_chats:,}</code>\n"
            f"  • Active (7d): <code>{len(active_chats):,}</code>\n\n"
            
            "📚 <b>Content:</b>\n"
            f"  • Filters: <code>{total_filters:,}</code>\n"
            f"  • Notes: <code>{total_notes:,}</code>\n"
            f"  • Blocklists: <code>{total_blocklists:,}</code>\n"
            f"  • Warnings: <code>{total_warnings:,}</code>\n\n"
            
            "🌐 <b>Federations:</b>\n"
            f"  • Total Feds: <code>{total_federations:,}</code>\n\n"
            
            "🔐 <b>Captcha:</b>\n"
            f"  • Pending: <code>{total_captcha_pending:,}</code>\n\n"
            
            "⏰ <b>Scheduled:</b>\n"
            f"  • Actions: <code>{total_scheduled:,}</code>\n\n"
            
            "📝 <b>System:</b>\n"
            f"  • Commands: <code>{total_commands:,}</code>\n"
            f"  • Action Logs: <code>{total_actions:,}</code>\n"
            f"  • Cache Size: <code>{cache_size:,}</code>\n\n"
            
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"⏱️ Generated at {now_utc().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        
        await msg.edit_text(response, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error gathering statistics: {e}")
        await msg.edit_text(f"❌ Error gathering statistics: {str(e)}")

