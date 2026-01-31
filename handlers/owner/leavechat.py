"""
Make bot leave a specific chat
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import owner_only, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "leavechat",
    "aliases": ["leave"],
    "description": "Make bot leave a specific chat",
    "usage": "/leavechat <chat_id>",
    "category": "owner",
    "scope": ["private"]
}


@log_command
@owner_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Make bot leave a specific chat
    """
    if not context.args:
        await update.message.reply_html(
            "❌ <b>Please provide a chat ID</b>\n\n"
            "<b>Usage:</b> /leavechat &lt;chat_id&gt;\n\n"
            "Tip: Use /chatlist to get chat IDs"
        )
        return
    
    try:
        chat_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid chat ID")
        return
    
    try:
        # Get chat info
        chat = await context.bot.get_chat(chat_id)
        chat_name = chat.title or f"Chat {chat_id}"
        
        # Leave chat
        await context.bot.leave_chat(chat_id)
        
        await update.message.reply_html(
            f"✅ <b>Left chat:</b>\n"
            f"{chat_name}\n"
            f"<code>{chat_id}</code>"
        )
        
        logger.info(f"Bot left chat {chat_id} ({chat_name}) by owner command")
        
    except Exception as e:
        logger.error(f"Error leaving chat {chat_id}: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

