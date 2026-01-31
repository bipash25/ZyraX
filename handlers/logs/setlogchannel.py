"""
Set Log Channel by ID command
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timezone

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "setlogchannel",
    "aliases": [],
    "description": "Set log channel by ID",
    "usage": "/setlogchannel <channel_id>",
    "category": "logs"
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set log channel by channel ID"""
    chat_id = update.effective_chat.id
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    if not context.args:
        await update.message.reply_html(
            "❌ <b>Please provide channel ID.</b>\n\n"
            "<b>Usage:</b> /setlogchannel &lt;channel_id&gt;\n\n"
            "To get channel ID:\n"
            "1. Add bot to channel as admin\n"
            "2. Use /id in the channel\n"
            "3. Copy the channel ID"
        )
        return
    
    try:
        log_channel_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid channel ID. Must be a number.")
        return
    
    # Try to send a test message to verify access
    try:
        test_msg = await context.bot.send_message(
            log_channel_id,
            f"✅ Log channel connected to {update.effective_chat.title}\n\n"
            f"Admin actions will now be logged here."
        )
        
        # Update database
        await db.chats.update_one(
            {"_id": str(chat_id)},
            {
                "$set": {
                    "log_channel_id": log_channel_id,
                    "updated_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        
        await update.message.reply_text(
            f"✅ Log channel set successfully!\n\n"
            f"Channel ID: {log_channel_id}\n"
            f"All admin actions will be logged there."
        )
        
        logger.info(f"Log channel {log_channel_id} set for chat {chat_id}")
        
    except Exception as e:
        await update.message.reply_html(
            f"❌ <b>Failed to set log channel.</b>\n\n"
            f"Make sure:\n"
            f"• Bot is admin in the channel\n"
            f"• Channel ID is correct\n"
            f"• Bot has permission to post\n\n"
            f"Error: {str(e)}"
        )
        logger.error(f"Failed to set log channel: {e}")

