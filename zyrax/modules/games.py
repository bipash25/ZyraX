import random
import aiohttp
import asyncio
import html
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from zyrax.database.mongo import db

__mod_name__ = "Games"
__help__ = """
**Quick Games:**
/dice - Roll a dice
/dart - Throw a dart
/coin - Flip a coin
/rps <rock/paper/scissors> - Rock Paper Scissors

**Word Games:**
/trivia - Start a trivia question
/hangman - Start a hangman game
/scramble - Word scramble game

**Number Games:**
/guess - Guess the number (1-100)
/slots - Slot machine (costs coins)

**Two-Player Games:**
/ttt @user - Tic-Tac-Toe challenge

**Gambling (requires coins):**
/gamble <amount> - 50/50 double or nothing
/blackjack <bet> - Play blackjack
"""

# Store active games
TRIVIA_GAMES = {}
GUESS_GAMES = {}
HANGMAN_GAMES = {}
SCRAMBLE_GAMES = {}
TTT_GAMES = {}
BLACKJACK_GAMES = {}

# Hangman words
HANGMAN_WORDS = [
    "python", "telegram", "programming", "developer", "keyboard", "computer",
    "algorithm", "database", "internet", "software", "hardware", "network",
    "security", "encryption", "function", "variable", "boolean", "integer"
]

@Client.on_message(filters.command("dice"))
async def dice(client: Client, message: Message):
    await client.send_dice(message.chat.id, "🎲")

@Client.on_message(filters.command("dart"))
async def dart(client: Client, message: Message):
    await client.send_dice(message.chat.id, "🎯")

@Client.on_message(filters.command("coin"))
async def coin_flip(client: Client, message: Message):
    result = random.choice(["Heads", "Tails"])
    await message.reply_text(f"**Coin Flip:** {result}!")

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


# ===== TRIVIA =====
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
    question = html.unescape(q["question"])
    correct = html.unescape(q["correct_answer"])
    incorrect = [html.unescape(a) for a in q["incorrect_answers"]]
    
    options = incorrect + [correct]
    random.shuffle(options)
    
    TRIVIA_GAMES[chat_id] = {
        "correct": correct,
        "options": options
    }
    
    buttons = []
    for i, opt in enumerate(options):
        buttons.append([InlineKeyboardButton(opt, callback_data=f"trivia_{i}")])
        
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
            f"Correct! **{callback_query.from_user.mention}** won!\nAnswer: {selected}"
        )
        await db.add_balance(callback_query.from_user.id, 25)
        await db.update_game_stats(callback_query.from_user.id, "trivia", True)
    else:
        await callback_query.answer("Wrong! Try again.", show_alert=True)


