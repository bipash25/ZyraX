"""
Warn Limit command - Set warning limit before action
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timezone

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "warnlimit",
    "aliases": ["setwarnlimit", "maxwarns"],
    "description": "Set warning limit before action is taken",
    "usage": "/warnlimit <number>",
    "category": "moderation",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_restrict_members"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /warnlimit command
    
    Sets the number of warnings before action is taken
    """
    chat_id = update.effective_chat.id
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Check arguments
    if not context.args:
        # Show current limit
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        current_limit = 3
        
        if chat_doc:
            current_limit = chat_doc.get("warn_limit", 3)
        
        await update.message.reply_html(
            f"⚠️ <b>Current warn limit:</b> {current_limit}\n\n"
            "<b>Usage:</b> /warnlimit &lt;number&gt;\n"
            "Set the number of warnings before action is taken."
        )
        return
    
    try:
        limit = int(context.args[0])
        
        if limit < 1:
            await update.message.reply_text("❌ Warning limit must be at least 1")
            return
        
        if limit > 50:
            await update.message.reply_text("❌ Warning limit cannot exceed 50")
            return
        
    except ValueError:
        await update.message.reply_text("❌ Invalid number. Please provide a valid integer.")
        return
    
    # Update database
    await db.chats.update_one(
        {"_id": str(chat_id)},
        {
            "$set": {
                "warn_limit": limit,
                "updated_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    
    await update.message.reply_html(
        f"✅ Warning limit set to: <b>{limit}</b>"
    )
    
    logger.info(f"Warning limit set to {limit} in chat {chat_id}")

