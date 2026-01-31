"""
Welcome command - Configure welcome messages for new members
"""
import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command
from utils.message_parser import extract_filter_content

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "welcome",
    "description": "Enable/disable welcome messages for new members",
    "usage": "/welcome <on/off> - Toggle welcome messages\n"
             "/welcome - Show current welcome message\n\n"
             "To set a custom welcome message, use /setwelcome",
    "category": "greetings",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /welcome command
    
    Enable, disable, or show current welcome message.
    """
    chat_id = update.effective_chat.id
    
    db = context.application.bot_data.get('database')
    if db is None:
        await update.message.reply_html("❌ <b>Database connection error</b>")
        return
    
    # Get current settings
    chat_settings = await db.chats.find_one({"_id": str(chat_id)})
    
    if not context.args:
        # Show current settings
        welcome_enabled = chat_settings.get('welcome_enabled', True) if chat_settings else True
        welcome_text = chat_settings.get('welcome_text') if chat_settings else None
        
        status = "✅ Enabled" if welcome_enabled else "❌ Disabled"
        
        response = f"<b>Welcome Message Status:</b> {status}\n\n"
        
        if welcome_text:
            response += f"<b>Current Message:</b>\n{welcome_text[:200]}"
            if len(welcome_text) > 200:
                response += "..."
        else:
            response += "<b>Current Message:</b> Default welcome message\n\n"
            response += "Use <code>/setwelcome</code> to set a custom message."
        
        response += "\n\n<b>Commands:</b>\n"
        response += "• <code>/welcome on</code> - Enable\n"
        response += "• <code>/welcome off</code> - Disable\n"
        response += "• <code>/setwelcome</code> - Set custom message\n"
        response += "• <code>/resetwelcome</code> - Reset to default"
        
        await update.message.reply_html(response)
        return
    
    # Toggle welcome
    arg = context.args[0].lower()
    
    if arg in ['on', 'yes', 'enable', 'true']:
        enabled = True
        action = "enabled"
    elif arg in ['off', 'no', 'disable', 'false']:
        enabled = False
        action = "disabled"
    else:
        await update.message.reply_html(
            "❌ <b>Invalid argument</b>\n\n"
            "Use: <code>/welcome on</code> or <code>/welcome off</code>"
        )
        return
    
    # Update database
    await db.chats.update_one(
        {"_id": str(chat_id)},
        {
            "$set": {
                "welcome_enabled": enabled,
                "updated_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    
    await update.message.reply_html(
        f"✅ <b>Welcome messages {action}</b>"
    )
    
    logger.info(f"Welcome messages {action} in chat {chat_id}")