"""
Slowmode command - Set chat slowmode
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import require_admin, require_bot_admin, group_only

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "slowmode",
    "aliases": ["slow"],
    "description": "Set slowmode delay (Telegram native)",
    "usage": "/slowmode <seconds> - 0-21600 seconds",
    "category": "admin",
    "permissions": ["can_restrict_members"],
    "admin_only": True,
    "group_only": True
}


@group_only
@require_admin(permissions=["can_restrict_members"])
@require_bot_admin(permissions=["can_restrict_members"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set chat slowmode"""
    message = update.message
    chat = update.effective_chat
    
    if not context.args:
        await message.reply_html(
            "⏱️ <b>Slowmode</b>\n\n"
            "<b>Usage:</b> <code>/slowmode &lt;seconds&gt;</code>\n"
            "<b>Range:</b> 0-21600 seconds (0 to disable)\n\n"
            "<b>Examples:</b>\n"
            "<code>/slowmode 10</code> - 10 seconds\n"
            "<code>/slowmode 60</code> - 1 minute\n"
            "<code>/slowmode 0</code> - Disable"
        )
        return
    
    try:
        seconds = int(context.args[0])
    except ValueError:
        await message.reply_text("❌ Invalid number! Please provide seconds (0-21600)")
        return
    
    if seconds < 0 or seconds > 21600:
        await message.reply_text("❌ Slowmode must be between 0 and 21600 seconds (6 hours)!")
        return
    
    try:
        await chat.set_message_delete_queue_size(seconds)
        
        if seconds == 0:
            await message.reply_html("✅ <b>Slowmode disabled</b>")
        else:
            # Format time nicely
            if seconds >= 3600:
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                time_str = f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
            elif seconds >= 60:
                minutes = seconds // 60
                secs = seconds % 60
                time_str = f"{minutes}m {secs}s" if secs > 0 else f"{minutes}m"
            else:
                time_str = f"{seconds}s"
            
            await message.reply_html(
                f"✅ <b>Slowmode enabled</b>\n\n"
                f"⏱️ <b>Delay:</b> {time_str}\n"
                f"Users must wait {time_str} between messages"
            )
        
    except Exception as e:
        logger.error(f"Error setting slowmode: {e}", exc_info=True)
        
        # Try alternative method
        try:
            from telegram.error import BadRequest
            # Telegram may not support slowmode for this chat type
            await message.reply_text(
                "❌ Error setting slowmode. This may not be supported for this chat type."
            )
        except:
            await message.reply_text("❌ Error setting slowmode")

