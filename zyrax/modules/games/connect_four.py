"""
Connect Four Game Module
"""

import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from zyrax.database.mongo import db
from zyrax.utils.errors import error_handler
from zyrax.utils.ratelimit import rate_limit
from zyrax.constants import Rewards, ConnectFour as C4
from .base import C4_GAMES


def render_board(board: list) -> str:
    """Render Connect Four board."""
    rows = []
    for row in board:
        rows.append("".join(C4.SYMBOLS[cell] for cell in row))
    # Add column numbers at bottom
    numbers = "1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣"
    return "\n".join(rows) + "\n" + numbers


def check_winner(board: list) -> int:
    """Check for Connect Four winner (4 in a row)."""
    rows = C4.ROWS
    cols = C4.COLS
    
    # Check horizontal
    for r in range(rows):
        for c in range(cols - 3):
            if board[r][c] != 0 and \
               board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                return board[r][c]
    
    # Check vertical
    for r in range(rows - 3):
        for c in range(cols):
            if board[r][c] != 0 and \
               board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                return board[r][c]
    
    # Check diagonal (down-right)
    for r in range(rows - 3):
        for c in range(cols - 3):
            if board[r][c] != 0 and \
               board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                return board[r][c]
    
    # Check diagonal (down-left)
    for r in range(rows - 3):
        for c in range(3, cols):
            if board[r][c] != 0 and \
               board[r][c] == board[r+1][c-1] == board[r+2][c-2] == board[r+3][c-3]:
                return board[r][c]
    
    # Check for draw (top row full)
    if all(board[0][c] != 0 for c in range(cols)):
        return -1
    
    return 0  # Game continues


def drop_piece(board: list, col: int, player: int) -> int:
    """Drop a piece in the column. Returns row or -1 if column full."""
    for row in range(C4.ROWS - 1, -1, -1):  # Start from bottom
        if board[row][col] == 0:
            board[row][col] = player
            return row
    return -1


def create_column_buttons() -> InlineKeyboardMarkup:
    """Create column selection buttons."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(str(i+1), callback_data=f"c4_{i}")
        for i in range(C4.COLS)
    ]])


@Client.on_message(filters.command("c4") & filters.group)
@rate_limit(max_attempts=3, window=60)
@error_handler
async def connect_four_start(client: Client, message: Message):
    """Start a Connect Four game."""
    chat_id = message.chat.id
    
    if chat_id in C4_GAMES:
        return await message.reply_text("A Connect Four game is already in progress!")
    
    if not message.reply_to_message:
        return await message.reply_text("Reply to someone to challenge them to Connect Four!")
    
    player1 = message.from_user.id
    player2 = message.reply_to_message.from_user.id
    
    if player1 == player2:
        return await message.reply_text("You can't play against yourself!")
    
    if message.reply_to_message.from_user.is_bot:
        return await message.reply_text("You can't play against a bot!")
    
    # 6 rows x 7 columns board
    board = [[0 for _ in range(C4.COLS)] for _ in range(C4.ROWS)]
    
    C4_GAMES[chat_id] = {
        "board": board,
        "player1": player1,
        "player2": player2,
        "turn": player1,
        "p1_name": message.from_user.first_name,
        "p2_name": message.reply_to_message.from_user.first_name,
        "created_at": time.time()
    }
    
    game = C4_GAMES[chat_id]
    await message.reply_text(
        f"**Connect Four**\n\n"
        f"{game['p1_name']} ({C4.PLAYER1}) vs {game['p2_name']} ({C4.PLAYER2})\n\n"
        f"{render_board(board)}\n\n"
        f"{game['p1_name']}'s turn!",
        reply_markup=create_column_buttons()
    )


@Client.on_callback_query(filters.regex(r"^c4_\d$"))
async def connect_four_move(client: Client, callback: CallbackQuery):
    """Handle Connect Four moves."""
    chat_id = callback.message.chat.id
    
    if chat_id not in C4_GAMES:
        return await callback.answer("Game ended.", show_alert=True)
    
    game = C4_GAMES[chat_id]
    user_id = callback.from_user.id
    
    if user_id not in [game["player1"], game["player2"]]:
        return await callback.answer("You're not in this game!", show_alert=True)
    
    if user_id != game["turn"]:
        return await callback.answer("Not your turn!", show_alert=True)
    
    col = int(callback.data.split("_")[1])
    player = 1 if user_id == game["player1"] else 2
    
    row = drop_piece(game["board"], col, player)
    if row == -1:
        return await callback.answer("Column is full!", show_alert=True)
    
    winner = check_winner(game["board"])
    
    if winner > 0:
        winner_name = game["p1_name"] if winner == 1 else game["p2_name"]
        winner_id = game["player1"] if winner == 1 else game["player2"]
        del C4_GAMES[chat_id]
        await db.add_balance(winner_id, Rewards.CONNECT4_WIN)
        await db.update_game_stats(winner_id, "connect4", True)
        await callback.message.edit_text(
            f"**{winner_name} wins Connect Four!**\n\n"
            f"{render_board(game['board'])}\n\n"
            f"Reward: {Rewards.CONNECT4_WIN} coins"
        )
    elif winner == -1:
        del C4_GAMES[chat_id]
        await callback.message.edit_text(
            f"**It's a draw!**\n\n"
            f"{render_board(game['board'])}"
        )
    else:
        # Switch turns
        game["turn"] = game["player2"] if game["turn"] == game["player1"] else game["player1"]
        turn_name = game["p1_name"] if game["turn"] == game["player1"] else game["p2_name"]
        
        await callback.message.edit_text(
            f"**Connect Four**\n\n"
            f"{game['p1_name']} ({C4.PLAYER1}) vs {game['p2_name']} ({C4.PLAYER2})\n\n"
            f"{render_board(game['board'])}\n\n"
            f"{turn_name}'s turn!",
            reply_markup=create_column_buttons()
        )
    
    await callback.answer()


@Client.on_message(filters.command("endc4") & filters.group)
@error_handler
async def connect_four_end(client: Client, message: Message):
    """End the current Connect Four game."""
    chat_id = message.chat.id
    if chat_id in C4_GAMES:
        game = C4_GAMES[chat_id]
        # Only players can end
        if message.from_user.id in [game["player1"], game["player2"]]:
            del C4_GAMES[chat_id]
            await message.reply_text("Game ended.")
        else:
            await message.reply_text("Only players can end the game.")
    else:
        await message.reply_text("No game in progress.")
