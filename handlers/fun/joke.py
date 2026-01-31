"""
Joke command - Random jokes
"""
import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "joke",
    "aliases": [],
    "description": "Get a random joke",
    "usage": "/joke - Random joke",
    "category": "fun"
}

JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "Why did the scarecrow win an award? He was outstanding in his field!",
    "Why don't eggs tell jokes? They'd crack each other up!",
    "What do you call a fake noodle? An impasta!",
    "Why did the bicycle fall over? Because it was two-tired!",
    "What do you call cheese that isn't yours? Nacho cheese!",
    "Why couldn't the bicycle stand up by itself? It was two tired!",
    "What do you call a bear with no teeth? A gummy bear!",
    "Why did the math book look so sad? Because it had too many problems!",
    "What did one wall say to the other? I'll meet you at the corner!",
    "Why don't skeletons fight each other? They don't have the guts!",
    "What do you call a boomerang that doesn't come back? A stick!",
    "Why was the computer cold? It left its Windows open!",
    "What's orange and sounds like a parrot? A carrot!",
    "Why did the tomato turn red? Because it saw the salad dressing!",
    "What do you call a fish with no eyes? Fsh!",
    "Why don't programmers like nature? It has too many bugs!",
    "What's the best thing about Switzerland? I don't know, but the flag is a big plus!",
    "Why did the coffee file a police report? It got mugged!",
    "What do you call a sleeping bull? A bulldozer!",
]


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send random joke"""
    joke = random.choice(JOKES)
    
    await update.message.reply_html(
        f"😄 <b>Joke of the Day</b>\n\n{joke}"
    )

