"""
Set custom goodbye message
Command: /setgoodbye <reply to message or text>
"""

from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import require_admin, group_only, log_command
from core.database import Database
from utils.message_parser import extract_filter_content

COMMAND_INFO = {
    "name": "setgoodbye",
    "aliases": ["setbye", "goodbyemsg", "byemsg"],
    "description": "Set a custom goodbye message",
    "usage": "/setgoodbye <text> or reply to a message",
    "category": "greetings",
    "permissions": ["can_change_info"],
    "admin_only": True,
    "group_only": True
}

@require_admin(permissions=["can_change_info"])
@group_only
@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set custom goodbye message"""
    chat_id = str(update.effective_chat.id)
    message = update.message
    
    # Extract goodbye content
    goodbye_text = None
    file_id = None
    file_type = None
    
    if message.reply_to_message:
        # Get content from replied message
        replied_msg = message.reply_to_message
        goodbye_text = replied_msg.text or replied_msg.caption or ""
        
        # Extract media if present
        media_info = extract_filter_content(replied_msg)
        if media_info:
            file_id = media_info.get("file_id")
            file_type = media_info.get("type")
    
    elif context.args:
        # Get content from command arguments
        goodbye_text = " ".join(context.args)
    
    else:
        # No content provided
        await message.reply_text(
            "❌ Please provide a goodbye message.\n\n"
            "<b>Usage:</b>\n"
            "• <code>/setgoodbye Your goodbye text here</code>\n"
            "• Reply to a message with <code>/setgoodbye</code>\n\n"
            "<b>Available variables:</b>\n"
            "• {first} - User's first name\n"
            "• {last} - User's last name\n"
            "• {fullname} - User's full name\n"
            "• {username} - User's username\n"
            "• {mention} - Mention the user\n"
            "• {id} - User's ID\n"
            "• {chatname} - Chat name\n"
            "• {count} - Total members\n\n"
            "<b>Buttons:</b>\n"
            "Use <code>[Button Text](buttonurl://example.com)</code>\n"
            "Add <code>:same</code> to put buttons in the same row",
            parse_mode="HTML"
        )
        return
    
    # Validate content
    if not goodbye_text and not file_id:
        await message.reply_text(
            "❌ Goodbye message cannot be empty."
        )
        return
    
    if len(goodbye_text) > 4096:
        await message.reply_text(
            "❌ Goodbye message is too long. Maximum 4096 characters."
        )
        return
    
    try:
        # Get database from context
        db = context.application.bot_data.get('database')
        if not db:
            await message.reply_text("❌ Database not available")
            return
        
        # Update database
        await db.chats.update_one(
            {"_id": chat_id},
            {
                "$set": {
                    "goodbye_text": goodbye_text,
                    "goodbye_file_id": file_id,
                    "goodbye_file_type": file_type,
                    "goodbye_enabled": True  # Auto-enable when setting
                }
            },
            upsert=True
        )
        
        # Prepare confirmation message
        response = "✅ Goodbye message has been set!\n\n"
        
        if file_type:
            response += f"📎 Media type: {file_type}\n"
        
        if goodbye_text:
            preview = goodbye_text[:200] + "..." if len(goodbye_text) > 200 else goodbye_text
            response += f"\n<b>Preview:</b>\n<code>{preview}</code>\n"
        
        response += "\n💡 Members will see this when they leave the chat."
        
        await message.reply_text(response, parse_mode="HTML")
        
    except Exception as e:
        await message.reply_text(
            f"❌ Error setting goodbye message: {str(e)}"
        )