"""
Antiraid commands - Protect against mass join attacks
Supports: /antiraid, /raidmode, /setantiraid
"""
import logging
from datetime import datetime, timezone, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "antiraid",
    "aliases": ["setantiraid", "raidmode"],
    "description": "Configure antiraid protection",
    "usage": "/antiraid <on/off> - Enable/disable raid protection\n"
             "/antiraid - Check current status",
    "category": "antiraid",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_restrict_members"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /antiraid command
    
    Enable or disable antiraid mode. When enabled, new members
    are automatically muted until manually approved by admins.
    
    Args:
        update: Telegram update
        context: PTB context
    """
    chat_id = update.effective_chat.id
    admin_user = update.effective_user
    
    # Get database
    db = context.application.bot_data.get('database')
    if db is None:
        await update.message.reply_html("❌ Database not available")
        return
    
    if not context.args:
        # Show current status
        try:
            chat_doc = await db.chats.find_one({"_id": str(chat_id)})
            
            if chat_doc and chat_doc.get('antiraid_enabled', False):
                expires = chat_doc.get('antiraid_expires')
                
                message = "🛡️ <b>Antiraid Status: ACTIVE</b>\n\n"
                message += "🔒 New members are being automatically restricted\n"
                
                if expires:
                    remaining = (expires - datetime.now(timezone.utc)).total_seconds()
                    if remaining > 0:
                        hours = int(remaining // 3600)
                        minutes = int((remaining % 3600) // 60)
                        message += f"⏱️ Auto-disable in: {hours}h {minutes}m\n"
                
                message += "\n💡 Use <code>/antiraid off</code> to disable"
            else:
                message = (
                    "🛡️ <b>Antiraid Status: INACTIVE</b>\n\n"
                    "✅ New members can join normally\n\n"
                    "💡 Use <code>/antiraid on</code> to enable protection"
                )
            
            await update.message.reply_html(message)
            return
            
        except Exception as e:
            logger.error(f"Error checking antiraid status in chat {chat_id}: {e}")
            await update.message.reply_html("❌ Failed to check antiraid status")
            return
    
    # Parse argument
    arg = context.args[0].lower()
    
    if arg in ['on', 'enable', 'yes', '1']:
        enable = True
    elif arg in ['off', 'disable', 'no', '0']:
        enable = False
    else:
        await update.message.reply_html(
            "❌ <b>Invalid argument</b>\n\n"
            "Usage:\n"
            "• <code>/antiraid on</code> - Enable\n"
            "• <code>/antiraid off</code> - Disable"
        )
        return
    
    # Get duration if enabling (default 6 hours)
    duration_hours = 6
    if enable and len(context.args) > 1:
        try:
            duration_hours = int(context.args[1])
            if duration_hours < 1 or duration_hours > 168:  # Max 1 week
                await update.message.reply_html(
                    "❌ Duration must be between 1 and 168 hours (1 week)"
                )
                return
        except ValueError:
            await update.message.reply_html(
                "❌ Invalid duration. Use number of hours."
            )
            return
    
    try:
        if enable:
            # Enable antiraid with expiry
            expires = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
            
            await db.chats.update_one(
                {"_id": str(chat_id)},
                {
                    "$set": {
                        "antiraid_enabled": True,
                        "antiraid_expires": expires,
                        "antiraid_activated_by": str(admin_user.id),
                        "antiraid_activated_at": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
            
            # Schedule auto-disable
            scheduler = context.application.bot_data.get('scheduler')
            if scheduler:
                await scheduler.schedule_action(
                    chat_id=chat_id,
                    action_type='disable_antiraid',
                    execute_at=expires
                )
            
            await update.message.reply_html(
                f"🛡️ <b>Antiraid Mode: ACTIVATED</b>\n\n"
                f"🔒 New members will be automatically restricted\n"
                f"⏱️ Auto-disable in: {duration_hours} hours\n\n"
                f"💡 Admins can manually approve users with /approve"
            )
            
            logger.info(
                f"Antiraid enabled in chat {chat_id} by {admin_user.id} "
                f"for {duration_hours} hours"
            )
        
        else:
            # Disable antiraid
            result = await db.chats.update_one(
                {"_id": str(chat_id)},
                {
                    "$set": {
                        "antiraid_enabled": False
                    },
                    "$unset": {
                        "antiraid_expires": ""
                    }
                }
            )
            
            # Cancel scheduled auto-disable
            scheduler = context.application.bot_data.get('scheduler')
            if scheduler:
                await scheduler.cancel_action(chat_id, 'disable_antiraid')
            
            await update.message.reply_html(
                "✅ <b>Antiraid Mode: DEACTIVATED</b>\n\n"
                "🔓 New members can join normally"
            )
            
            logger.info(f"Antiraid disabled in chat {chat_id} by {admin_user.id}")
        
        # Log action
        if db is not None:
            await db.action_logs.insert_one({
                "chat_id": str(chat_id),
                "action_type": f"antiraid_{'enable' if enable else 'disable'}",
                "performed_by": str(admin_user.id),
                "metadata": {
                    "duration_hours": duration_hours if enable else None
                },
                "timestamp": datetime.now(timezone.utc)
            })
        
    except Exception as e:
        logger.error(f"Error toggling antiraid in chat {chat_id}: {e}")
        await update.message.reply_html(
            "❌ Failed to update antiraid settings"
        )