"""
Quick Games Module

Simple one-shot games: dice, dart, coin, rock-paper-scissors.
"""

import random
from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.utils.errors import error_handler
from zyrax.utils.ratelimit import rate_limit


@Client.on_message(filters.command("dice"))
@rate_limit(max_attempts=5, window=60)
@error_handler
async def dice(client: Client, message: Message):
    """Roll a dice."""
    await client.send_dice(message.chat.id, emoji="🎲")


@Client.on_message(filters.command("dart"))
@rate_limit(max_attempts=5, window=60)
@error_handler
async def dart(client: Client, message: Message):
    """Throw a dart."""
    await client.send_dice(message.chat.id, emoji="🎯")


@Client.on_message(filters.command("coin"))
@rate_limit(max_attempts=5, window=60)
@error_handler
async def coin_flip(client: Client, message: Message):
    """Flip a coin."""
    result = random.choice(["Heads", "Tails"])
    await message.reply_text(f"**Coin Flip:** {result}!")


@Client.on_message(filters.command("rps"))
@rate_limit(max_attempts=5, window=60)
@error_handler
async def rps(client: Client, message: Message):
    """Play rock-paper-scissors."""
    choices = ["rock", "paper", "scissors"]
    bot_choice = random.choice(choices)
    
    if len(message.command) < 2:
        return await message.reply_text("Usage: /rps <rock/paper/scissors>")
    
    user_choice = message.command[1].lower()
    if user_choice not in choices:
        return await message.reply_text("Invalid choice! Choose rock, paper, or scissors.")
    
    # Determine winner
    if user_choice == bot_choice:
        result = "It's a tie!"
    elif (user_choice == "rock" and bot_choice == "scissors") or \
         (user_choice == "paper" and bot_choice == "rock") or \
         (user_choice == "scissors" and bot_choice == "paper"):
        result = "You win!"
    else:
        result = "I win!"
    
    await message.reply_text(f"I chose {bot_choice}. {result}")
