"""
Guess the Number Game Module
"""

import time
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.database.mongo import db
from zyrax.utils.errors import error_handler
from zyrax.utils.ratelimit import rate_limit
from zyrax.constants import Rewards
from .base import GUESS_GAMES


@Client.on_message(filters.command("guess"))
@rate_limit(max_attempts=3, window=60)
@error_handler
async def guess_game(client: Client, message: Message):
    """Start a guess the number game."""
    chat_id = message.chat.id
    
    if chat_id in GUESS_GAMES:
        return await message.reply_text(
            "A guessing game is already in progress! Use /endguess to stop it."
        )
    
    number = random.randint(1, 100)
    GUESS_GAMES[chat_id] = {
        "number": number,
        "attempts": 0,
        "created_at": time.time()
    }
    
    await message.reply_text(
        "**Guess the Number!**\n"
        "I have picked a number between 1 and 100.\n"
        "Send your guess in the chat!"
    )


@Client.on_message(filters.command("endguess"))
@error_handler
async def end_guess(client: Client, message: Message):
    """End the current guess game."""
    if message.chat.id in GUESS_GAMES:
        num = GUESS_GAMES[message.chat.id]["number"]
        del GUESS_GAMES[message.chat.id]
        await message.reply_text(f"Game ended. The number was **{num}**.")
    else:
        await message.reply_text("No guess game in progress.")


@Client.on_message(filters.group & filters.text, group=3)
async def guess_handler(client: Client, message: Message):
    """Handle number guesses."""
    chat_id = message.chat.id
    if chat_id not in GUESS_GAMES:
        return
    
    try:
        guess = int(message.text)
    except ValueError:
        return
    
    game = GUESS_GAMES[chat_id]
    target = game["number"]
    game["attempts"] += 1
    
    if guess == target:
        del GUESS_GAMES[chat_id]
        # Calculate reward based on attempts
        reward = max(
            Rewards.GUESS_BASE_REWARD - game["attempts"] * Rewards.GUESS_PENALTY_PER_ATTEMPT,
            Rewards.GUESS_MIN_REWARD
        )
        await db.add_balance(message.from_user.id, reward)
        await db.update_game_stats(message.from_user.id, "guess", True)
        await message.reply_text(
            f"**Correct!**\n"
            f"{message.from_user.mention} guessed **{target}** in {game['attempts']} attempts!\n"
            f"Reward: {reward} coins"
        )
    elif guess < target:
        await message.reply_text("Too low!")
    else:
        await message.reply_text("Too high!")
