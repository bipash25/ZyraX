import random
import aiohttp
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from zyrax.database.mongo import db

__mod_name__ = "Games"
__help__ = """
/dice - Roll a dice
/dart - Throw a dart
/rps <rock/paper/scissors> - Play Rock Paper Scissors
/trivia - Start a trivia question
/guess - Start a number guessing game
"""

# Store active games
# trivia_games = {chat_id: {"answer": "...", "options": [...]}}
TRIVIA_GAMES = {}
GUESS_GAMES = {}

@Client.on_message(filters.command("dice"))
async def dice(client: Client, message: Message):
    await client.send_dice(message.chat.id, "🎲")

@Client.on_message(filters.command("dart"))
async def dart(client: Client, message: Message):
    await client.send_dice(message.chat.id, "🎯")

@Client.on_message(filters.command("rps"))
async def rps(client: Client, message: Message):
    choices = ["rock", "paper", "scissors"]
    bot_choice = random.choice(choices)
    
    if len(message.command) < 2:
        return await message.reply_text("Usage: /rps <rock/paper/scissors>")
    
    user_choice = message.command[1].lower()
    if user_choice not in choices:
         return await message.reply_text("Invalid choice! Choose rock, paper, or scissors.")
         
    result = "It's a tie!"
    if (user_choice == "rock" and bot_choice == "scissors") or \
       (user_choice == "paper" and bot_choice == "rock") or \
       (user_choice == "scissors" and bot_choice == "paper"):
        result = "You win!"
    elif user_choice != bot_choice:
        result = "I win!"
        
    await message.reply_text(f"I chose {bot_choice}. {result}")

# Trivia System
@Client.on_message(filters.command("trivia"))
async def trivia(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id in TRIVIA_GAMES:
        return await message.reply_text("A trivia game is already in progress!")
        
    async with aiohttp.ClientSession() as session:
        async with session.get("https://opentdb.com/api.php?amount=1&type=multiple") as resp:
            data = await resp.json()
            
    if data["response_code"] != 0:
        return await message.reply_text("Failed to fetch trivia.")
        
    q = data["results"][0]
    question = q["question"]
    correct = q["correct_answer"]
    incorrect = q["incorrect_answers"]
    
    options = incorrect + [correct]
    random.shuffle(options)
    
    # Store game state
    TRIVIA_GAMES[chat_id] = {
        "correct": correct,
        "options": options
    }
    
    # Build keyboard
    buttons = []
    for opt in options:
        # Use index as callback data to avoid long data issues
        idx = options.index(opt)
        buttons.append([InlineKeyboardButton(opt, callback_data=f"trivia_{idx}")])
        
    await message.reply_text(
        f"**Trivia Time!**\n\n{question}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r"^trivia_"))
async def trivia_callback(client: Client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    if chat_id not in TRIVIA_GAMES:
        return await callback_query.answer("Game ended.", show_alert=True)
        
    game = TRIVIA_GAMES[chat_id]
    idx = int(callback_query.data.split("_")[1])
    selected = game["options"][idx]
    
    if selected == game["correct"]:
        del TRIVIA_GAMES[chat_id]
        await callback_query.message.edit_text(
            f"✅ Correct! **{callback_query.from_user.mention}** won!\nAnswer: {selected}"
        )
        # Give reward?
        # await db.add_balance(callback_query.from_user.id, 50)
    else:
        await callback_query.answer("Wrong! Try again.", show_alert=True)

# Guess Number System
@Client.on_message(filters.command("guess"))
async def guess_game(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id in GUESS_GAMES:
        return await message.reply_text("A guessing game is already in progress!")
        
    number = random.randint(1, 100)
    GUESS_GAMES[chat_id] = {"number": number, "attempts": 0}
    
    await message.reply_text(
        "🔢 **Guess the Number!**\n"
        "I have picked a number between 1 and 100.\n"
        "Send your guess in the chat!"
    )

@Client.on_message(filters.group & filters.text, group=3)
async def guess_handler(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in GUESS_GAMES:
        return
        
    try:
        guess = int(message.text)
    except:
        return # Not a number
        
    game = GUESS_GAMES[chat_id]
    target = game["number"]
    game["attempts"] += 1
    
    if guess == target:
        del GUESS_GAMES[chat_id]
        await message.reply_text(
            f"🎉 **Correct!**\n"
            f"{message.from_user.mention} guessed the number **{target}** in {game['attempts']} attempts!"
        )
    elif guess < target:
        await message.reply_text("Too low! ⬆️")
    else:
        await message.reply_text("Too high! ⬇️")
