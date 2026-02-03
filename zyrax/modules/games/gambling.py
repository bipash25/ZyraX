"""
Gambling Games Module

Slots and gamble (50/50 double or nothing).
"""

import random
from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.database.mongo import db
from zyrax.utils.errors import error_handler
from zyrax.utils.ratelimit import rate_limit
from zyrax.constants import Limits, Rewards, Slots


@Client.on_message(filters.command("slots"))
@rate_limit(max_attempts=5, window=60)
@error_handler
async def slots_game(client: Client, message: Message):
    """Play the slot machine."""
    user_id = message.from_user.id
    bet = 10
    
    if len(message.command) > 1:
        try:
            bet = int(message.command[1])
        except ValueError:
            pass
    
    # Enforce bet limits
    bet = min(max(bet, Limits.MIN_BET_AMOUNT), 1000)
    
    user_data = await db.get_user_data(user_id)
    balance = user_data.get("balance", 0) if user_data else 0
    
    if balance < bet:
        return await message.reply_text(f"Not enough coins! You have {balance} coins.")
    
    await db.add_balance(user_id, -bet)
    
    results = random.choices(Slots.SYMBOLS, weights=Slots.WEIGHTS, k=3)
    
    # Calculate multiplier
    multiplier = 0
    if results[0] == results[1] == results[2]:
        if results[0] == Slots.JACKPOT_SYMBOL:
            multiplier = Rewards.SLOTS_JACKPOT_MULTIPLIER
        elif results[0] == Slots.SPECIAL_SYMBOL:
            multiplier = Rewards.SLOTS_STAR_MULTIPLIER
        else:
            multiplier = Rewards.SLOTS_NORMAL_MULTIPLIER
    elif results[0] == results[1] or results[1] == results[2]:
        multiplier = Rewards.SLOTS_TWO_MATCH_MULTIPLIER
    
    winnings = bet * multiplier
    if winnings > 0:
        await db.add_balance(user_id, winnings)
    
    result_str = " | ".join(results)
    
    if winnings > 0:
        await message.reply_text(
            f"**SLOTS**\n\n[ {result_str} ]\n\n**YOU WIN!** +{winnings} coins!"
        )
    else:
        await message.reply_text(
            f"**SLOTS**\n\n[ {result_str} ]\n\nNo match. -{bet} coins"
        )


@Client.on_message(filters.command("gamble"))
@rate_limit(max_attempts=5, window=60)
@error_handler
async def gamble_game(client: Client, message: Message):
    """50/50 double or nothing gamble."""
    user_id = message.from_user.id
    
    if len(message.command) < 2:
        return await message.reply_text("Usage: /gamble <amount>")
    
    try:
        amount = int(message.command[1])
    except ValueError:
        return await message.reply_text("Invalid amount.")
    
    # Enforce limits
    amount = min(max(amount, 1), Limits.MAX_BET_AMOUNT)
    
    user_data = await db.get_user_data(user_id)
    balance = user_data.get("balance", 0) if user_data else 0
    
    if balance < amount:
        return await message.reply_text(f"Not enough coins! You have {balance} coins.")
    
    if random.random() < Rewards.GAMBLE_WIN_RATE:
        await db.add_balance(user_id, amount)
        await message.reply_text(
            f"**You won!** +{amount} coins!\n"
            f"New balance: {balance + amount}"
        )
    else:
        await db.add_balance(user_id, -amount)
        await message.reply_text(
            f"**You lost!** -{amount} coins\n"
            f"New balance: {balance - amount}"
        )
