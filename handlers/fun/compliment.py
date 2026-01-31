"""
Compliment command - Make someone's day!
"""
import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

from utils.user_resolver import resolve_user

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "compliment",
    "aliases": ["praise", "nice"],
    "description": "Compliment someone",
    "usage": "/compliment [@user]",
    "category": "fun"
}

COMPLIMENTS = [
    "You're an awesome person!",
    "You light up every room you enter!",
    "You have a great sense of humor!",
    "You're more fun than bubble wrap!",
    "You're a gift to those around you!",
    "You're a smart cookie!",
    "You're awesome sauce!",
    "Your smile is contagious!",
    "You're one of a kind!",
    "You're inspiring!",
    "You're a great example to others!",
    "Colors seem brighter when you're around!",
    "You're better than a triple-scoop ice cream cone!",
    "You're a candle in the darkness!",
    "You're like a breath of fresh air!",
    "You make me want to be a better person!",
    "You're someone's reason to smile!",
    "You're more helpful than you realize!",
    "You have impeccable manners!",
    "You're really something special!",
]


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Compliment a user"""
    target_user, _ = await resolve_user(update, context)
    
    if not target_user:
        target_user = update.effective_user
    
    compliment = random.choice(COMPLIMENTS)
    
    await update.message.reply_html(
        f"💝 <b>Compliment</b>\n\n"
        f"{target_user.mention_html()}, {compliment} ✨"
    )

