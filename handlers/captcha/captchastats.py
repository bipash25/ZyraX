"""
View captcha statistics
Command: /captchastats
"""

from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import require_admin, group_only, log_command
from datetime import timedelta
from utils.time_parser import now_utc
import logging

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "captchastats",
    "aliases": ["captcha_stats", "captcha_statistics"],
    "description": "View captcha statistics",
    "usage": "/captchastats",
    "category": "captcha",
    "permissions": ["can_restrict_members"],
    "admin_only": True,
    "group_only": True
}

@require_admin(permissions=["can_restrict_members"])
@group_only
@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View captcha statistics"""
    chat_id = str(update.effective_chat.id)
    message = update.message
    
    try:
        # Get database
        db = context.application.bot_data.get('database')
        if not db:
            await message.reply_text("❌ Database not available")
            return
        
        # Get chat settings
        chat_settings = await db.chats.find_one({"_id": chat_id})
        
        if not chat_settings:
            await message.reply_text(
                "ℹ️ No captcha data available for this chat."
            )
            return
        
        captcha_enabled = chat_settings.get("captcha_enabled", False)
        captcha_mode = chat_settings.get("captcha_mode", "button")
        whitelist = chat_settings.get("captcha_whitelist", [])
        
        # Get current pending users
        pending_count = await db.captcha_pending.count_documents({"chat_id": chat_id})
        
        # Get statistics from action logs
        # Last 30 days
        thirty_days_ago = now_utc() - timedelta(days=30)
        
        # Count manual verifications
        manual_verifies = await db.action_logs.count_documents({
            "chat_id": chat_id,
            "action_type": "manual_verify",
            "timestamp": {"$gte": thirty_days_ago}
        })
        
        # Count successful captcha completions (from last 30 days)
        # We'll count by checking captcha_pending entries that were removed
        # This is an approximation
        
        # Count kicks due to captcha failure
        captcha_kicks = await db.action_logs.count_documents({
            "chat_id": chat_id,
            "action_type": {"$in": ["captcha_timeout", "captcha_failed"]},
            "timestamp": {"$gte": thirty_days_ago}
        })
        
        # Count rate limit violations
        rate_limit_bans = await db.action_logs.count_documents({
            "chat_id": chat_id,
            "action_type": "rate_limit_ban",
            "timestamp": {"$gte": thirty_days_ago}
        })
        
        # Get whitelist count
        whitelist_count = len(whitelist)
        
        # Calculate approximate success rate
        # Total verifications = manual + (estimated successful automated)
        # We can estimate successful by checking recent joins that aren't in logs
        
        # Build statistics message
        status_emoji = "✅" if captcha_enabled else "🔕"
        mode_emoji = {
            "text": "📝",
            "math": "🔢",
            "button": "🔘"
        }.get(captcha_mode, "❓")
        
        stats_message = (
            f"📊 <b>Captcha Statistics</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{status_emoji} <b>Status:</b> {'Enabled' if captcha_enabled else 'Disabled'}\n"
            f"{mode_emoji} <b>Mode:</b> {captcha_mode.title()}\n"
            f"👥 <b>Currently Pending:</b> {pending_count}\n"
            f"⚪ <b>Whitelisted Users:</b> {whitelist_count}\n\n"
            f"<b>📈 Last 30 Days:</b>\n"
            f"• Manual Verifications: {manual_verifies}\n"
            f"• Captcha Failures/Timeouts: {captcha_kicks}\n"
            f"• Rate Limit Bans: {rate_limit_bans}\n"
        )
        
        # Add rate limit info
        if chat_settings.get("captcha_rate_limit"):
            rate_config = chat_settings.get("captcha_rate_limit", {})
            max_joins = rate_config.get("max_joins", 3)
            time_window = rate_config.get("time_window", 300)
            stats_message += f"\n<b>⚙️ Rate Limit:</b> {max_joins} joins per {time_window//60} minutes"
        
        # Add timeout info
        captcha_kick_time = chat_settings.get("captcha_kick_time", 0)
        if captcha_kick_time > 0:
            minutes = captcha_kick_time // 60
            stats_message += f"\n<b>⏱️ Timeout:</b> {minutes} minutes"
        else:
            stats_message += "\n<b>⏱️ Timeout:</b> Disabled (users stay muted)"
        
        # Add attempt limit info
        stats_message += "\n<b>🎯 Max Attempts:</b> 3 (then kicked)"
        
        await message.reply_text(stats_message, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in captchastats command: {e}")
        await message.reply_text(
            f"❌ Error fetching statistics: {str(e)}"
        )