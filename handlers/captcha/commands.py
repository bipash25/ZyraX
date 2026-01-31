"""
Captcha configuration commands
Supports: /captcha, /setcaptcha, /captchamode
"""
import logging
from utils.time_parser import now_utc
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "captcha",
    "aliases": ["setcaptcha"],
    "description": "Configure captcha verification for new members",
    "usage": "/captcha <on/off> - Enable/disable captcha\n"
             "/captcha - Check current settings",
    "category": "captcha",
    "scope": ["group", "supergroup"]
}

CAPTCHA_MODES = ['math', 'button', 'text']


@log_command
@group_only
@require_admin(permissions=["can_restrict_members"])
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /captcha command
    
    Configure captcha verification for new members.
    
    Args:
        update: Telegram update
        context: PTB context
    """
    chat_id = update.effective_chat.id
    admin_user = update.effective_user
    
    # Get database
    db = context.application.bot_data.get('database')
    if db is None:
        await update.message.reply_html("❌ Database not available")
        return
    
    if not context.args:
        # Show current settings
        try:
            chat_doc = await db.chats.find_one({"_id": str(chat_id)})
            
            if chat_doc and chat_doc.get('captcha_enabled', False):
                mode = chat_doc.get('captcha_mode', 'math')
                timeout = chat_doc.get('captcha_timeout', 120)
                kick_on_fail = chat_doc.get('captcha_kick', False)
                
                message = (
                    f"🔐 <b>Captcha Status: ENABLED</b>\n\n"
                    f"📝 <b>Mode:</b> {mode.title()}\n"
                    f"⏱️ <b>Timeout:</b> {timeout} seconds\n"
                    f"👢 <b>Kick on Fail:</b> {'Yes' if kick_on_fail else 'No'}\n\n"
                    f"💡 Use <code>/captcha off</code> to disable"
                )
            else:
                message = (
                    "🔐 <b>Captcha Status: DISABLED</b>\n\n"
                    "New members can join without verification\n\n"
                    "💡 Use <code>/captcha on</code> to enable"
                )
            
            await update.message.reply_html(message)
            return
            
        except Exception as e:
            logger.error(f"Error checking captcha status in chat {chat_id}: {e}")
            await update.message.reply_html("❌ Failed to check captcha status")
            return
    
    # Parse argument
    arg = context.args[0].lower()
    
    if arg in ['on', 'enable', 'yes', '1']:
        enable = True
    elif arg in ['off', 'disable', 'no', '0']:
        enable = False
    else:
        await update.message.reply_html(
            "❌ <b>Invalid argument</b>\n\n"
            "Usage:\n"
            "• <code>/captcha on</code> - Enable\n"
            "• <code>/captcha off</code> - Disable"
        )
        return
    
    try:
        if enable:
            # Enable captcha with default settings
            await db.chats.update_one(
                {"_id": str(chat_id)},
                {
                    "$set": {
                        "captcha_enabled": True,
                        "captcha_mode": "math",  # Default mode
                        "captcha_timeout": 120,  # 2 minutes
                        "captcha_kick": False
                    }
                },
                upsert=True
            )
            
            await update.message.reply_html(
                f"🔐 <b>Captcha Verification: ENABLED</b>\n\n"
                f"📝 <b>Mode:</b> Math (default)\n"
                f"⏱️ <b>Timeout:</b> 120 seconds\n"
                f"👢 <b>Kick on Fail:</b> No\n\n"
                f"💡 Use <code>/captchamode</code> to change verification type"
            )
            
            logger.info(f"Captcha enabled in chat {chat_id} by {admin_user.id}")
        
        else:
            # Disable captcha
            await db.chats.update_one(
                {"_id": str(chat_id)},
                {"$set": {"captcha_enabled": False}}
            )
            
            await update.message.reply_html(
                "✅ <b>Captcha Verification: DISABLED</b>\n\n"
                "New members can join without verification"
            )
            
            logger.info(f"Captcha disabled in chat {chat_id} by {admin_user.id}")
        
        # Log action
        if db is not None:
            await db.action_logs.insert_one({
                "chat_id": str(chat_id),
                "action_type": f"captcha_{'enable' if enable else 'disable'}",
                "performed_by": str(admin_user.id),
                "timestamp": now_utc()
            })
        
    except Exception as e:
        logger.error(f"Error toggling captcha in chat {chat_id}: {e}")
        await update.message.reply_html(
            "❌ Failed to update captcha settings"
        )