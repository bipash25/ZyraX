"""
ZyraX Bot Constants

Centralized configuration for all magic numbers, limits, and default values.
"""

from enum import Enum, auto
from typing import Dict, List


# =============================================================================
# BOT LIMITS
# =============================================================================

class Limits:
    """Rate limits, size limits, and operational boundaries."""
    
    # Warning System
    MAX_WARNS: int = 3
    WARN_REASON_MAX_LENGTH: int = 500
    
    # Music System
    MAX_QUEUE_SIZE: int = 50
    MAX_AUDIO_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    MAX_AUDIO_DURATION: int = 3600  # 1 hour in seconds
    
    # Notes & Filters
    MAX_NOTE_LENGTH: int = 4096
    MAX_FILTER_LENGTH: int = 4096
    MAX_NOTES_PER_CHAT: int = 200
    MAX_FILTERS_PER_CHAT: int = 200
    
    # Games
    MAX_GAME_IDLE_TIME: int = 3600  # 1 hour
    MAX_CONCURRENT_GAMES: int = 5  # Per chat
    
    # Economy
    MAX_BET_AMOUNT: int = 10000
    MIN_BET_AMOUNT: int = 10
    MAX_TRANSFER_AMOUNT: int = 100000
    
    # Rate Limiting
    DEFAULT_RATE_LIMIT_WINDOW: int = 60  # seconds
    DEFAULT_RATE_LIMIT_MAX: int = 10  # attempts
    ADMIN_COMMAND_RATE_LIMIT: int = 5
    GAME_COMMAND_RATE_LIMIT: int = 3
    AI_COMMAND_RATE_LIMIT: int = 5
    
    # Anti-Spam
    FLOOD_WINDOW: int = 5  # seconds
    MEDIA_SPAM_WINDOW: int = 30  # seconds
    MAX_MENTIONS_DEFAULT: int = 5
    CAPS_THRESHOLD: float = 0.7  # 70% caps
    MIN_CAPS_CHARS: int = 10  # Minimum characters to check
    
    # Captcha
    CAPTCHA_TIMEOUT: int = 60  # seconds
    
    # Cache TTL (seconds)
    ADMIN_CACHE_TTL: int = 300  # 5 minutes
    NOTE_CACHE_TTL: int = 600  # 10 minutes
    SETTINGS_CACHE_TTL: int = 300  # 5 minutes
    USER_DATA_CACHE_TTL: int = 300  # 5 minutes
    FLOOD_LIMIT_CACHE_TTL: int = 300  # 5 minutes
    
    # Database
    MONGO_MAX_POOL_SIZE: int = 50
    MONGO_MIN_POOL_SIZE: int = 10
    MONGO_MAX_IDLE_TIME_MS: int = 45000
    
    # Telegram Message Limits
    MAX_MESSAGE_LENGTH: int = 4096
    MAX_CAPTION_LENGTH: int = 1024
    MAX_ADMIN_TITLE_LENGTH: int = 16
    MAX_BUTTONS_PER_ROW: int = 8
    MAX_BUTTON_ROWS: int = 100
    
    # Dashboard
    DEFAULT_DASHBOARD_PORT: int = 8080
    DEFAULT_DASHBOARD_HOST: str = "0.0.0.0"


# =============================================================================
# REWARDS & ECONOMY
# =============================================================================

class Rewards:
    """Game rewards and economy constants."""
    
    # Daily & Work
    DAILY_MIN: int = 100
    DAILY_MAX: int = 500
    WORK_MIN: int = 10
    WORK_MAX: int = 100
    WORK_COOLDOWN: int = 300  # 5 minutes
    
    # Games
    TRIVIA_WIN: int = 25
    HANGMAN_WIN: int = 50
    SCRAMBLE_WIN: int = 30
    GUESS_BASE_REWARD: int = 100
    GUESS_PENALTY_PER_ATTEMPT: int = 5
    GUESS_MIN_REWARD: int = 10
    TTT_WIN: int = 50
    CONNECT4_WIN: int = 75
    
    # Gambling
    GAMBLE_WIN_RATE: float = 0.45  # 45% win rate
    SLOTS_JACKPOT_MULTIPLIER: int = 50
    SLOTS_STAR_MULTIPLIER: int = 20
    SLOTS_NORMAL_MULTIPLIER: int = 5
    SLOTS_TWO_MATCH_MULTIPLIER: int = 2
    BLACKJACK_WIN_MULTIPLIER: int = 2
    BLACKJACK_NATURAL_MULTIPLIER: float = 2.5


