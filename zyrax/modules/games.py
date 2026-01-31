import random
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

__mod_name__ = "Games"
__help__ = """
/dice - Roll a dice
/dart - Throw a dart
/rps <rock/paper/scissors> - Play Rock Paper Scissors
"""

@Client.on_message(filters.command("dice") & filters.group)
async def dice(client: Client, message: Message):
    await client.send_dice(message.chat.id, "🎲")

@Client.on_message(filters.command("dart") & filters.group)
async def dart(client: Client, message: Message):
    await client.send_dice(message.chat.id, "🎯")

@Client.on_message(filters.command("rps") & filters.group)
async def rps(client: Client, message: Message):
    # Determine bot's choice
    choices = ["rock", "paper", "scissors"]
    bot_choice = random.choice(choices)
    
    # Check if user provided choice
    if len(message.command) < 2:
        return await message.reply_text("Usage: /rps <rock/paper/scissors>")
    
    user_choice = message.command[1].lower()
    if user_choice not in choices:
         return await message.reply_text("Invalid choice! Choose rock, paper, or scissors.")
         
    # Determine winner
    result = "It's a tie!"
    if (user_choice == "rock" and bot_choice == "scissors") or \
       (user_choice == "paper" and bot_choice == "rock") or \
       (user_choice == "scissors" and bot_choice == "paper"):
        result = "You win!"
    elif user_choice != bot_choice:
        result = "I win!"
        
    await message.reply_text(f"I chose {bot_choice}. {result}")
