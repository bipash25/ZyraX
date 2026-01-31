"""
Quote command - Inspirational quotes
"""
import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "quote",
    "aliases": ["inspire"],
    "description": "Get an inspirational quote",
    "usage": "/quote - Random quote",
    "category": "fun"
}

QUOTES = [
    ("The only way to do great work is to love what you do.", "Steve Jobs"),
    ("Innovation distinguishes between a leader and a follower.", "Steve Jobs"),
    ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
    ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
    ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
    ("Everything you've ever wanted is on the other side of fear.", "George Addair"),
    ("Success is not final, failure is not fatal: it is the courage to continue that counts.", "Winston Churchill"),
    ("Hardships often prepare ordinary people for an extraordinary destiny.", "C.S. Lewis"),
    ("Believe in yourself. You are braver than you think.", "Roy T. Bennett"),
    ("I learned that courage was not the absence of fear, but the triumph over it.", "Nelson Mandela"),
    ("The only impossible journey is the one you never begin.", "Tony Robbins"),
    ("In this life we cannot do great things. We can only do small things with great love.", "Mother Teresa"),
    ("Don't watch the clock; do what it does. Keep going.", "Sam Levenson"),
    ("The best time to plant a tree was 20 years ago. The second best time is now.", "Chinese Proverb"),
    ("Your limitation—it's only your imagination.", "Unknown"),
    ("Push yourself, because no one else is going to do it for you.", "Unknown"),
    ("Great things never come from comfort zones.", "Unknown"),
    ("Dream it. Wish it. Do it.", "Unknown"),
    ("Success doesn't just find you. You have to go out and get it.", "Unknown"),
    ("The harder you work for something, the greater you'll feel when you achieve it.", "Unknown"),
]


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send random inspirational quote"""
    quote, author = random.choice(QUOTES)
    
    await update.message.reply_html(
        f"✨ <b>Quote of the Day</b>\n\n"
        f"<i>\"{quote}\"</i>\n\n"
        f"— <b>{author}</b>"
    )

