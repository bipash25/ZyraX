"""
Balance command - Check currency balance
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from utils.user_resolver import resolve_user

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "balance",
    "aliases": ["bal", "wallet", "coins"],
    "description": "Check your or another user's balance",
    "usage": "/balance [@user]",
    "category": "economy"
}


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's currency balance"""
    message = update.message
    
    db = context.application.bot_data.get('database')
    if not db:
        await message.reply_text("❌ Database not available")
        return
    
    # Resolve target user
    target_user, _ = await resolve_user(update, context)
    if not target_user:
        target_user = update.effective_user
    
    user_id = target_user.id
    
    try:
        # Get user data
        user_doc = await db.users.find_one({"_id": str(user_id)})
        
        if not user_doc:
            currency = 0
        else:
            currency = user_doc.get('currency', 0)
        
        # Build message
        is_self = user_id == update.effective_user.id
        
        if is_self:
            msg = f"💰 <b>Your Balance</b>\n\n"
            msg += f"<b>Coins:</b> {currency:,} 🪙"
        else:
            msg = f"💰 <b>{target_user.first_name}'s Balance</b>\n\n"
            msg += f"<b>Coins:</b> {currency:,} 🪙"
        
        await message.reply_html(msg)
        
    except Exception as e:
        logger.error(f"Error in balance command: {e}", exc_info=True)
        await message.reply_text("❌ Error retrieving balance")

