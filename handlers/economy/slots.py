"""
Slots command - Slot machine gambling
"""
import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "slots",
    "aliases": ["slot"],
    "description": "Play the slot machine",
    "usage": "/slots <bet> - Bet coins to play",
    "category": "economy"
}

# Slot symbols
SYMBOLS = ["🍒", "🍋", "🍊", "🍇", "7️⃣", "💎"]
WEIGHTS = [30, 25, 20, 15, 7, 3]  # Probability weights

# Payouts
PAYOUTS = {
    "🍒": 2,   # 2x
    "🍋": 3,   # 3x
    "🍊": 4,   # 4x
    "🍇": 5,   # 5x
    "7️⃣": 10,  # 10x
    "💎": 20   # 20x (jackpot!)
}


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Play slot machine"""
    user = update.effective_user
    message = update.message
    
    db = context.application.bot_data.get('database')
    if not db:
        await message.reply_text("❌ Database not available")
        return
    
    # Get bet amount
    if not context.args:
        await message.reply_html(
            "🎰 <b>Slot Machine</b>\n\n"
            "Place your bet and spin!\n\n"
            "<b>Usage:</b> <code>/slots &lt;bet&gt;</code>\n"
            "<b>Example:</b> <code>/slots 100</code>\n\n"
            "<b>Payouts:</b>\n"
            "🍒 2x | 🍋 3x | 🍊 4x\n"
            "🍇 5x | 7️⃣ 10x | 💎 20x"
        )
        return
    
    try:
        bet = int(context.args[0])
    except ValueError:
        await message.reply_text("❌ Invalid bet! Please provide a number.")
        return
    
    if bet < 10:
        await message.reply_text("❌ Minimum bet is 10 coins!")
        return
    
    if bet > 10000:
        await message.reply_text("❌ Maximum bet is 10,000 coins!")
        return
    
    try:
        # Get user balance
        user_doc = await db.users.find_one({"_id": str(user.id)})
        balance = user_doc.get('currency', 0) if user_doc else 0
        
        if balance < bet:
            await message.reply_html(
                f"❌ <b>Insufficient balance!</b>\n\n"
                f"<b>Your balance:</b> {balance:,} 🪙\n"
                f"<b>Bet amount:</b> {bet:,} 🪙"
            )
            return
        
        # Spin the slots!
        slots = random.choices(SYMBOLS, weights=WEIGHTS, k=3)
        
        # Check for wins
        win_amount = 0
        if slots[0] == slots[1] == slots[2]:
            # All three match!
            multiplier = PAYOUTS[slots[0]]
            win_amount = bet * multiplier
        elif slots[0] == slots[1] or slots[1] == slots[2]:
            # Two match
            win_amount = bet
        
        # Calculate net
        net = win_amount - bet
        new_balance = balance + net
        
        # Update balance
        await db.users.update_one(
            {"_id": str(user.id)},
            {"$set": {"currency": new_balance}},
            upsert=True
        )
        
        # Build message
        msg = f"🎰 <b>Slot Machine</b>\n\n"
        msg += f"[ {slots[0]} | {slots[1]} | {slots[2]} ]\n\n"
        
        if net > 0:
            if slots[0] == slots[1] == slots[2]:
                msg += f"🎉 <b>JACKPOT!</b>\n"
                msg += f"✨ <b>Win:</b> {win_amount:,} 🪙 ({PAYOUTS[slots[0]]}x)\n"
            else:
                msg += f"🎊 <b>You won!</b>\n"
                msg += f"✨ <b>Win:</b> {win_amount:,} 🪙\n"
            msg += f"📈 <b>Profit:</b> +{net:,} 🪙\n"
        elif net == 0:
            msg += f"😐 <b>Push!</b> Bet returned.\n"
        else:
            msg += f"💸 <b>You lost!</b>\n"
            msg += f"📉 <b>Loss:</b> {net:,} 🪙\n"
        
        msg += f"\n<b>New balance:</b> {new_balance:,} 🪙"
        
        await message.reply_html(msg)
        
    except Exception as e:
        logger.error(f"Error in slots command: {e}", exc_info=True)
        await message.reply_text("❌ Error playing slots")

