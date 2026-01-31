"""
Start command - Concise welcome message with buttons
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Command metadata for dynamic loader
COMMAND_INFO = {
    "name": "start",
    "aliases": [],
    "description": "Start the bot and get welcome message",
    "usage": "/start",
    "category": "misc",
    "scope": ["private", "group", "supergroup"]
}


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command
    
    Supports deep links:
    - /start rules_{chat_id} - Show rules for a specific chat
    
    Args:
        update: Telegram update
        context: PTB context
    """
    user = update.effective_user
    chat = update.effective_chat
    
    logger.info(f"User {user.id} ({user.first_name}) started bot in {chat.type} chat {chat.id}")
    
    # Check for deep link parameters
    if context.args and len(context.args) > 0:
        param = context.args[0]
        
        # Handle rules deep link
        if param.startswith('rules_'):
            chat_id = param.replace('rules_', '')
            db = context.application.bot_data.get('database')
            
            if db:
                try:
                    # Get chat settings
                    chat_doc = await db.chats.find_one({"_id": chat_id})
                    
                    if chat_doc and chat_doc.get('rules'):
                        rules_text = chat_doc.get('rules')
                        
                        # Try to get chat name
                        try:
                            source_chat = await context.bot.get_chat(int(chat_id))
                            chat_name = source_chat.title
                        except:
                            chat_name = "the chat"
                        
                        message = f"📜 <b>Rules for {chat_name}:</b>\n\n{rules_text}"
                        await update.message.reply_html(message)
                        return
                    else:
                        await update.message.reply_text("❌ No rules found for that chat.")
                        return
                except Exception as e:
                    logger.error(f"Error fetching rules for deep link: {e}")
                    await update.message.reply_text("❌ Error retrieving rules.")
                    return
    
    # Concise welcome message with buttons
    bot_username = context.bot.username
    welcome_message = f"""
👋 <b>Welcome to ZyraX Bot!</b>

Hello {user.mention_html()}! I'm an all-in-one group management bot.

🛡️ <b>Features:</b>
• Moderation & Administration
• Anti-spam Protection (Flood/Raid/Captcha)
• Content Management (Filters/Notes/Rules)
• Federations & Leveling System
• Economy & Fun Commands

<b>Get Started:</b>
• Add me to your group
• Promote me to admin
• Use /help to see all commands
"""
    
    # Create inline keyboard with useful buttons
    keyboard = [
        [
            InlineKeyboardButton("📚 Help & Commands", callback_data="help_main"),
            InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{bot_username}?startgroup=true")
        ],
        [
            InlineKeyboardButton("💬 Support Group", url="https://t.me/ZyraChatOfficial"),  # Replace with actual link
            InlineKeyboardButton("📢 Updates Channel", url="https://t.me/projectZyra")  # Replace with actual link
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_html(welcome_message, reply_markup=reply_markup)