# =============================================================================
# TIMEOUTS & INTERVALS
# =============================================================================

class Timeouts:
    """Timeout and interval constants in seconds."""
    
    # Scheduler
    SCHEDULER_INTERVAL: int = 30
    BACKUP_INTERVAL: int = 86400  # 24 hours
    BACKUP_RETRY_INTERVAL: int = 3600  # 1 hour
    
    # Games
    GAME_CLEANUP_INTERVAL: int = 300  # 5 minutes
    GAME_MAX_AGE: int = 3600  # 1 hour
    
    # Raid Mode
    RAID_DEFAULT_DURATION: int = 3600  # 1 hour
    
    # Mutes
    MUTE_CACHE_TTL: int = 60
    
    # API
    HTTP_TIMEOUT: int = 30
    GEMINI_TIMEOUT: int = 60
    YT_DLP_TIMEOUT: int = 120
    
    # Shutdown
    GRACEFUL_SHUTDOWN_TIMEOUT: int = 10


# =============================================================================
# SLOT MACHINE SYMBOLS
# =============================================================================

class Slots:
    """Slot machine configuration."""
    
    SYMBOLS: List[str] = ["🍎", "🍊", "🍋", "🍇", "🍒", "⭐", "💎"]
    WEIGHTS: List[int] = [30, 25, 20, 15, 7, 2, 1]
    
    JACKPOT_SYMBOL: str = "💎"
    SPECIAL_SYMBOL: str = "⭐"


# =============================================================================
# WORK JOBS
# =============================================================================

WORK_JOBS: List[str] = [
    "barista", "programmer", "taxi driver", "chef", 
    "teacher", "artist", "musician", "writer",
    "designer", "engineer", "doctor", "pilot"
]


# =============================================================================
# HANGMAN WORDS
# =============================================================================

HANGMAN_WORDS: List[str] = [
    "python", "telegram", "programming", "developer", "keyboard", "computer",
    "algorithm", "database", "internet", "software", "hardware", "network",
    "security", "encryption", "function", "variable", "boolean", "integer",
    "framework", "library", "compiler", "debugging", "interface", "protocol"
]


# =============================================================================
# BLACKJACK
# =============================================================================

class Blackjack:
    """Blackjack game configuration."""
    
    CARD_VALUES: Dict[str, int] = {
        'A': 11, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
        '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10
    }
    
    SUITS: List[str] = ['hearts', 'diamonds', 'clubs', 'spades']
    
    SUIT_EMOJIS: Dict[str, str] = {
        'hearts': '♥️',
        'diamonds': '♦️', 
        'clubs': '♣️',
        'spades': '♠️'
    }
    
    DEALER_STAND_VALUE: int = 17
    BLACKJACK_VALUE: int = 21


# =============================================================================
# ANTI-SPAM PATTERNS
# =============================================================================

class AntiSpam:
    """Anti-spam patterns and known bad domains."""
    
    SUSPICIOUS_PATTERNS: List[str] = [
        r't\.me/\+[a-zA-Z0-9_-]+',  # Private group invites
        r'bit\.ly', r'tinyurl', r'goo\.gl', r'is\.gd',  # URL shorteners
        r'discord\.gg', r'discord\.com/invite',  # Discord invites
    ]
    
    PHISHING_KEYWORDS: List[str] = [
        'telegramverify', 'telegram-verify', 'tg-verify',
        'cryptoairdrop', 'free-nft', 'usdt-giveaway',
        'wallet-connect', 'metamask-sync', 'claim-token',
        'verify-wallet', 'nft-drop', 'eth-giveaway'
    ]


