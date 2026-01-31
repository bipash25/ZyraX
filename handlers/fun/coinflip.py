"""
Coin flip command - Heads or tails
"""
import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "coinflip",
    "aliases": ["flip", "coin"],
    "description": "Flip a coin - heads or tails",
    "usage": "/coinflip",
    "category": "fun"
}


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Flip a coin"""
    message = update.message
    
    result = random.choice(["Heads", "Tails"])
    emoji = "🟡" if result == "Heads" else "⚪"
    
    await message.reply_html(
        f"🪙 <b>Coin Flip</b>\n\n"
        f"{emoji} You got <b>{result}</b>!"
    )

