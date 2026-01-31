"""
Setbio command - Set profile bio
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "setbio",
    "aliases": ["bio"],
    "description": "Set your profile bio",
    "usage": "/setbio <text> - Max 200 characters",
    "category": "profile"
}

MAX_BIO_LENGTH = 200


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set user bio"""
    user = update.effective_user
    message = update.message
    
    db = context.application.bot_data.get('database')
    if not db:
        await message.reply_text("❌ Database not available")
        return
    
    # Get bio text
    if not context.args:
        await message.reply_html(
            f"📝 <b>Set Bio</b>\n\n"
            f"<b>Usage:</b> <code>/setbio &lt;text&gt;</code>\n"
            f"<b>Max length:</b> {MAX_BIO_LENGTH} characters\n\n"
            f"<b>Example:</b>\n"
            f"<code>/setbio I love coding and gaming! 🎮</code>"
        )
        return
    
    bio = ' '.join(context.args)
    
    if len(bio) > MAX_BIO_LENGTH:
        await message.reply_html(
            f"❌ <b>Bio too long!</b>\n\n"
            f"<b>Your bio:</b> {len(bio)} characters\n"
            f"<b>Maximum:</b> {MAX_BIO_LENGTH} characters"
        )
        return
    
    try:
        # Update bio
        await db.users.update_one(
            {"_id": str(user.id)},
            {
                "$set": {
                    "bio": bio,
                    "username": user.username,
                    "first_name": user.first_name
                }
            },
            upsert=True
        )
        
        await message.reply_html(
            f"✅ <b>Bio updated!</b>\n\n"
            f"<b>Your new bio:</b>\n"
            f"<i>{bio}</i>"
        )
        
    except Exception as e:
        logger.error(f"Error in setbio command: {e}", exc_info=True)
        await message.reply_text("❌ Error setting bio")

