"""
Tic-Tac-Toe Game Module
"""

import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from zyrax.database.mongo import db
from zyrax.utils.errors import error_handler
from zyrax.utils.ratelimit import rate_limit
from zyrax.constants import Rewards, TTT
from .base import TTT_GAMES


# Win lines: rows, columns, diagonals
WIN_LINES = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
    [0, 3, 6], [1, 4, 7], [2, 5, 8],  # cols
    [0, 4, 8], [2, 4, 6]  # diagonals
]


def render_board(board: list) -> str:
    """Render the board as text."""
    rows = []
    for i in range(3):
        row = "".join(TTT.SYMBOLS[board[i*3 + j]] for j in range(3))
        rows.append(row)
    return "\n".join(rows)


def check_winner(board: list) -> int:
    """Check for winner. Returns 1/2 for player, -1 for draw, 0 for ongoing."""
    for line in WIN_LINES:
        if board[line[0]] == board[line[1]] == board[line[2]] != 0:
            return board[line[0]]
    if 0 not in board:
        return -1  # Draw
    return 0  # Game continues


def create_board_buttons(board: list) -> InlineKeyboardMarkup:
    """Create keyboard buttons for the board."""
    buttons = []
    for i in range(3):
        row = []
        for j in range(3):
            idx = i * 3 + j
            row.append(InlineKeyboardButton(
                TTT.SYMBOLS[board[idx]],
                callback_data=f"ttt_{idx}"
            ))
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


@Client.on_message(filters.command("ttt") & filters.group)
@rate_limit(max_attempts=3, window=60)
@error_handler
async def ttt_start(client: Client, message: Message):
    """Start a Tic-Tac-Toe game."""
    chat_id = message.chat.id
    
    if chat_id in TTT_GAMES:
        return await message.reply_text("A game is already in progress!")
    
    if not message.reply_to_message:
        return await message.reply_text("Reply to someone to challenge them!")
    
    player1 = message.from_user.id
    player2 = message.reply_to_message.from_user.id
    
    if player1 == player2:
        return await message.reply_text("You can't play against yourself!")
    
    if message.reply_to_message.from_user.is_bot:
        return await message.reply_text("You can't play against a bot!")
    
    TTT_GAMES[chat_id] = {
        "board": [0] * 9,
        "player1": player1,
        "player2": player2,
        "turn": player1,
        "p1_name": message.from_user.first_name,
        "p2_name": message.reply_to_message.from_user.first_name,
        "created_at": time.time()
    }
    
    game = TTT_GAMES[chat_id]
    await message.reply_text(
        f"**Tic-Tac-Toe**\n\n"
        f"{game['p1_name']} ({TTT.X}) vs {game['p2_name']} ({TTT.O})\n\n"
        f"{game['p1_name']}'s turn!",
        reply_markup=create_board_buttons(game["board"])
    )


@Client.on_callback_query(filters.regex(r"^ttt_"))
async def ttt_callback(client: Client, callback: CallbackQuery):
    """Handle TTT moves."""
    chat_id = callback.message.chat.id
    
    if chat_id not in TTT_GAMES:
        return await callback.answer("Game ended.", show_alert=True)
    
    game = TTT_GAMES[chat_id]
    user_id = callback.from_user.id
    
    if user_id not in [game["player1"], game["player2"]]:
        return await callback.answer("You're not in this game!", show_alert=True)
    
    if user_id != game["turn"]:
        return await callback.answer("Not your turn!", show_alert=True)
    
    idx = int(callback.data.split("_")[1])
    
    if game["board"][idx] != 0:
        return await callback.answer("Cell already taken!", show_alert=True)
    
    # Make move
    symbol = 1 if user_id == game["player1"] else 2
    game["board"][idx] = symbol
    
    # Check winner
    winner = check_winner(game["board"])
    
    if winner > 0:
        winner_name = game["p1_name"] if winner == 1 else game["p2_name"]
        winner_id = game["player1"] if winner == 1 else game["player2"]
        del TTT_GAMES[chat_id]
        await db.add_balance(winner_id, Rewards.TTT_WIN)
        await db.update_game_stats(winner_id, "ttt", True)
        await callback.message.edit_text(
            f"**{winner_name} wins!**\n\n"
            f"{render_board(game['board'])}\n\n"
            f"Reward: {Rewards.TTT_WIN} coins"
        )
    elif winner == -1:
        del TTT_GAMES[chat_id]
        await callback.message.edit_text(
            f"**It's a draw!**\n\n{render_board(game['board'])}"
        )
    else:
        game["turn"] = game["player2"] if game["turn"] == game["player1"] else game["player1"]
        turn_name = game["p1_name"] if game["turn"] == game["player1"] else game["p2_name"]
        await callback.message.edit_text(
            f"**Tic-Tac-Toe**\n\n"
            f"{game['p1_name']} ({TTT.X}) vs {game['p2_name']} ({TTT.O})\n\n"
            f"{turn_name}'s turn!",
            reply_markup=create_board_buttons(game["board"])
        )
    
    await callback.answer()


@Client.on_message(filters.command("endttt") & filters.group)
@error_handler
async def ttt_end(client: Client, message: Message):
    """End the current TTT game."""
    chat_id = message.chat.id
    if chat_id in TTT_GAMES:
        game = TTT_GAMES[chat_id]
        # Only players can end
        if message.from_user.id in [game["player1"], game["player2"]]:
            del TTT_GAMES[chat_id]
            await message.reply_text("Game ended.")
        else:
            await message.reply_text("Only players can end the game.")
    else:
        await message.reply_text("No game in progress.")
