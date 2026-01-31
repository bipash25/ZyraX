"""
Fact command - Random interesting facts
"""
import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "fact",
    "aliases": ["funfact"],
    "description": "Get a random interesting fact",
    "usage": "/fact - Random fact",
    "category": "fun"
}

FACTS = [
    "Honey never spoils. Archaeologists have found 3000-year-old honey in Egyptian tombs that was still edible!",
    "Octopuses have three hearts and blue blood!",
    "A day on Venus is longer than a year on Venus!",
    "Bananas are berries, but strawberries aren't!",
    "Sharks existed before trees. Sharks have been around for about 400 million years, while trees appeared around 350 million years ago!",
    "Hot water freezes faster than cold water under certain conditions (Mpemba effect)!",
    "The Eiffel Tower can be 15 cm taller during the summer due to thermal expansion!",
    "A single cloud can weigh over a million pounds!",
    "Your nose can remember 50,000 different scents!",
    "Butterflies can taste with their feet!",
    "The shortest war in history lasted 38 minutes (Britain vs Zanzibar, 1896)!",
    "A group of flamingos is called a 'flamboyance'!",
    "Scotland's national animal is the unicorn!",
    "There are more stars in space than grains of sand on all beaches on Earth!",
    "The human brain uses 20% of the body's energy but is only 2% of body mass!",
    "Sound travels 4 times faster through water than air!",
    "Cheetahs can't roar, but they can purr!",
    "An octopus can change its skin texture in 0.3 seconds!",
    "Humans and giraffes have the same number of neck vertebrae (7)!",
    "A sneeze travels at about 100 mph!",
]


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send random fact"""
    fact = random.choice(FACTS)
    
    await update.message.reply_html(
        f"🧠 <b>Did You Know?</b>\n\n{fact}"
    )

