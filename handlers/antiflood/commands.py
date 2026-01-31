"""
Antiflood commands - Configure flood protection
Supports: /setflood, /flood, /setfloodmode, /floodmode
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

# Command metadata for /setflood
COMMAND_INFO = {
    "name": "setflood",
    "aliases": ["flood"],
    "description": "Set message flood limit",
    "usage": "/setflood <number> - Set max messages in timeframe\n"
             "/setflood 0 or off - Disable antiflood",
    "category": "antiflood",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_restrict_members"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /setflood and /flood commands
    
    Configure the maximum number of messages a user can send
    in the flood timeframe before action is taken.
    
    Args:
        update: Telegram update
        context: PTB context
    """
    chat_id = update.effective_chat.id
    
    if not context.args:
        # Show current settings
        db = context.application.bot_data.get('database')
        if db is None:
            await update.message.reply_html("❌ Database not available")
            return
        
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        
        if chat_doc and chat_doc.get('flood_limit', 0) > 0:
            flood_limit = chat_doc.get('flood_limit', 10)
            flood_mode = chat_doc.get('flood_mode', 'mute')
            
            message = (
                f"🌊 <b>Antiflood Settings</b>\n\n"
                f"📊 <b>Limit:</b> {flood_limit} messages\n"
                f"⚡ <b>Action:</b> {flood_mode.title()}\n\n"
                f"💡 Use <code>/setflood &lt;number&gt;</code> to change"
            )
        else:
            message = (
                "🌊 <b>Antiflood is currently disabled</b>\n\n"
                "💡 Use <code>/setflood &lt;number&gt;</code> to enable"
            )
        
        await update.message.reply_html(message)
        return
    
    # Parse limit
    limit_str = context.args[0].lower()
    
    if limit_str in ['0', 'off', 'no', 'disable']:
        limit = 0
    else:
        try:
            limit = int(limit_str)
            if limit < 0:
                raise ValueError("Negative number")
            if limit > 200:
                await update.message.reply_html(
                    "❌ Flood limit cannot exceed 200 messages"
                )
                return
        except ValueError:
            await update.message.reply_html(
                "❌ <b>Invalid number.</b>\n\n"
                "Usage: <code>/setflood &lt;number&gt;</code>\n"
                "Or: <code>/setflood off</code>"
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
            {
                "$set": {
                    "flood_limit": limit,
                    "flood_mode": "mute"  # Default mode
                }
            },
            upsert=True
        )
        
        if limit == 0:
            await update.message.reply_html(
                "✅ <b>Antiflood disabled</b>\n\n"
                "Users can send unlimited messages"
            )
        else:
            await update.message.reply_html(
                f"✅ <b>Antiflood configured</b>\n\n"
                f"📊 <b>Limit:</b> {limit} messages\n"
                f"⚡ <b>Action:</b> Mute (default)\n\n"
                f"💡 Use <code>/setfloodmode</code> to change action"
            )
        
        logger.info(f"Antiflood limit set to {limit} in chat {chat_id}")
        
    except Exception as e:
        logger.error(f"Error setting flood limit in chat {chat_id}: {e}")
        await update.message.reply_html(
            "❌ Failed to update antiflood settings"
        )