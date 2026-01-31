"""
Reset welcome message to default
Command: /resetwelcome
"""

from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import require_admin, group_only, log_command
from core.database import Database

COMMAND_INFO = {
    "name": "resetwelcome",
    "aliases": ["resetwel", "clearwelcome"],
    "description": "Reset welcome message to default",
    "usage": "/resetwelcome",
    "category": "greetings",
    "permissions": ["can_change_info"],
    "admin_only": True,
    "group_only": True
}

DEFAULT_WELCOME = "Hey {mention}! Welcome to {chatname}."

@require_admin(permissions=["can_change_info"])
@group_only
@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset welcome message to default"""
    chat_id = str(update.effective_chat.id)
    
    try:
        # Get current chat settings
        chat_settings = await Database.chats.find_one({"_id": chat_id})
        
        if not chat_settings:
            # Initialize chat if not exists
            chat_settings = {
                "_id": chat_id,
                "welcome_enabled": True,
                "welcome_text": DEFAULT_WELCOME,
                "welcome_file_id": None,
                "welcome_file_type": None
            }
            await Database.chats.insert_one(chat_settings)
        else:
            # Reset to default
            await Database.chats.update_one(
                {"_id": chat_id},
                {
                    "$set": {
                        "welcome_text": DEFAULT_WELCOME,
                        "welcome_file_id": None,
                        "welcome_file_type": None
                    }
                }
            )
        
        await update.message.reply_text(
            "✅ Welcome message has been reset to default:\n\n"
            f"<code>{DEFAULT_WELCOME}</code>\n\n"
            "New members will see this message when they join.",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error resetting welcome message: {str(e)}"
        )