"""
Warn Mode command - Set action when warning limit is reached
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timezone

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "warnmode",
    "aliases": ["setwarnmode"],
    "description": "Set action when warning limit is reached",
    "usage": "/warnmode <ban|kick|mute>",
    "category": "moderation",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_restrict_members"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /warnmode command
    
    Sets the action to take when a user reaches the warning limit
    """
    chat_id = update.effective_chat.id
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Check arguments
    if not context.args:
        # Show current mode
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        current_mode = "ban"
        
        if chat_doc:
            current_mode = chat_doc.get("warn_mode", "ban")
        
        await update.message.reply_html(
            f"⚠️ <b>Current warn mode:</b> {current_mode}\n\n"
            "<b>Available modes:</b>\n"
            "• <code>ban</code> - Ban user permanently\n"
            "• <code>kick</code> - Kick user (can rejoin)\n"
            "• <code>mute</code> - Mute user\n\n"
            "<b>Usage:</b> /warnmode &lt;ban|kick|mute&gt;"
        )
        return
    
    mode = context.args[0].lower()
    valid_modes = ["ban", "kick", "mute"]
    
    if mode not in valid_modes:
        await update.message.reply_html(
            f"❌ Invalid mode: <code>{mode}</code>\n\n"
            "<b>Valid modes:</b> ban, kick, mute"
        )
        return
    
    # Update database
    await db.chats.update_one(
        {"_id": str(chat_id)},
        {
            "$set": {
                "warn_mode": mode,
                "updated_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    
    await update.message.reply_html(
        f"✅ Warn mode set to: <b>{mode}</b>"
    )
    
    logger.info(f"Warn mode set to {mode} in chat {chat_id}")

