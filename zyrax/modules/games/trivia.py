"""
Trivia Game Module

Fetches trivia questions from Open Trivia DB.
"""

import time
import html
import aiohttp
import random
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from zyrax.database.mongo import db
from zyrax.utils.errors import error_handler
from zyrax.utils.ratelimit import rate_limit
from zyrax.constants import Rewards
from .base import TRIVIA_GAMES


TRIVIA_API_URL = "https://opentdb.com/api.php?amount=1&type=multiple"


@Client.on_message(filters.command("trivia"))
@rate_limit(max_attempts=3, window=60)
@error_handler
async def trivia(client: Client, message: Message):
    """Start a trivia question."""
    chat_id = message.chat.id
    
    if chat_id in TRIVIA_GAMES:
        return await message.reply_text("A trivia game is already in progress!")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(TRIVIA_API_URL) as resp:
            data = await resp.json()
    
    if data["response_code"] != 0:
        return await message.reply_text("Failed to fetch trivia. Try again later.")
    
    q = data["results"][0]
    question = html.unescape(q["question"])
    correct = html.unescape(q["correct_answer"])
    incorrect = [html.unescape(a) for a in q["incorrect_answers"]]
    
    options = incorrect + [correct]
    random.shuffle(options)
    
    TRIVIA_GAMES[chat_id] = {
        "correct": correct,
        "options": options,
        "created_at": time.time()
    }
    
    buttons = [
        [InlineKeyboardButton(opt, callback_data=f"trivia_{i}")]
        for i, opt in enumerate(options)
    ]
    
    await message.reply_text(
        f"**Trivia Time!**\n\n{question}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Client.on_callback_query(filters.regex(r"^trivia_"))
async def trivia_callback(client: Client, callback_query: CallbackQuery):
    """Handle trivia answer selection."""
    chat_id = callback_query.message.chat.id
    
    if chat_id not in TRIVIA_GAMES:
        return await callback_query.answer("Game ended.", show_alert=True)
    
    game = TRIVIA_GAMES[chat_id]
    idx = int(callback_query.data.split("_")[1])
    selected = game["options"][idx]
    
    if selected == game["correct"]:
        del TRIVIA_GAMES[chat_id]
        await callback_query.message.edit_text(
            f"Correct! **{callback_query.from_user.mention}** won!\n"
            f"Answer: {selected}\n"
            f"Reward: {Rewards.TRIVIA_WIN} coins"
        )
        await db.add_balance(callback_query.from_user.id, Rewards.TRIVIA_WIN)
        await db.update_game_stats(callback_query.from_user.id, "trivia", True)
    else:
        await callback_query.answer("Wrong! Try again.", show_alert=True)
