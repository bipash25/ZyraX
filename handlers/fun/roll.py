"""
Roll command - Roll dice or random numbers
"""
import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "roll",
    "aliases": ["dice", "rand"],
    "description": "Roll dice or generate random numbers",
    "usage": "/roll [max] or /roll [min] [max]",
    "category": "fun"
}


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roll dice or random number"""
    message = update.message
    
    # Default: roll 1d6
    if not context.args:
        result = random.randint(1, 6)
        await message.reply_html(
            f"🎲 <b>Dice Roll</b>\n\n"
            f"You rolled: <b>{result}</b>"
        )
        return
    
    try:
        # Single argument: /roll max (roll 1 to max)
        if len(context.args) == 1:
            max_val = int(context.args[0])
            
            if max_val < 1:
                await message.reply_text("❌ Maximum must be at least 1!")
                return
            
            if max_val > 1000000:
                await message.reply_text("❌ Maximum is too large! (max: 1,000,000)")
                return
            
            result = random.randint(1, max_val)
            
            await message.reply_html(
                f"🎲 <b>Random Number</b>\n\n"
                f"<b>Range:</b> 1 - {max_val:,}\n"
                f"<b>Result:</b> {result:,}"
            )
        
        # Two arguments: /roll min max
        elif len(context.args) == 2:
            min_val = int(context.args[0])
            max_val = int(context.args[1])
            
            if min_val >= max_val:
                await message.reply_text("❌ Minimum must be less than maximum!")
                return
            
            if max_val - min_val > 1000000:
                await message.reply_text("❌ Range is too large! (max: 1,000,000)")
                return
            
            result = random.randint(min_val, max_val)
            
            await message.reply_html(
                f"🎲 <b>Random Number</b>\n\n"
                f"<b>Range:</b> {min_val:,} - {max_val:,}\n"
                f"<b>Result:</b> {result:,}"
            )
        
        else:
            await message.reply_html(
                "❌ <b>Invalid usage!</b>\n\n"
                "<b>Usage:</b>\n"
                "• <code>/roll</code> - Roll 1-6\n"
                "• <code>/roll 100</code> - Roll 1-100\n"
                "• <code>/roll 50 100</code> - Roll 50-100"
            )
    
    except ValueError:
        await message.reply_text("❌ Please provide valid numbers!")

