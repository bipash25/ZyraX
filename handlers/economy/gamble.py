"""
Gamble command - 50/50 coin flip bet
"""
import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "gamble",
    "aliases": ["bet"],
    "description": "Gamble coins on a coin flip (50/50)",
    "usage": "/gamble <amount> - Double or nothing!",
    "category": "economy"
}


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gamble coins on coin flip"""
    user = update.effective_user
    message = update.message
    
    db = context.application.bot_data.get('database')
    if not db:
        await message.reply_text("❌ Database not available")
        return
    
    # Get bet amount
    if not context.args:
        await message.reply_html(
            "🎲 <b>Gamble</b>\n\n"
            "Bet coins on a 50/50 coin flip!\n"
            "Win = Double your bet\n"
            "Lose = Lose your bet\n\n"
            "<b>Usage:</b> <code>/gamble &lt;amount&gt;</code>"
        )
        return
    
    try:
        amount = int(context.args[0])
    except ValueError:
        await message.reply_text("❌ Invalid amount! Please provide a number.")
        return
    
    if amount < 10:
        await message.reply_text("❌ Minimum gamble is 10 coins!")
        return
    
    if amount > 50000:
        await message.reply_text("❌ Maximum gamble is 50,000 coins!")
        return
    
    try:
        # Get user balance
        user_doc = await db.users.find_one({"_id": str(user.id)})
        balance = user_doc.get('currency', 0) if user_doc else 0
        
        if balance < amount:
            await message.reply_html(
                f"❌ <b>Insufficient balance!</b>\n\n"
                f"<b>Your balance:</b> {balance:,} 🪙\n"
                f"<b>Gamble amount:</b> {amount:,} 🪙"
            )
            return
        
        # Flip the coin!
        won = random.choice([True, False])
        
        if won:
            # Won - double the bet
            win_amount = amount
            new_balance = balance + win_amount
            
            await db.users.update_one(
                {"_id": str(user.id)},
                {"$set": {"currency": new_balance}}
            )
            
            await message.reply_html(
                f"🎉 <b>You Won!</b>\n\n"
                f"🪙 <b>Bet:</b> {amount:,} 🪙\n"
                f"✨ <b>Won:</b> +{win_amount:,} 🪙\n"
                f"💰 <b>New balance:</b> {new_balance:,} 🪙"
            )
        else:
            # Lost
            new_balance = balance - amount
            
            await db.users.update_one(
                {"_id": str(user.id)},
                {"$set": {"currency": new_balance}}
            )
            
            await message.reply_html(
                f"💸 <b>You Lost!</b>\n\n"
                f"🪙 <b>Bet:</b> {amount:,} 🪙\n"
                f"📉 <b>Lost:</b> -{amount:,} 🪙\n"
                f"💰 <b>New balance:</b> {new_balance:,} 🪙"
            )
        
    except Exception as e:
        logger.error(f"Error in gamble command: {e}", exc_info=True)
        await message.reply_text("❌ Error processing gamble")

