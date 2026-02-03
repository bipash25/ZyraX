"""
Word Games Module

Hangman and Word Scramble games.
"""

import time
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.database.mongo import db
from zyrax.utils.errors import error_handler
from zyrax.utils.ratelimit import rate_limit
from zyrax.constants import HANGMAN_WORDS, Rewards
from .base import HANGMAN_GAMES, SCRAMBLE_GAMES


# =============================================================================
# HANGMAN
# =============================================================================

@Client.on_message(filters.command("hangman"))
@rate_limit(max_attempts=3, window=60)
@error_handler
async def hangman_start(client: Client, message: Message):
    """Start a hangman game."""
    chat_id = message.chat.id
    
    if chat_id in HANGMAN_GAMES:
        return await message.reply_text(
            "A hangman game is already in progress! Use /endhangman to stop it."
        )
    
    word = random.choice(HANGMAN_WORDS).lower()
    HANGMAN_GAMES[chat_id] = {
        "word": word,
        "guessed": set(),
        "lives": 6,
        "created_at": time.time()
    }
    
    display = " ".join("_" if c.isalpha() else c for c in word)
    await message.reply_text(
        f"**Hangman!**\n\n"
        f"`{display}`\n\n"
        f"Lives: 6\n\n"
        f"Guess a letter by typing it!"
    )


@Client.on_message(filters.command("endhangman"))
@error_handler
async def hangman_end(client: Client, message: Message):
    """End the current hangman game."""
    if message.chat.id in HANGMAN_GAMES:
        word = HANGMAN_GAMES[message.chat.id]["word"]
        del HANGMAN_GAMES[message.chat.id]
        await message.reply_text(f"Game ended. The word was: **{word}**")
    else:
        await message.reply_text("No hangman game in progress.")


@Client.on_message(filters.group & filters.text & filters.regex(r"^[a-zA-Z]$"), group=4)
async def hangman_guess(client: Client, message: Message):
    """Handle single letter guesses for hangman."""
    chat_id = message.chat.id
    if chat_id not in HANGMAN_GAMES:
        return
    
    game = HANGMAN_GAMES[chat_id]
    letter = message.text.lower()
    
    if letter in game["guessed"]:
        return await message.reply_text("Already guessed!")
    
    game["guessed"].add(letter)
    
    if letter in game["word"]:
        display = " ".join(
            c if c in game["guessed"] or not c.isalpha() else "_"
            for c in game["word"]
        )
        
        if "_" not in display:
            # Player won
            del HANGMAN_GAMES[chat_id]
            await db.add_balance(message.from_user.id, Rewards.HANGMAN_WIN)
            await db.update_game_stats(message.from_user.id, "hangman", True)
            return await message.reply_text(
                f"**You win!** The word was: **{game['word']}**\n"
                f"Reward: {Rewards.HANGMAN_WIN} coins"
            )
        
        await message.reply_text(
            f"Correct!\n\n`{display}`\n\nLives: {game['lives']}"
        )
    else:
        game["lives"] -= 1
        if game["lives"] <= 0:
            del HANGMAN_GAMES[chat_id]
            return await message.reply_text(
                f"**Game Over!** The word was: **{game['word']}**"
            )
        
        display = " ".join(
            c if c in game["guessed"] or not c.isalpha() else "_"
            for c in game["word"]
        )
        await message.reply_text(
            f"Wrong!\n\n`{display}`\n\nLives: {game['lives']}"
        )


# =============================================================================
# WORD SCRAMBLE
# =============================================================================

@Client.on_message(filters.command("scramble"))
@rate_limit(max_attempts=3, window=60)
@error_handler
async def scramble_start(client: Client, message: Message):
    """Start a word scramble game."""
    chat_id = message.chat.id
    
    if chat_id in SCRAMBLE_GAMES:
        return await message.reply_text("A scramble game is in progress!")
    
    word = random.choice(HANGMAN_WORDS)
    scrambled = list(word)
    random.shuffle(scrambled)
    scrambled = "".join(scrambled)
    
    SCRAMBLE_GAMES[chat_id] = {
        "word": word,
        "scrambled": scrambled,
        "created_at": time.time()
    }
    
    await message.reply_text(
        f"**Word Scramble!**\n\n"
        f"Unscramble: `{scrambled}`\n\n"
        f"Type the correct word!"
    )


@Client.on_message(filters.command("endscramble"))
@error_handler
async def scramble_end(client: Client, message: Message):
    """End the current scramble game."""
    if message.chat.id in SCRAMBLE_GAMES:
        word = SCRAMBLE_GAMES[message.chat.id]["word"]
        del SCRAMBLE_GAMES[message.chat.id]
        await message.reply_text(f"Game ended. The word was: **{word}**")
    else:
        await message.reply_text("No scramble game in progress.")


@Client.on_message(filters.group & filters.text, group=5)
async def scramble_guess(client: Client, message: Message):
    """Handle scramble word guesses."""
    chat_id = message.chat.id
    if chat_id not in SCRAMBLE_GAMES:
        return
    
    game = SCRAMBLE_GAMES[chat_id]
    if message.text.lower() == game["word"]:
        del SCRAMBLE_GAMES[chat_id]
        await db.add_balance(message.from_user.id, Rewards.SCRAMBLE_WIN)
        await db.update_game_stats(message.from_user.id, "scramble", True)
        await message.reply_text(
            f"**Correct!** {message.from_user.mention} wins!\n"
            f"Reward: {Rewards.SCRAMBLE_WIN} coins"
        )
