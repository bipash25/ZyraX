"""
RPS command - Rock Paper Scissors game
"""
import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "rps",
    "aliases": ["rockpaperscissors"],
    "description": "Play Rock Paper Scissors",
    "usage": "/rps <rock/paper/scissors>",
    "category": "fun"
}

CHOICES = ['rock', 'paper', 'scissors']
EMOJIS = {
    'rock': '🪨',
    'paper': '📄',
    'scissors': '✂️'
}


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Play rock paper scissors"""
    message = update.message
    
    if not context.args:
        await message.reply_html(
            "🎮 <b>Rock Paper Scissors</b>\n\n"
            "<b>Usage:</b> <code>/rps &lt;choice&gt;</code>\n\n"
            "<b>Choices:</b> rock, paper, scissors\n"
            "🪨 Rock beats ✂️ Scissors\n"
            "📄 Paper beats 🪨 Rock\n"
            "✂️ Scissors beats 📄 Paper"
        )
        return
    
    user_choice = context.args[0].lower()
    
    # Validate choice
    if user_choice not in CHOICES:
        await message.reply_text(
            f"❌ Invalid choice! Choose: rock, paper, or scissors"
        )
        return
    
    # Bot chooses
    bot_choice = random.choice(CHOICES)
    
    # Determine winner
    if user_choice == bot_choice:
        result = "🤝 It's a tie!"
        outcome = "tie"
    elif (
        (user_choice == 'rock' and bot_choice == 'scissors') or
        (user_choice == 'paper' and bot_choice == 'rock') or
        (user_choice == 'scissors' and bot_choice == 'paper')
    ):
        result = "🎉 You won!"
        outcome = "win"
    else:
        result = "💔 You lost!"
        outcome = "lose"
    
    # Build message
    msg = f"🎮 <b>Rock Paper Scissors</b>\n\n"
    msg += f"<b>You chose:</b> {EMOJIS[user_choice]} {user_choice.title()}\n"
    msg += f"<b>I chose:</b> {EMOJIS[bot_choice]} {bot_choice.title()}\n\n"
    msg += f"<b>{result}</b>"
    
    await message.reply_html(msg)

