"""
Captcha mode command - Set verification type
Supports: /captchamode, /setcaptchamode
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "captchamode",
    "aliases": ["setcaptchamode"],
    "description": "Set captcha verification type",
    "usage": "/captchamode <mode> - Set verification mode\n"
             "Modes: math, button, text",
    "category": "captcha",
    "scope": ["group", "supergroup"]
}

VALID_MODES = ['math', 'button', 'text']


@log_command
@group_only
@require_admin(permissions=["can_restrict_members"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /captchamode command
    
    Set the type of captcha challenge for new members.
    
    Args:
        update: Telegram update
        context: PTB context
    """
    chat_id = update.effective_chat.id
    
    if not context.args:
        # Show current mode
        db = context.application.bot_data.get('database')
        if db is None:
            await update.message.reply_html("❌ Database not available")
            return
        
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        mode = chat_doc.get('captcha_mode', 'math') if chat_doc else 'math'
        
        message = (
            f"📝 <b>Current Captcha Mode:</b> {mode.title()}\n\n"
            f"<b>Available Modes:</b>\n"
            f"• <code>math</code> - Solve simple math problems\n"
            f"• <code>button</code> - Click correct button\n"
            f"• <code>text</code> - Type displayed text\n\n"
            f"💡 Use <code>/captchamode &lt;mode&gt;</code> to change"
        )
        
        await update.message.reply_html(message)
        return
    
    # Parse mode
    mode = context.args[0].lower()
    
    if mode not in VALID_MODES:
        await update.message.reply_html(
            f"❌ <b>Invalid mode:</b> {mode}\n\n"
            f"<b>Valid modes:</b>\n"
            f"• math, button, text"
        )
        return
    
    # Update database
    db = context.application.bot_data.get('database')
    if db is None:
        await update.message.reply_html("❌ Database not available")
        return
    
    try:
        await db.chats.update_one(
            {"_id": str(chat_id)},
            {"$set": {"captcha_mode": mode}},
            upsert=True
        )
        
        mode_descriptions = {
            'math': 'solve simple math problems',
            'button': 'click the correct button',
            'text': 'type the displayed text'
        }
        
        await update.message.reply_html(
            f"✅ <b>Captcha mode updated</b>\n\n"
            f"📝 New members will: <b>{mode_descriptions[mode]}</b>"
        )
        
        logger.info(f"Captcha mode set to {mode} in chat {chat_id}")
        
    except Exception as e:
        logger.error(f"Error setting captcha mode in chat {chat_id}: {e}")
        await update.message.reply_html(
            "❌ Failed to update captcha mode"
        )