# =============================================================================
# RADIO STATIONS
# =============================================================================

RADIO_STATIONS: Dict[str, Dict[str, str]] = {
    "lofi": {
        "name": "Lofi Hip Hop",
        "url": "https://streams.ilovemusic.de/iloveradio17.mp3",
        "genre": "Chill"
    },
    "jazz": {
        "name": "Smooth Jazz",
        "url": "https://strw3.openstream.co/654?aw_0_1st.collession=default",
        "genre": "Jazz"
    },
    "classical": {
        "name": "Classical Radio",
        "url": "https://live.musopen.org:8085/streamvbr0",
        "genre": "Classical"
    },
    "pop": {
        "name": "Pop Hits",
        "url": "https://streams.ilovemusic.de/iloveradio1.mp3",
        "genre": "Pop"
    },
    "rock": {
        "name": "Rock Radio",
        "url": "https://streams.ilovemusic.de/iloveradio16.mp3",
        "genre": "Rock"
    },
    "electronic": {
        "name": "Electronic Beats",
        "url": "https://streams.ilovemusic.de/iloveradio2.mp3",
        "genre": "Electronic"
    },
    "hiphop": {
        "name": "Hip Hop Hits",
        "url": "https://streams.ilovemusic.de/iloveradio3.mp3",
        "genre": "Hip Hop"
    },
    "ambient": {
        "name": "Ambient Chill",
        "url": "https://ice2.somafm.com/dronezone-128-mp3",
        "genre": "Ambient"
    }
}


# =============================================================================
# MESSAGE TEMPLATES
# =============================================================================

class Messages:
    """Standard message templates."""
    
    # Errors
    NO_PERMISSION = "You don't have permission to do this."
    PERMISSION_DENIED = "Permission denied."
    USER_NOT_FOUND = "User not found."
    RATE_LIMITED = "Slow down! You're being rate limited."
    BOT_NO_ADMIN = "I need admin rights to do this!"
    BOT_NOT_ADMIN = "I need admin rights to do this!"
    ADMIN_REQUIRED = "You need to be an admin to use this command!"
    OWNER_REQUIRED = "Only the bot owner can use this command!"
    INVALID_ARGS = "Invalid arguments. Check /help for usage."
    ERROR_GENERIC = "Something went wrong. Please try again."
    
    # Success
    DONE = "Done!"
    SUCCESS = "Success!"
    
    # Games
    GAME_ALREADY_ACTIVE = "A game is already in progress in this chat."
    NOT_YOUR_TURN = "It's not your turn!"
    NOT_IN_GAME = "You're not in this game!"
    
    # Economy
    INSUFFICIENT_FUNDS = "Insufficient funds!"
    CANT_PAY_SELF = "You can't pay yourself."
    CANT_PAY_BOT = "You can't pay bots."


# =============================================================================
# CURRENCY
# =============================================================================

CURRENCY_NAME: str = "ZyraCoins"
CURRENCY_SYMBOL: str = "💰"


# =============================================================================
# TIC-TAC-TOE SYMBOLS
# =============================================================================

class TTT:
    """Tic-Tac-Toe symbols."""
    
    EMPTY: str = "⬜"
    X: str = "❌"
    O: str = "⭕"
    
    SYMBOLS: Dict[int, str] = {0: EMPTY, 1: X, 2: O}


# =============================================================================
# CONNECT FOUR SYMBOLS  
# =============================================================================

class ConnectFour:
    """Connect Four symbols."""
    
    EMPTY: str = "⚪"
    PLAYER1: str = "🔴"
    PLAYER2: str = "🟡"
    
    SYMBOLS: Dict[int, str] = {0: EMPTY, 1: PLAYER1, 2: PLAYER2}
    
    ROWS: int = 6
    COLS: int = 7
    WIN_LENGTH: int = 4
