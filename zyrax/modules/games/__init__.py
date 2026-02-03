"""
Games Package

Split from the monolithic games.py (1120 lines) into separate modules:
- base.py: Shared game state dictionaries and cleanup utilities
- quick.py: Dice, dart, coin flip, rock-paper-scissors
- trivia.py: Trivia questions from Open Trivia DB
- word.py: Hangman and word scramble games
- guess.py: Guess the number game
- gambling.py: Slots and gamble (50/50)
- blackjack.py: Blackjack card game
- tictactoe.py: Two-player tic-tac-toe
- connect_four.py: Two-player Connect Four
- roulette.py: Multiplayer Russian Roulette
"""

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
/ttt (reply) - Tic-Tac-Toe challenge
/c4 (reply) - Connect Four challenge

**Multiplayer Games:**
/rr [bet] - Start Russian Roulette
/rrjoin - Join Russian Roulette
/rrstart - Start the game
/rrcancel - Cancel game

**Gambling (requires coins):**
/gamble <amount> - 50/50 double or nothing
/blackjack <bet> - Play blackjack
"""

# Import all submodules to register handlers
from . import quick
from . import trivia
from . import word
from . import guess
from . import gambling
from . import blackjack
from . import tictactoe
from . import connect_four
from . import roulette

# Export base module for game state access
from .base import (
    TRIVIA_GAMES,
    GUESS_GAMES,
    HANGMAN_GAMES,
    SCRAMBLE_GAMES,
    TTT_GAMES,
    C4_GAMES,
    BLACKJACK_GAMES,
    RR_GAMES,
    cleanup_all_games,
)
