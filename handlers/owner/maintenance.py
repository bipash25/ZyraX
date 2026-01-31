"""
Enable/disable maintenance mode
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import owner_only, log_command
from utils.time_parser import now_utc

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "maintenance",
    "aliases": ["maint"],
    "description": "Enable/disable maintenance mode",
    "usage": "/maintenance <on|off> [reason]",
    "category": "owner",
    "scope": ["private"]
}


@log_command
@owner_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Enable or disable maintenance mode
    """
    db = context.application.bot_data.get('database')
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    if not context.args:
        # Check current status
        try:
            config = await db.get_collection('config').find_one({"_id": "maintenance"})
            if config and config.get('enabled', False):
                reason = config.get('reason', 'No reason provided')
                since = config.get('enabled_at', 'Unknown')
                await update.message.reply_html(
                    f"🔧 <b>Maintenance Mode: ACTIVE</b>\n\n"
                    f"Reason: {reason}\n"
                    f"Since: {since}\n\n"
                    f"Use <code>/maintenance off</code> to disable"
                )
            else:
                await update.message.reply_html(
                    f"✅ <b>Maintenance Mode: INACTIVE</b>\n\n"
                    f"Use <code>/maintenance on [reason]</code> to enable"
                )
            return
        except Exception as e:
            logger.error(f"Error checking maintenance status: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
            return
    
    action = context.args[0].lower()
    if action not in ['on', 'off', 'enable', 'disable']:
        await update.message.reply_text("❌ Invalid action. Use: on or off")
        return
    
    enable = action in ['on', 'enable']
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Scheduled maintenance"
    
    try:
        if enable:
            await db.get_collection('config').update_one(
                {"_id": "maintenance"},
                {
                    "$set": {
                        "enabled": True,
                        "reason": reason,
                        "enabled_at": now_utc().strftime('%Y-%m-%d %H:%M:%S UTC'),
                        "enabled_by": str(update.effective_user.id)
                    }
                },
                upsert=True
            )
            
            await update.message.reply_html(
                f"🔧 <b>Maintenance Mode: ENABLED</b>\n\n"
                f"Reason: {reason}\n\n"
                f"⚠️ Non-owner commands will be blocked"
            )
        else:
            await db.get_collection('config').update_one(
                {"_id": "maintenance"},
                {"$set": {"enabled": False}},
                upsert=True
            )
            
            await update.message.reply_html(
                f"✅ <b>Maintenance Mode: DISABLED</b>\n\n"
                f"Bot is now fully operational"
            )
        
        logger.info(f"Maintenance mode {'enabled' if enable else 'disabled'} by owner")
        
    except Exception as e:
        logger.error(f"Error toggling maintenance mode: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

