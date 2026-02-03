"""
Russian Roulette Game Module

Multiplayer elimination game.
"""

import time
import random
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from zyrax.database.mongo import db
from zyrax.utils.errors import error_handler
from zyrax.utils.ratelimit import rate_limit
from zyrax.constants import Limits
from .base import RR_GAMES


MAX_PLAYERS = 6
MIN_PLAYERS = 2
CHAMBERS = 6


@Client.on_message(filters.command("rr") & filters.group)
@rate_limit(max_attempts=3, window=60)
@error_handler
async def russian_roulette_start(client: Client, message: Message):
    """Start a Russian Roulette game."""
    chat_id = message.chat.id
    
    if chat_id in RR_GAMES:
        game = RR_GAMES[chat_id]
        return await message.reply_text(
            f"A Russian Roulette game is in progress!\n"
            f"Players: {len(game['players'])}/{MAX_PLAYERS}\n"
            f"Use /rrjoin to join or /rrstart to begin!"
        )
    
    # Get bet amount
    bet = 50
    if len(message.command) > 1:
        try:
            bet = int(message.command[1])
        except ValueError:
            pass
    bet = min(max(bet, Limits.MIN_BET_AMOUNT), 500)
    
    RR_GAMES[chat_id] = {
        "players": [{
            "id": message.from_user.id,
            "name": message.from_user.first_name
        }],
        "bet": bet,
        "started": False,
        "current_player": 0,
        "bullet_chamber": random.randint(0, CHAMBERS - 1),
        "current_chamber": 0,
        "host_id": message.from_user.id,
        "created_at": time.time()
    }
    
    await message.reply_text(
        f"**Russian Roulette**\n\n"
        f"Buy-in: {bet} coins\n"
        f"Players: 1/{MAX_PLAYERS}\n\n"
        f"{message.from_user.first_name} created a game!\n\n"
        f"Use /rrjoin to join\n"
        f"Use /rrstart when ready (min {MIN_PLAYERS} players)"
    )


@Client.on_message(filters.command("rrjoin") & filters.group)
@rate_limit(max_attempts=5, window=60)
@error_handler
async def russian_roulette_join(client: Client, message: Message):
    """Join a Russian Roulette game."""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if chat_id not in RR_GAMES:
        return await message.reply_text("No game in progress. Use /rr to start one!")
    
    game = RR_GAMES[chat_id]
    
    if game["started"]:
        return await message.reply_text("Game already started!")
    
    if len(game["players"]) >= MAX_PLAYERS:
        return await message.reply_text(f"Game is full! ({MAX_PLAYERS} players max)")
    
    if any(p["id"] == user_id for p in game["players"]):
        return await message.reply_text("You're already in the game!")
    
    # Check balance
    user_data = await db.get_user_data(user_id)
    balance = user_data.get("balance", 0) if user_data else 0
    
    if balance < game["bet"]:
        return await message.reply_text(
            f"Not enough coins! You need {game['bet']} coins to join."
        )
    
    # Deduct bet
    await db.add_balance(user_id, -game["bet"])
    
    game["players"].append({
        "id": user_id,
        "name": message.from_user.first_name
    })
    
    player_list = "\n".join(f"- {p['name']}" for p in game["players"])
    await message.reply_text(
        f"**{message.from_user.first_name} joined!**\n\n"
        f"Players ({len(game['players'])}/{MAX_PLAYERS}):\n{player_list}\n\n"
        f"Use /rrstart when ready!"
    )


@Client.on_message(filters.command("rrstart") & filters.group)
@error_handler
async def russian_roulette_begin(client: Client, message: Message):
    """Start the Russian Roulette game."""
    chat_id = message.chat.id
    
    if chat_id not in RR_GAMES:
        return await message.reply_text("No game in progress!")
    
    game = RR_GAMES[chat_id]
    
    if game["started"]:
        return await message.reply_text("Game already started!")
    
    if len(game["players"]) < MIN_PLAYERS:
        return await message.reply_text(
            f"Need at least {MIN_PLAYERS} players to start!"
        )
    
    # Deduct bet from host (first player)
    host_id = game["players"][0]["id"]
    user_data = await db.get_user_data(host_id)
    balance = user_data.get("balance", 0) if user_data else 0
    if balance >= game["bet"]:
        await db.add_balance(host_id, -game["bet"])
    
    game["started"] = True
    random.shuffle(game["players"])
    
    current = game["players"][0]
    
    buttons = InlineKeyboardMarkup([[
        InlineKeyboardButton("Pull Trigger", callback_data="rr_pull")
    ]])
    
    pot = game["bet"] * len(game["players"])
    await message.reply_text(
        f"**Russian Roulette Started!**\n\n"
        f"Pot: {pot} coins\n"
        f"Chamber: ?/{CHAMBERS}\n\n"
        f"**{current['name']}**, it's your turn!\n"
        f"Pull the trigger...",
        reply_markup=buttons
    )


