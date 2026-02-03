"""
Blackjack Game Module
"""

import time
import random
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from zyrax.database.mongo import db
from zyrax.utils.errors import error_handler
from zyrax.utils.ratelimit import rate_limit
from zyrax.constants import Limits, Rewards, Blackjack as BJ
from .base import BLACKJACK_GAMES


def create_deck() -> list:
    """Create and shuffle a standard deck of cards."""
    deck = [
        (card, suit)
        for suit in BJ.SUITS
        for card in BJ.CARD_VALUES.keys()
    ]
    random.shuffle(deck)
    return deck


def card_to_str(card: tuple) -> str:
    """Convert card tuple to display string."""
    rank, suit = card
    emoji = BJ.SUIT_EMOJIS.get(suit, '')
    return f"{rank}{emoji}"


def hand_to_str(hand: list) -> str:
    """Convert hand to display string."""
    return " ".join(card_to_str(c) for c in hand)


def calculate_hand(hand: list) -> int:
    """Calculate hand value with ace adjustment."""
    value = 0
    aces = 0
    for card, suit in hand:
        value += BJ.CARD_VALUES[card]
        if card == 'A':
            aces += 1
    # Adjust for aces
    while value > BJ.BLACKJACK_VALUE and aces:
        value -= 10
        aces -= 1
    return value


@Client.on_message(filters.command("blackjack") | filters.command("bj"))
@rate_limit(max_attempts=3, window=60)
@error_handler
async def blackjack_start(client: Client, message: Message):
    """Start a blackjack game."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    game_key = f"{chat_id}_{user_id}"
    
    if game_key in BLACKJACK_GAMES:
        return await message.reply_text(
            "You already have an active blackjack game! Use the buttons to play."
        )
    
    # Get bet amount
    bet = 50  # Default bet
    if len(message.command) > 1:
        try:
            bet = int(message.command[1])
        except ValueError:
            return await message.reply_text("Usage: /blackjack <bet>")
    
    bet = min(max(bet, Limits.MIN_BET_AMOUNT), 5000)
    
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
        "user_id": user_id,
        "created_at": time.time()
    }
    
    player_value = calculate_hand(player_hand)
    
    # Check for natural blackjack
    if player_value == BJ.BLACKJACK_VALUE:
        winnings = int(bet * Rewards.BLACKJACK_NATURAL_MULTIPLIER)
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
    """Handle blackjack actions."""
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
        
        if player_value > BJ.BLACKJACK_VALUE:
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
        
        if player_value == BJ.BLACKJACK_VALUE:
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
        while calculate_hand(dealer_hand) < BJ.DEALER_STAND_VALUE:
            dealer_hand.append(deck.pop())
        
        dealer_value = calculate_hand(dealer_hand)
        
        # Determine winner
        del BLACKJACK_GAMES[game_key]
        
        if dealer_value > BJ.BLACKJACK_VALUE:
            # Dealer busts
            winnings = bet * Rewards.BLACKJACK_WIN_MULTIPLIER
            await db.add_balance(user_id, winnings)
            await db.update_game_stats(user_id, "blackjack", True)
            result = f"**Dealer busts! You win {winnings} coins!**"
        elif dealer_value > player_value:
            await db.update_game_stats(user_id, "blackjack", False)
            result = f"**Dealer wins!** You lost {bet} coins."
        elif player_value > dealer_value:
            winnings = bet * Rewards.BLACKJACK_WIN_MULTIPLIER
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