# ===== GUESS NUMBER =====
@Client.on_message(filters.command("guess"))
async def guess_game(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id in GUESS_GAMES:
        return await message.reply_text("A guessing game is already in progress! Use /endguess to stop it.")
        
    number = random.randint(1, 100)
    GUESS_GAMES[chat_id] = {"number": number, "attempts": 0}
    
    await message.reply_text(
        "**Guess the Number!**\n"
        "I have picked a number between 1 and 100.\n"
        "Send your guess in the chat!"
    )

@Client.on_message(filters.command("endguess"))
async def end_guess(client: Client, message: Message):
    if message.chat.id in GUESS_GAMES:
        num = GUESS_GAMES[message.chat.id]["number"]
        del GUESS_GAMES[message.chat.id]
        await message.reply_text(f"Game ended. The number was **{num}**.")

@Client.on_message(filters.group & filters.text, group=3)
async def guess_handler(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in GUESS_GAMES:
        return
        
    try:
        guess = int(message.text)
    except:
        return
        
    game = GUESS_GAMES[chat_id]
    target = game["number"]
    game["attempts"] += 1
    
    if guess == target:
        del GUESS_GAMES[chat_id]
        reward = max(100 - game["attempts"] * 5, 10)
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


# ===== HANGMAN =====
@Client.on_message(filters.command("hangman"))
async def hangman_start(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id in HANGMAN_GAMES:
        return await message.reply_text("A hangman game is already in progress! Use /endhangman")
    
    word = random.choice(HANGMAN_WORDS).lower()
    HANGMAN_GAMES[chat_id] = {
        "word": word,
        "guessed": set(),
        "lives": 6
    }
    
    display = " ".join("_" if c.isalpha() else c for c in word)
    await message.reply_text(
        f"**Hangman!**\n\n`{display}`\n\nLives: 6\n\n"
        f"Guess a letter by typing it!"
    )

@Client.on_message(filters.command("endhangman"))
async def hangman_end(client: Client, message: Message):
    if message.chat.id in HANGMAN_GAMES:
        word = HANGMAN_GAMES[message.chat.id]["word"]
        del HANGMAN_GAMES[message.chat.id]
        await message.reply_text(f"Game ended. The word was: **{word}**")

@Client.on_message(filters.group & filters.text & filters.regex(r"^[a-zA-Z]$"), group=4)
async def hangman_guess(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in HANGMAN_GAMES:
        return
    
    game = HANGMAN_GAMES[chat_id]
    letter = message.text.lower()
    
    if letter in game["guessed"]:
        return await message.reply_text("Already guessed!")
    
    game["guessed"].add(letter)
    
    if letter in game["word"]:
        display = " ".join(c if c in game["guessed"] or not c.isalpha() else "_" for c in game["word"])
        
        if "_" not in display:
            del HANGMAN_GAMES[chat_id]
            await db.add_balance(message.from_user.id, 50)
            await db.update_game_stats(message.from_user.id, "hangman", True)
            return await message.reply_text(f"**You win!** The word was: **{game['word']}**\nReward: 50 coins")
        
        await message.reply_text(f"Correct!\n\n`{display}`\n\nLives: {game['lives']}")
    else:
        game["lives"] -= 1
        if game["lives"] <= 0:
            del HANGMAN_GAMES[chat_id]
            return await message.reply_text(f"**Game Over!** The word was: **{game['word']}**")
        
        display = " ".join(c if c in game["guessed"] or not c.isalpha() else "_" for c in game["word"])
        await message.reply_text(f"Wrong!\n\n`{display}`\n\nLives: {game['lives']}")


# ===== WORD SCRAMBLE =====
@Client.on_message(filters.command("scramble"))
async def scramble_start(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id in SCRAMBLE_GAMES:
        return await message.reply_text("A scramble game is in progress!")
    
    word = random.choice(HANGMAN_WORDS)
    scrambled = list(word)
    random.shuffle(scrambled)
    scrambled = "".join(scrambled)
    
    SCRAMBLE_GAMES[chat_id] = {"word": word, "scrambled": scrambled}
    
    await message.reply_text(
        f"**Word Scramble!**\n\n"
        f"Unscramble: `{scrambled}`\n\n"
        f"Type the correct word!"
    )

@Client.on_message(filters.group & filters.text, group=5)
async def scramble_guess(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in SCRAMBLE_GAMES:
        return
    
    game = SCRAMBLE_GAMES[chat_id]
    if message.text.lower() == game["word"]:
        del SCRAMBLE_GAMES[chat_id]
        await db.add_balance(message.from_user.id, 30)
        await db.update_game_stats(message.from_user.id, "scramble", True)
        await message.reply_text(f"**Correct!** {message.from_user.mention} wins!\nReward: 30 coins")


# ===== TIC-TAC-TOE =====
def render_ttt_board(board):
    symbols = {0: "⬜", 1: "❌", 2: "⭕"}
    rows = []
    for i in range(3):
        row = ""
        for j in range(3):
            row += symbols[board[i*3 + j]]
        rows.append(row)
    return "\n".join(rows)

def check_ttt_winner(board):
    lines = [
        [0,1,2], [3,4,5], [6,7,8],  # rows
        [0,3,6], [1,4,7], [2,5,8],  # cols
        [0,4,8], [2,4,6]  # diagonals
    ]
    for line in lines:
        if board[line[0]] == board[line[1]] == board[line[2]] != 0:
            return board[line[0]]
    if 0 not in board:
        return -1  # Draw
    return 0  # Game continues

@Client.on_message(filters.command("ttt") & filters.group)
async def ttt_start(client: Client, message: Message):
    chat_id = message.chat.id
    
    if chat_id in TTT_GAMES:
        return await message.reply_text("A game is already in progress!")
    
    if not message.reply_to_message:
        return await message.reply_text("Reply to someone to challenge them!")
    
    player1 = message.from_user.id
    player2 = message.reply_to_message.from_user.id
    
    if player1 == player2:
        return await message.reply_text("You can't play against yourself!")
    
    TTT_GAMES[chat_id] = {
        "board": [0] * 9,
        "player1": player1,
        "player2": player2,
        "turn": player1,
        "p1_name": message.from_user.first_name,
        "p2_name": message.reply_to_message.from_user.first_name
    }
    
    buttons = []
    for i in range(3):
        row = []
        for j in range(3):
            idx = i*3 + j
            row.append(InlineKeyboardButton("⬜", callback_data=f"ttt_{idx}"))
        buttons.append(row)
    
    game = TTT_GAMES[chat_id]
    await message.reply_text(
        f"**Tic-Tac-Toe**\n\n{game['p1_name']} (X) vs {game['p2_name']} (O)\n\n{game['p1_name']}'s turn!",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r"^ttt_"))
async def ttt_callback(client: Client, callback: CallbackQuery):
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
    winner = check_ttt_winner(game["board"])
    
    # Update buttons
    symbols = {0: "⬜", 1: "❌", 2: "⭕"}
    buttons = []
    for i in range(3):
        row = []
        for j in range(3):
            cell_idx = i*3 + j
            row.append(InlineKeyboardButton(symbols[game["board"][cell_idx]], callback_data=f"ttt_{cell_idx}"))
        buttons.append(row)
    
    if winner > 0:
        winner_name = game["p1_name"] if winner == 1 else game["p2_name"]
        winner_id = game["player1"] if winner == 1 else game["player2"]
        del TTT_GAMES[chat_id]
        await db.add_balance(winner_id, 50)
        await db.update_game_stats(winner_id, "ttt", True)
        await callback.message.edit_text(
            f"**{winner_name} wins!**\n\n{render_ttt_board(game['board'])}\nReward: 50 coins"
        )
    elif winner == -1:
        del TTT_GAMES[chat_id]
        await callback.message.edit_text(f"**It's a draw!**\n\n{render_ttt_board(game['board'])}")
    else:
        game["turn"] = game["player2"] if game["turn"] == game["player1"] else game["player1"]
        turn_name = game["p1_name"] if game["turn"] == game["player1"] else game["p2_name"]
        await callback.message.edit_text(
            f"**Tic-Tac-Toe**\n\n{game['p1_name']} (X) vs {game['p2_name']} (O)\n\n{turn_name}'s turn!",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    await callback.answer()


# ===== SLOTS =====
@Client.on_message(filters.command("slots"))
async def slots_game(client: Client, message: Message):
    user_id = message.from_user.id
    bet = 10
    
    if len(message.command) > 1:
        try:
            bet = int(message.command[1])
        except:
            pass
    
    bet = min(max(bet, 10), 1000)  # 10-1000 range
    
    user_data = await db.get_user_data(user_id)
    balance = user_data.get("balance", 0) if user_data else 0
    
    if balance < bet:
        return await message.reply_text(f"Not enough coins! You have {balance} coins.")
    
    await db.add_balance(user_id, -bet)
    
    symbols = ["🍎", "🍊", "🍋", "🍇", "🍒", "⭐", "💎"]
    weights = [30, 25, 20, 15, 7, 2, 1]  # Rarer symbols have lower weight
    
    results = random.choices(symbols, weights=weights, k=3)
    
    multiplier = 0
    if results[0] == results[1] == results[2]:
        if results[0] == "💎":
            multiplier = 50
        elif results[0] == "⭐":
            multiplier = 20
        else:
            multiplier = 5
    elif results[0] == results[1] or results[1] == results[2]:
        multiplier = 2
    
    winnings = bet * multiplier
    if winnings > 0:
        await db.add_balance(user_id, winnings)
    
    result_str = " | ".join(results)
    
    if winnings > 0:
        await message.reply_text(
            f"**SLOTS**\n\n[ {result_str} ]\n\n**YOU WIN!** +{winnings} coins!"
        )
    else:
        await message.reply_text(f"**SLOTS**\n\n[ {result_str} ]\n\nNo match. -{bet} coins")


# ===== GAMBLE =====
@Client.on_message(filters.command("gamble"))
async def gamble_game(client: Client, message: Message):
    user_id = message.from_user.id
    
    if len(message.command) < 2:
        return await message.reply_text("Usage: /gamble <amount>")
    
    try:
        amount = int(message.command[1])
    except:
        return await message.reply_text("Invalid amount.")
    
    amount = min(max(amount, 1), 10000)
    
    user_data = await db.get_user_data(user_id)
    balance = user_data.get("balance", 0) if user_data else 0
    
    if balance < amount:
        return await message.reply_text(f"Not enough coins! You have {balance} coins.")
    
    if random.random() < 0.45:  # 45% win rate
        await db.add_balance(user_id, amount)
        await message.reply_text(f"**You won!** +{amount} coins!\nNew balance: {balance + amount}")
    else:
        await db.add_balance(user_id, -amount)
        await message.reply_text(f"**You lost!** -{amount} coins\nNew balance: {balance - amount}")


# ===== BLACKJACK =====
CARD_VALUES = {
    'A': 11, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
    '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10
}
CARD_SUITS = ['hearts', 'diamonds', 'clubs', 'spades']
SUIT_EMOJIS = {'hearts': '', 'diamonds': '', 'clubs': '', 'spades': ''}

def create_deck():
    deck = []
    for suit in CARD_SUITS:
        for card in CARD_VALUES.keys():
            deck.append((card, suit))
    random.shuffle(deck)
    return deck

def card_to_str(card):
    rank, suit = card
    emoji = SUIT_EMOJIS.get(suit, '')
    return f"{rank}{emoji}"

def hand_to_str(hand):
    return " ".join(card_to_str(c) for c in hand)

def calculate_hand(hand):
    value = 0
    aces = 0
    for card, suit in hand:
        value += CARD_VALUES[card]
        if card == 'A':
            aces += 1
    # Adjust for aces
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value


@Client.on_message(filters.command("blackjack") | filters.command("bj"))
async def blackjack_start(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    game_key = f"{chat_id}_{user_id}"
    
    if game_key in BLACKJACK_GAMES:
        return await message.reply_text("You already have an active blackjack game! Use /hit or /stand")
    
    # Get bet amount
    if len(message.command) < 2:
        bet = 50  # Default bet
    else:
        try:
            bet = int(message.command[1])
        except:
            return await message.reply_text("Usage: /blackjack <bet>")
    
    bet = min(max(bet, 10), 5000)  # 10-5000 range
    
    user_data = await db.get_user_data(user_id)
    balance = user_data.get("balance", 0) if user_data else 0
    
    if balance < bet:
        return await message.reply_text(f"Not enough coins! You have {balance} coins.")
    
    # Deduct bet
    await db.add_balance(user_id, -bet)
    
    # Create deck and deal
    deck = create_deck()
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    
    BLACKJACK_GAMES[game_key] = {
        "deck": deck,
        "player_hand": player_hand,
        "dealer_hand": dealer_hand,
        "bet": bet,
        "user_id": user_id
    }
    
    player_value = calculate_hand(player_hand)
    
    # Check for natural blackjack
    if player_value == 21:
        winnings = int(bet * 2.5)
        await db.add_balance(user_id, winnings)
        await db.update_game_stats(user_id, "blackjack", True)
        del BLACKJACK_GAMES[game_key]
        return await message.reply_text(
            f"**BLACKJACK!**\n\n"
            f"Your hand: {hand_to_str(player_hand)} (21)\n"
            f"Dealer: {hand_to_str(dealer_hand)} ({calculate_hand(dealer_hand)})\n\n"
            f"**You win {winnings} coins!**"
        )
    
    # Create buttons
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Hit", callback_data=f"bj_hit_{user_id}"),
            InlineKeyboardButton("Stand", callback_data=f"bj_stand_{user_id}"),
            InlineKeyboardButton("Double", callback_data=f"bj_double_{user_id}")
        ]
    ])
    
    await message.reply_text(
        f"**Blackjack** | Bet: {bet} coins\n\n"
        f"Your hand: {hand_to_str(player_hand)} ({player_value})\n"
        f"Dealer shows: {card_to_str(dealer_hand[0])} ?\n\n"
        f"Choose your action:",
        reply_markup=buttons
    )


@Client.on_callback_query(filters.regex(r"^bj_(hit|stand|double)_"))
async def blackjack_action(client: Client, callback: CallbackQuery):
    parts = callback.data.split("_")
    action = parts[1]
    target_user = int(parts[2])
    
    if callback.from_user.id != target_user:
        return await callback.answer("Not your game!", show_alert=True)
    
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    game_key = f"{chat_id}_{user_id}"
    
    if game_key not in BLACKJACK_GAMES:
        return await callback.answer("Game not found!", show_alert=True)
    
    game = BLACKJACK_GAMES[game_key]
    player_hand = game["player_hand"]
    dealer_hand = game["dealer_hand"]
    deck = game["deck"]
    bet = game["bet"]
    
    if action == "double":
        # Check if player can afford to double
        user_data = await db.get_user_data(user_id)
        balance = user_data.get("balance", 0) if user_data else 0
        
        if balance < bet:
            return await callback.answer("Not enough coins to double!", show_alert=True)
        
        # Double the bet and deal one more card
        await db.add_balance(user_id, -bet)
        game["bet"] = bet * 2
        bet = game["bet"]
        player_hand.append(deck.pop())
        action = "stand"  # Force stand after double
    
    if action == "hit":
        player_hand.append(deck.pop())
        player_value = calculate_hand(player_hand)
        
        if player_value > 21:
            # Bust
            del BLACKJACK_GAMES[game_key]
            await db.update_game_stats(user_id, "blackjack", False)
            await callback.message.edit_text(
                f"**BUST!**\n\n"
                f"Your hand: {hand_to_str(player_hand)} ({player_value})\n"
                f"Dealer: {hand_to_str(dealer_hand)} ({calculate_hand(dealer_hand)})\n\n"
                f"You lost {bet} coins!"
            )
            return
        
        if player_value == 21:
            # Auto-stand on 21
            action = "stand"
        else:
            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Hit", callback_data=f"bj_hit_{user_id}"),
                    InlineKeyboardButton("Stand", callback_data=f"bj_stand_{user_id}")
                ]
            ])
            await callback.message.edit_text(
                f"**Blackjack** | Bet: {bet} coins\n\n"
                f"Your hand: {hand_to_str(player_hand)} ({player_value})\n"
                f"Dealer shows: {card_to_str(dealer_hand[0])} ?\n\n"
                f"Choose your action:",
                reply_markup=buttons
            )
            return
    
    if action == "stand":
        player_value = calculate_hand(player_hand)
        
        # Dealer plays
        while calculate_hand(dealer_hand) < 17:
            dealer_hand.append(deck.pop())
        
        dealer_value = calculate_hand(dealer_hand)
        
        # Determine winner
        del BLACKJACK_GAMES[game_key]
        
        if dealer_value > 21:
            # Dealer busts
            winnings = bet * 2
            await db.add_balance(user_id, winnings)
            await db.update_game_stats(user_id, "blackjack", True)
            result = f"**Dealer busts! You win {winnings} coins!**"
        elif dealer_value > player_value:
            await db.update_game_stats(user_id, "blackjack", False)
            result = f"**Dealer wins!** You lost {bet} coins."
        elif player_value > dealer_value:
            winnings = bet * 2
            await db.add_balance(user_id, winnings)
            await db.update_game_stats(user_id, "blackjack", True)
            result = f"**You win {winnings} coins!**"
        else:
            # Push - return bet
            await db.add_balance(user_id, bet)
            result = f"**Push!** Bet returned."
        
        await callback.message.edit_text(
            f"**Blackjack Result**\n\n"
            f"Your hand: {hand_to_str(player_hand)} ({player_value})\n"
            f"Dealer: {hand_to_str(dealer_hand)} ({dealer_value})\n\n"
            f"{result}"
        )
    
    await callback.answer()
