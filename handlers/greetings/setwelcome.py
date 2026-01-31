"""
Setwelcome command - Set custom welcome message
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
    "name": "setwelcome",
    "aliases": ["setwelcomemsg", "welcomemsg"],
    "description": "Set a custom welcome message for new members",
    "usage": "/setwelcome - Reply to a message to set it as welcome\n\n"
             "<b>Supported variables:</b>\n"
             "• {first} - User's first name\n"
             "• {last} - User's last name\n"
             "• {fullname} - Full name\n"
             "• {username} - Username with @\n"
             "• {mention} - Mention user\n"
             "• {id} - User ID\n"
             "• {chatname} - Chat name\n"
             "• {count} - Member count\n\n"
             "<b>Buttons:</b> [Text](buttonurl://url)",
    "category": "greetings",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /setwelcome command
    
    Set a custom welcome message for new members.
    """
    chat_id = update.effective_chat.id
    
    # Must be a reply to set the content
    if not update.message.reply_to_message:
        await update.message.reply_html(
            "❌ <b>Reply to a message to set it as welcome</b>\n\n"
            "<b>How to use:</b>\n"
            "1. Type your welcome message\n"
            "2. Reply to it with <code>/setwelcome</code>\n\n"
            "<b>Tip:</b> Use variables like {mention}, {chatname}, {count}"
        )
        return
    
    reply_msg = update.message.reply_to_message
    
    # Extract content from reply
    content = extract_filter_content(reply_msg)
    
    # Validate content
    if not content['text'] and not content['file_id']:
        await update.message.reply_html(
            "❌ <b>Reply message must contain text or media</b>"
        )
        return
    
    # Save welcome message to database
    db = context.application.bot_data.get('database')
    if db is not None:
        await db.chats.update_one(
            {"_id": str(chat_id)},
            {
                "$set": {
                    "welcome_enabled": True,
                    "welcome_text": content['text'],
                    "welcome_file_id": content['file_id'],
                    "welcome_file_type": content['file_type'],
                    "updated_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        
        response = "✅ <b>Welcome message set</b>\n\n"
        
        if content['text']:
            preview = content['text'][:150]
            if len(content['text']) > 150:
                preview += "..."
            response += f"<b>Preview:</b>\n{preview}\n\n"
        
        if content['file_id']:
            response += f"<b>Media Type:</b> {content['file_type']}\n\n"
        
        response += "<b>Commands:</b>\n"
        response += "• <code>/welcome off</code> - Disable\n"
        response += "• <code>/resetwelcome</code> - Reset to default"
        
        await update.message.reply_html(response)
        
        logger.info(f"Welcome message set in chat {chat_id}")
    else:
        await update.message.reply_html(
            "❌ <b>Database connection error</b>"
        )