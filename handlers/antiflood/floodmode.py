"""
Flood mode command - Set action for flood violators
Supports: /setfloodmode, /floodmode
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "setfloodmode",
    "aliases": ["floodmode"],
    "description": "Set action for flood violators",
    "usage": "/setfloodmode <mode> - Set flood action\n"
             "Modes: ban, mute, kick, tban, tmute",
    "category": "antiflood",
    "scope": ["group", "supergroup"]
}

VALID_MODES = ['ban', 'mute', 'kick', 'tban', 'tmute']


@log_command
@group_only
@require_admin(permissions=["can_restrict_members"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /setfloodmode and /floodmode commands
    
    Set what action should be taken when a user floods.
    
    Args:
        update: Telegram update
        context: PTB context
    """
    chat_id = update.effective_chat.id
    
    if not context.args:
        # Show current mode
        db = context.application.bot_data.get('database')
        if db is None:
            await update.message.reply_html("❌ Database not available")
            return
        
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        flood_mode = chat_doc.get('flood_mode', 'mute') if chat_doc else 'mute'
        
        message = (
            f"⚡ <b>Current Flood Action:</b> {flood_mode.title()}\n\n"
            f"<b>Available Modes:</b>\n"
            f"• <code>ban</code> - Permanently ban\n"
            f"• <code>mute</code> - Permanently mute\n"
            f"• <code>kick</code> - Kick from group\n"
            f"• <code>tban</code> - Temporary ban\n"
            f"• <code>tmute</code> - Temporary mute\n\n"
            f"💡 Use <code>/setfloodmode &lt;mode&gt;</code> to change"
        )
        
        await update.message.reply_html(message)
        return
    
    # Parse mode
    mode = context.args[0].lower()
    
    if mode not in VALID_MODES:
        await update.message.reply_html(
            f"❌ <b>Invalid mode:</b> {mode}\n\n"
            f"<b>Valid modes:</b>\n"
            f"• ban, mute, kick, tban, tmute"
        )
        return
    
    # Update database
    db = context.application.bot_data.get('database')
    if db is None:
        await update.message.reply_html("❌ Database not available")
        return
    
    try:
        await db.chats.update_one(
            {"_id": str(chat_id)},
            {"$set": {"flood_mode": mode}},
            upsert=True
        )
        
        await update.message.reply_html(
            f"✅ <b>Flood action updated</b>\n\n"
            f"⚡ Violators will be: <b>{mode.upper()}</b>"
        )
        
        logger.info(f"Flood mode set to {mode} in chat {chat_id}")
        
    except Exception as e:
        logger.error(f"Error setting flood mode in chat {chat_id}: {e}")
        await update.message.reply_html(
            "❌ Failed to update flood mode"
        )