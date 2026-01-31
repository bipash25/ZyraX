"""
Roast command - Funny roasts (all in good fun!)
"""
import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

from utils.user_resolver import resolve_user

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "roast",
    "aliases": ["burn"],
    "description": "Roast someone (in good fun!)",
    "usage": "/roast [@user]",
    "category": "fun"
}

ROASTS = [
    "I'd agree with you, but then we'd both be wrong.",
    "You're like a cloud. When you disappear, it's a beautiful day.",
    "If I had a dollar for every smart thing you say, I'd be broke.",
    "I'm jealous of people who don't know you.",
    "You're not stupid; you just have bad luck thinking.",
    "Somewhere out there is a tree tirelessly producing oxygen for you. You owe it an apology.",
    "I'd explain it to you, but I don't have any crayons with me.",
    "You're the human version of a participation award.",
    "I thought of you today. It reminded me to take out the trash.",
    "You're proof that evolution can go in reverse.",
    "I'd roast you, but my mom said I'm not allowed to burn trash.",
    "You bring everyone so much joy... when you leave the room.",
    "I'd give you a nasty look, but you already have one.",
    "You're like Monday mornings, nobody likes you.",
    "If laughter is the best medicine, your face must be curing the world.",
]


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roast a user"""
    target_user, _ = await resolve_user(update, context)
    
    if not target_user:
        target_user = update.effective_user
    
    roast = random.choice(ROASTS)
    
    await update.message.reply_html(
        f"🔥 <b>Roast</b>\n\n"
        f"{target_user.mention_html()}, {roast}\n\n"
        f"<i>(Just kidding! It's all in good fun! 😄)</i>"
    )

