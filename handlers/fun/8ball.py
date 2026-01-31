"""
Magic 8-Ball command - Random fortune telling
"""
import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "8ball",
    "aliases": ["eightball", "fortune"],
    "description": "Ask the magic 8-ball a question",
    "usage": "/8ball <question>",
    "category": "fun"
}

# Magic 8-Ball responses
RESPONSES = [
    # Positive
    "🟢 It is certain.",
    "🟢 It is decidedly so.",
    "🟢 Without a doubt.",
    "🟢 Yes - definitely.",
    "🟢 You may rely on it.",
    "🟢 As I see it, yes.",
    "🟢 Most likely.",
    "🟢 Outlook good.",
    "🟢 Yes.",
    "🟢 Signs point to yes.",
    
    # Neutral
    "🟡 Reply hazy, try again.",
    "🟡 Ask again later.",
    "🟡 Better not tell you now.",
    "🟡 Cannot predict now.",
    "🟡 Concentrate and ask again.",
    
    # Negative
    "🔴 Don't count on it.",
    "🔴 My reply is no.",
    "🔴 My sources say no.",
    "🔴 Outlook not so good.",
    "🔴 Very doubtful.",
]


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Magic 8-ball fortune"""
    message = update.message
    
    if not context.args:
        await message.reply_html(
            "🎱 <b>Magic 8-Ball</b>\n\n"
            "❓ Ask me a question!\n\n"
            "<b>Usage:</b> <code>/8ball Will I win?</code>"
        )
        return
    
    question = " ".join(context.args)
    
    # Pick random response
    response = random.choice(RESPONSES)
    
    await message.reply_html(
        f"🎱 <b>Magic 8-Ball</b>\n\n"
        f"<b>Question:</b> {question}\n\n"
        f"<b>Answer:</b> {response}"
    )

