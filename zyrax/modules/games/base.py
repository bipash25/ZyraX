"""
Games Base Module

Shared state dictionaries and utility functions for all games.
"""

import time
from typing import Dict, Any


# =============================================================================
# SHARED GAME STATE DICTIONARIES
# =============================================================================

# Word/Number games
TRIVIA_GAMES: Dict[int, Dict[str, Any]] = {}
GUESS_GAMES: Dict[int, Dict[str, Any]] = {}
HANGMAN_GAMES: Dict[int, Dict[str, Any]] = {}
SCRAMBLE_GAMES: Dict[int, Dict[str, Any]] = {}

# Two-player board games
TTT_GAMES: Dict[int, Dict[str, Any]] = {}
C4_GAMES: Dict[int, Dict[str, Any]] = {}

# Gambling games
BLACKJACK_GAMES: Dict[str, Dict[str, Any]] = {}

# Multiplayer games
RR_GAMES: Dict[int, Dict[str, Any]] = {}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_game_age(game: Dict[str, Any]) -> float:
    """Get the age of a game in seconds."""
    return time.time() - game.get("created_at", time.time())


def cleanup_old_games(games_dict: Dict, max_age: int) -> int:
    """Remove games older than max_age seconds. Returns count removed."""
    now = time.time()
    to_remove = [
        key for key, game in games_dict.items()
        if now - game.get("created_at", now) > max_age
    ]
    for key in to_remove:
        del games_dict[key]
    return len(to_remove)


def cleanup_all_games(max_age: int = 3600) -> Dict[str, int]:
    """Cleanup all game dictionaries. Returns counts per game type."""
    results = {}
    
    game_dicts = {
        "trivia": TRIVIA_GAMES,
        "guess": GUESS_GAMES,
        "hangman": HANGMAN_GAMES,
        "scramble": SCRAMBLE_GAMES,
        "ttt": TTT_GAMES,
        "connect4": C4_GAMES,
        "blackjack": BLACKJACK_GAMES,
        "roulette": RR_GAMES,
    }
    
    for name, games in game_dicts.items():
        results[name] = cleanup_old_games(games, max_age)
    
    return results
