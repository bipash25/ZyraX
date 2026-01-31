"""
Choose command - Random choice from options
"""
import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "choose",
    "aliases": ["pick", "choice"],
    "description": "Randomly choose from options",
    "usage": "/choose <option1> <option2> ...",
    "category": "fun"
}


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Choose random option"""
    message = update.message
    
    if not context.args or len(context.args) < 2:
        await message.reply_html(
            "🤔 <b>Random Choice</b>\n\n"
            "❓ Provide at least 2 options!\n\n"
            "<b>Usage:</b> <code>/choose pizza burger pasta</code>"
        )
        return
    
    # Join args and split by common separators
    text = " ".join(context.args)
    
    # Try to split by separators
    if '|' in text:
        options = [opt.strip() for opt in text.split('|')]
    elif ',' in text:
        options = [opt.strip() for opt in text.split(',')]
    else:
        options = context.args
    
    # Filter empty options
    options = [opt for opt in options if opt]
    
    if len(options) < 2:
        await message.reply_text("❌ Provide at least 2 options!")
        return
    
    choice = random.choice(options)
    
    await message.reply_html(
        f"🤔 <b>Random Choice</b>\n\n"
        f"<b>Options:</b> {', '.join(options)}\n\n"
        f"✨ <b>I choose:</b> {choice}"
    )

