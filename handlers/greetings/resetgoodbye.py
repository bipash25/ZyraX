"""
Reset goodbye message to default
Command: /resetgoodbye
"""

from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import require_admin, group_only, log_command
from core.database import Database

COMMAND_INFO = {
    "name": "resetgoodbye",
    "aliases": ["resetbye", "cleargoodbye"],
    "description": "Reset goodbye message to default",
    "usage": "/resetgoodbye",
    "category": "greetings",
    "permissions": ["can_change_info"],
    "admin_only": True,
    "group_only": True
}

DEFAULT_GOODBYE = "Goodbye {first}! Thanks for being a part of {chatname}."

@require_admin(permissions=["can_change_info"])
@group_only
@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset goodbye message to default"""
    chat_id = str(update.effective_chat.id)
    
    try:
        # Get current chat settings
        chat_settings = await Database.chats.find_one({"_id": chat_id})
        
        if not chat_settings:
            # Initialize chat if not exists
            chat_settings = {
                "_id": chat_id,
                "goodbye_enabled": False,
                "goodbye_text": DEFAULT_GOODBYE,
                "goodbye_file_id": None,
                "goodbye_file_type": None
            }
            await Database.chats.insert_one(chat_settings)
        else:
            # Reset to default
            await Database.chats.update_one(
                {"_id": chat_id},
                {
                    "$set": {
                        "goodbye_text": DEFAULT_GOODBYE,
                        "goodbye_file_id": None,
                        "goodbye_file_type": None
                    }
                }
            )
        
        await update.message.reply_text(
            "✅ Goodbye message has been reset to default:\n\n"
            f"<code>{DEFAULT_GOODBYE}</code>\n\n"
            "Members will see this message when they leave.",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error resetting goodbye message: {str(e)}"
        )