"""
Auto-delete welcome messages
Command: /cleanwelcome <on/off>
"""

from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import require_admin, group_only, log_command
from core.database import Database

COMMAND_INFO = {
    "name": "cleanwelcome",
    "aliases": ["cwelcome", "cleanwelcomes"],
    "description": "Auto-delete welcome messages after 5 minutes",
    "usage": "/cleanwelcome <on/off>",
    "category": "greetings",
    "permissions": ["can_delete_messages"],
    "admin_only": True,
    "group_only": True
}

@require_admin(permissions=["can_delete_messages"])
@group_only
@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle auto-deletion of welcome messages"""
    chat_id = str(update.effective_chat.id)
    
    # Check if argument provided
    if not context.args:
        # Show current status
        chat_settings = await Database.chats.find_one({"_id": chat_id})
        
        if not chat_settings or "clean_welcome" not in chat_settings:
            status = "disabled"
        else:
            status = "enabled" if chat_settings.get("clean_welcome") else "disabled"
        
        await update.message.reply_text(
            f"Clean welcome is currently <b>{status}</b>.\n\n"
            "Usage: <code>/cleanwelcome on</code> or <code>/cleanwelcome off</code>\n\n"
            "When enabled, welcome messages will be automatically deleted after 5 minutes.",
            parse_mode="HTML"
        )
        return
    
    # Parse argument
    arg = context.args[0].lower()
    
    if arg not in ["on", "off", "yes", "no", "true", "false", "enable", "disable"]:
        await update.message.reply_text(
            "❌ Invalid argument. Use:\n"
            "• <code>/cleanwelcome on</code> to enable\n"
            "• <code>/cleanwelcome off</code> to disable",
            parse_mode="HTML"
        )
        return
    
    # Determine new state
    enable = arg in ["on", "yes", "true", "enable"]
    
    try:
        # Update database
        await Database.chats.update_one(
            {"_id": chat_id},
            {"$set": {"clean_welcome": enable}},
            upsert=True
        )
        
        status = "enabled" if enable else "disabled"
        emoji = "✅" if enable else "🔕"
        
        message = f"{emoji} Clean welcome has been <b>{status}</b>."
        
        if enable:
            message += "\n\n🗑️ Welcome messages will be automatically deleted after 5 minutes."
        
        await update.message.reply_text(message, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error updating clean welcome settings: {str(e)}"
        )