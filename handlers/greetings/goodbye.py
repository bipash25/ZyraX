"""
Toggle goodbye messages
Command: /goodbye <on/off>
"""

from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import require_admin, group_only, log_command
from core.database import Database

COMMAND_INFO = {
    "name": "goodbye",
    "aliases": ["bye", "farewell", "goodbyes", "byebye"],
    "description": "Toggle goodbye messages on/off",
    "usage": "/goodbye <on/off>",
    "category": "greetings",
    "permissions": ["can_change_info"],
    "admin_only": True,
    "group_only": True
}

@require_admin(permissions=["can_change_info"])
@group_only
@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle goodbye messages"""
    chat_id = str(update.effective_chat.id)
    
    # Check if argument provided
    if not context.args:
        # Show current status
        chat_settings = await Database.chats.find_one({"_id": chat_id})
        
        if not chat_settings or "goodbye_enabled" not in chat_settings:
            status = "disabled"
        else:
            status = "enabled" if chat_settings.get("goodbye_enabled") else "disabled"
        
        await update.message.reply_text(
            f"Goodbye messages are currently <b>{status}</b>.\n\n"
            "Usage: <code>/goodbye on</code> or <code>/goodbye off</code>",
            parse_mode="HTML"
        )
        return
    
    # Parse argument
    arg = context.args[0].lower()
    
    if arg not in ["on", "off", "yes", "no", "true", "false", "enable", "disable"]:
        await update.message.reply_text(
            "❌ Invalid argument. Use:\n"
            "• <code>/goodbye on</code> to enable\n"
            "• <code>/goodbye off</code> to disable",
            parse_mode="HTML"
        )
        return
    
    # Determine new state
    enable = arg in ["on", "yes", "true", "enable"]
    
    try:
        # Get current chat settings
        chat_settings = await Database.chats.find_one({"_id": chat_id})
        
        if not chat_settings:
            # Initialize chat if not exists
            default_goodbye = "Goodbye {first}! Thanks for being a part of {chatname}."
            chat_settings = {
                "_id": chat_id,
                "goodbye_enabled": enable,
                "goodbye_text": default_goodbye,
                "goodbye_file_id": None,
                "goodbye_file_type": None
            }
            await Database.chats.insert_one(chat_settings)
        else:
            # Update existing
            await Database.chats.update_one(
                {"_id": chat_id},
                {"$set": {"goodbye_enabled": enable}}
            )
        
        status = "enabled" if enable else "disabled"
        emoji = "✅" if enable else "🔕"
        
        message = f"{emoji} Goodbye messages have been <b>{status}</b>."
        
        if enable:
            goodbye_text = chat_settings.get("goodbye_text", "Goodbye {first}!")
            message += f"\n\nCurrent goodbye message:\n<code>{goodbye_text}</code>"
            message += "\n\nUse /setgoodbye to customize the message."
        
        await update.message.reply_text(message, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error updating goodbye settings: {str(e)}"
        )