"""
Rules command - Display chat rules
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.decorators import log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "rules",
    "aliases": [],
    "description": "View chat rules",
    "usage": "/rules - Show the chat rules",
    "category": "rules"
}


@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /rules command
    
    Shows chat rules either in chat or PM based on private_rules setting
    """
    chat = update.effective_chat
    chat_id = chat.id
    user_id = update.effective_user.id
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Get chat settings
    chat_doc = await db.chats.find_one({"_id": str(chat_id)})
    
    if not chat_doc or not chat_doc.get('rules'):
        await update.message.reply_html(
            "❌ <b>No rules have been set for this chat.</b>\n\n"
            "Admins can set rules using /setrules"
        )
        return
    
    rules_text = chat_doc.get('rules')
    private_rules = chat_doc.get('private_rules', False)
    rules_button_text = chat_doc.get('rules_button', 'Rules')
    
    # If private rules and in group, send button to PM
    if private_rules and chat.type in ['group', 'supergroup']:
        keyboard = [
            [InlineKeyboardButton(
                text=f"📜 {rules_button_text}",
                url=f"t.me/{context.bot.username}?start=rules_{chat_id}"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Click the button below to view the rules in private:",
            reply_markup=reply_markup
        )
    else:
        # Send rules in chat/PM
        message = f"📜 <b>Rules for {chat.title or 'this chat'}:</b>\n\n"
        message += rules_text
        
        await update.message.reply_html(message)
    
    logger.debug(f"Rules requested for chat {chat_id}")

