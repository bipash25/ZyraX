"""
Ship command - Calculate compatibility between two users
"""
import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

from utils.user_resolver import resolve_user

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "ship",
    "aliases": ["love", "compatibility"],
    "description": "Check compatibility between two users",
    "usage": "/ship @user1 @user2",
    "category": "fun"
}


def calculate_compatibility(id1: int, id2: int) -> int:
    """Calculate consistent compatibility based on user IDs"""
    # Use both IDs to create a seed for consistent results
    combined = sorted([id1, id2])
    seed = int(str(combined[0]) + str(combined[1]))
    random.seed(seed)
    compatibility = random.randint(0, 100)
    random.seed()  # Reset seed
    return compatibility


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Calculate compatibility between users"""
    message = update.message
    user = update.effective_user
    
    # Get first user (from reply or args)
    user1, remaining_text = await resolve_user(update, context)
    
    # If no user1, use message sender
    if not user1:
        user1 = user
    
    # Get second user
    user2 = None
    if remaining_text:
        # Try to extract second mention/username
        words = remaining_text.split()
        for word in words:
            if word.startswith('@'):
                username = word[1:]
                try:
                    chat_member = await message.chat.get_member_by_username(username)
                    if chat_member:
                        user2 = chat_member.user
                        break
                except:
                    pass
    
    # If still no user2, random match with sender
    if not user2:
        if user1.id == user.id:
            await message.reply_html(
                "💕 <b>Ship</b>\n\n"
                "<b>Usage:</b> <code>/ship @user1 @user2</code>\n"
                "Or reply to a user with <code>/ship @user2</code>"
            )
            return
        user2 = user
    
    # Can't ship yourself
    if user1.id == user2.id:
        await message.reply_text("❌ You can't ship someone with themselves!")
        return
    
    # Calculate compatibility
    compatibility = calculate_compatibility(user1.id, user2.id)
    
    # Determine message
    if compatibility >= 90:
        msg_emoji = "💞"
        msg_text = "Perfect match! Made for each other!"
    elif compatibility >= 70:
        msg_emoji = "💕"
        msg_text = "Great compatibility! Very promising!"
    elif compatibility >= 50:
        msg_emoji = "❤️"
        msg_text = "Good match! Worth a shot!"
    elif compatibility >= 30:
        msg_emoji = "💛"
        msg_text = "Could work with effort!"
    else:
        msg_emoji = "💔"
        msg_text = "Not the best match..."
    
    # Build progress bar
    filled = int(compatibility / 10)
    bar = "█" * filled + "░" * (10 - filled)
    
    await message.reply_html(
        f"{msg_emoji} <b>Love Calculator</b>\n\n"
        f"<b>{user1.first_name}</b> 💗 <b>{user2.first_name}</b>\n\n"
        f"<b>Compatibility:</b> {compatibility}%\n"
        f"[{bar}]\n\n"
        f"<i>{msg_text}</i>"
    )