@Client.on_callback_query(filters.regex(r"^rr_pull$"))
async def russian_roulette_pull(client: Client, callback: CallbackQuery):
    """Handle trigger pull."""
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    
    if chat_id not in RR_GAMES:
        return await callback.answer("Game ended.", show_alert=True)
    
    game = RR_GAMES[chat_id]
    
    if not game["started"]:
        return await callback.answer("Game hasn't started!", show_alert=True)
    
    current_player = game["players"][game["current_player"]]
    
    if user_id != current_player["id"]:
        return await callback.answer("Not your turn!", show_alert=True)
    
    # Check if bullet fires
    if game["current_chamber"] == game["bullet_chamber"]:
        # BANG! Player is out
        eliminated = game["players"].pop(game["current_player"])
        
        if len(game["players"]) == 1:
            # Winner!
            winner = game["players"][0]
            pot = game["bet"] * (len(game["players"]) + 1 + game["current_chamber"])
            await db.add_balance(winner["id"], pot)
            await db.update_game_stats(winner["id"], "roulette", True)
            
            del RR_GAMES[chat_id]
            
            await callback.message.edit_text(
                f"**BANG!**\n\n"
                f"{eliminated['name']} is eliminated!\n\n"
                f"**{winner['name']} WINS {pot} coins!**"
            )
        else:
            # Game continues, reset chamber
            game["bullet_chamber"] = random.randint(0, CHAMBERS - 1)
            game["current_chamber"] = 0
            if game["current_player"] >= len(game["players"]):
                game["current_player"] = 0
            
            next_player = game["players"][game["current_player"]]
            remaining = ", ".join(p["name"] for p in game["players"])
            
            buttons = InlineKeyboardMarkup([[
                InlineKeyboardButton("Pull Trigger", callback_data="rr_pull")
            ]])
            
            await callback.message.edit_text(
                f"**BANG!**\n\n"
                f"{eliminated['name']} is eliminated!\n\n"
                f"Remaining: {remaining}\n"
                f"New round! Chamber reloaded.\n\n"
                f"**{next_player['name']}**, your turn!",
                reply_markup=buttons
            )
    else:
        # Click! Safe
        game["current_chamber"] += 1
        game["current_player"] = (game["current_player"] + 1) % len(game["players"])
        next_player = game["players"][game["current_player"]]
        
        buttons = InlineKeyboardMarkup([[
            InlineKeyboardButton("Pull Trigger", callback_data="rr_pull")
        ]])
        
        await callback.message.edit_text(
            f"*Click!*\n\n"
            f"{current_player['name']} survives!\n"
            f"Chamber: {game['current_chamber']}/{CHAMBERS}\n\n"
            f"**{next_player['name']}**, your turn!",
            reply_markup=buttons
        )
    
    await callback.answer()


@Client.on_message(filters.command("rrcancel") & filters.group)
@error_handler
async def russian_roulette_cancel(client: Client, message: Message):
    """Cancel a Russian Roulette game."""
    chat_id = message.chat.id
    
    if chat_id not in RR_GAMES:
        return await message.reply_text("No game in progress!")
    
    game = RR_GAMES[chat_id]
    
    # Only host can cancel
    if message.from_user.id != game["host_id"]:
        return await message.reply_text("Only the game creator can cancel!")
    
    # Refund bets if not started
    if not game["started"]:
        for player in game["players"]:
            await db.add_balance(player["id"], game["bet"])
        refund_msg = " Bets refunded."
    else:
        refund_msg = ""
    
    del RR_GAMES[chat_id]
    await message.reply_text(f"Game cancelled.{refund_msg}")
