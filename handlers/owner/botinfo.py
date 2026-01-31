"""
Detailed bot information
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import owner_only, log_command
from utils.time_parser import now_utc
from config import settings

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "botinfo",
    "aliases": ["about", "botdetails"],
    "description": "Get detailed bot information",
    "usage": "/botinfo",
    "category": "owner",
    "scope": ["private"]
}


@log_command
@owner_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Get detailed bot information
    """
    bot = context.bot
    bot_data = context.application.bot_data
    
    # Get bot info
    me = await bot.get_me()
    
    # Get component status
    mtproto = bot_data.get('mtproto_client')
    mtproto_status = "✅ Enabled" if mtproto and mtproto.is_available() else "❌ Disabled"
    
    cache = bot_data.get('cache')
    cache_status = "✅ Enabled" if cache else "❌ Disabled"
    redis_status = "✅ Connected" if cache and cache.redis_enabled else "❌ Not connected"
    
    scheduler = bot_data.get('scheduler')
    scheduler_status = "✅ Running" if scheduler and scheduler.scheduler.running else "❌ Stopped"
    
    db = bot_data.get('database')
    db_status = "✅ Connected" if db else "❌ Not connected"
    
    # Get command count
    command_registry = bot_data.get('command_registry', {})
    command_count = len(command_registry)
    
    response = (
        "🤖 <b>Bot Information</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        f"👤 <b>Bot Details:</b>\n"
        f"  • Name: {me.first_name}\n"
        f"  • Username: @{me.username}\n"
        f"  • ID: <code>{me.id}</code>\n"
        f"  • Version: 2.0.0\n\n"
        
        f"⚙️ <b>Components:</b>\n"
        f"  • Database: {db_status}\n"
        f"  • MTProto: {mtproto_status}\n"
        f"  • Cache: {cache_status}\n"
        f"  • Redis: {redis_status}\n"
        f"  • Scheduler: {scheduler_status}\n\n"
        
        f"📊 <b>Statistics:</b>\n"
        f"  • Commands: {command_count}\n"
        f"  • Owner ID: <code>{settings.OWNER_ID}</code>\n\n"
        
        f"🔧 <b>Configuration:</b>\n"
        f"  • Log Level: {settings.LOG_LEVEL}\n"
        f"  • Rate Limiting: {'✅ Enabled' if settings.RATE_LIMIT_ENABLED else '❌ Disabled'}\n\n"
        
        f"⏰ <b>Server Time:</b> {now_utc().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    
    await update.message.reply_text(response, parse_mode='HTML')

