"""
Global constants and enums for ZyraX bot
"""
from enum import Enum

# ============================================================================
# TIME LIMITS (in seconds)
# ============================================================================

# Ban/Mute durations
MIN_BAN_DURATION = 30  # 30 seconds
MAX_BAN_DURATION = 31536000  # 365 days
MIN_MUTE_DURATION = 30  # 30 seconds
MAX_MUTE_DURATION = 31536000  # 365 days

# Captcha
CAPTCHA_TIMEOUT_DEFAULT = 120  # 2 minutes
CAPTCHA_MAX_ATTEMPTS = 3
CAPTCHA_KICK_TIMEOUT_DEFAULT = 300  # 5 minutes

# Flood
MAX_FLOOD_LIMIT = 100
MIN_FLOOD_TIMEFRAME = 5
MAX_FLOOD_TIMEFRAME = 60
DEFAULT_FLOOD_TIMEFRAME = 10

# Antiraid
DEFAULT_ANTIRAID_DURATION = 21600  # 6 hours
DEFAULT_ANTIRAID_ACTION_TIME = 3600  # 1 hour

# ============================================================================
# CACHE SETTINGS
# ============================================================================

ADMIN_CACHE_TTL = 600  # 10 minutes
CHAT_SETTINGS_CACHE_TTL = 300  # 5 minutes
USER_CACHE_TTL = 300  # 5 minutes

# ============================================================================
# CONTENT LIMITS (in characters)
# ============================================================================

MAX_FILTER_SIZE = 4096
MAX_NOTE_SIZE = 4096
MAX_RULES_SIZE = 8192
MAX_WELCOME_SIZE = 4096
MAX_GOODBYE_SIZE = 4096
MAX_CUSTOM_TITLE_LENGTH = 16
MAX_REASON_LENGTH = 200
MAX_FED_NAME_LENGTH = 64

# ============================================================================
# UI/UX SETTINGS
# ============================================================================

AUTO_DELETE_DELAY = 10  # seconds for auto-deleting messages
CATEGORIES_PER_PAGE = 8  # categories per help page

# ============================================================================
# XP/LEVELING SYSTEM
# ============================================================================

XP_PER_MESSAGE = 10
XP_COOLDOWN = 60  # seconds between XP awards
MAX_LEVEL = 100

# ============================================================================
# ECONOMY SYSTEM
# ============================================================================

DAILY_REWARD_MIN = 100
DAILY_REWARD_MAX = 500
WORK_REWARD_MIN = 50
WORK_REWARD_MAX = 200
WORK_COOLDOWN = 3600  # 1 hour
GAMBLE_MIN = 10
GAMBLE_MAX = 10000
STARTING_BALANCE = 1000

# ============================================================================
# RATE LIMITING
# ============================================================================

DEFAULT_RATE_LIMIT_CALLS = 5
DEFAULT_RATE_LIMIT_WINDOW = 60  # seconds
COMMAND_RATE_LIMIT_CALLS = 3
COMMAND_RATE_LIMIT_WINDOW = 60

# ============================================================================
# FLOOD TRACKER CLEANUP
# ============================================================================

FLOOD_TRACKER_CLEANUP_INTERVAL = 300  # 5 minutes
FLOOD_TRACKER_CLEANUP_THRESHOLD = 300  # 5 minutes

# ============================================================================
# CAPTCHA MODES
# ============================================================================

CAPTCHA_MODES = ['math', 'button', 'text']

# ============================================================================
# ENUMS
# ============================================================================

class FloodMode(Enum):
    """Flood action modes"""
    WARN = "warn"
    MUTE = "mute"
    KICK = "kick"
    BAN = "ban"
    TBAN = "tban"
    TMUTE = "tmute"


class CaptchaMode(Enum):
    """Captcha verification modes"""
    MATH = "math"
    BUTTON = "button"
    TEXT = "text"


class WarnAction(Enum):
    """Warning threshold actions"""
    BAN = "ban"
    KICK = "kick"
    MUTE = "mute"
    TBAN = "tban"
    TMUTE = "tmute"


class LockType(Enum):
    """Types of content that can be locked"""
    TEXT = "text"
    MEDIA = "media"
    STICKER = "sticker"
    GIF = "gif"
    URL = "url"
    FORWARD = "forward"
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    VOICE = "voice"
    DOCUMENT = "document"
    CONTACT = "contact"
    LOCATION = "location"
    POLL = "poll"
    MENTION = "mention"
    HASHTAG = "hashtag"
    COMMAND = "command"


class BlocklistAction(Enum):
    """Actions for blocklist violations"""
    NOTHING = "nothing"
    WARN = "warn"
    MUTE = "mute"
    KICK = "kick"
    BAN = "ban"


# ============================================================================
# PERMISSION STRINGS
# ============================================================================

REQUIRED_BOT_PERMISSIONS = [
    "can_delete_messages",
    "can_restrict_members",
    "can_pin_messages",
    "can_invite_users"
]

PROMOTE_PERMISSIONS = {
    "can_change_info": True,
    "can_delete_messages": True,
    "can_invite_users": True,
    "can_restrict_members": True,
    "can_pin_messages": True,
    "can_promote_members": False,  # Don't grant by default
    "can_manage_chat": True,
    "can_manage_video_chats": True
}

# ============================================================================
# FILE PATHS
# ============================================================================

DATA_DIR = "data"
LOGS_DIR = "data/logs"
SESSIONS_DIR = "data/sessions"
BACKUPS_DIR = "data/backups"

# ============================================================================
# COMMAND CATEGORIES (for help display order)
# ============================================================================

COMMAND_CATEGORIES = [
    'admin',
    'moderation',
    'warnings',
    'antiflood',
    'antiraid',
    'approval',
    'captcha',
    'locks',
    'filters',
    'blocklists',
    'notes',
    'greetings',
    'rules',
    'federation',
    'pins',
    'reports',
    'clean',
    'logs',
    'backup',
    'leveling',
    'economy',
    'profile',
    'fun',
    'info',
    'misc',
    'owner'
]

# ============================================================================
# ERROR MESSAGES
# ============================================================================

ERROR_NOT_ADMIN = "❌ You must be an administrator to use this command."
ERROR_NOT_BOT_ADMIN = "❌ I need administrator permissions to execute this command."
ERROR_USER_NOT_FOUND = "❌ Could not find the specified user."
ERROR_INVALID_DURATION = "❌ Invalid duration format. Use: 5m, 2h, 3d, 1w"
ERROR_PERMISSION_DENIED = "❌ You don't have permission to perform this action."
ERROR_DATABASE_ERROR = "❌ A database error occurred. Please try again later."
ERROR_GENERIC = "❌ An unexpected error occurred. Please try again."

SUCCESS_BAN = "🔨 {user} has been banned"
SUCCESS_UNBAN = "✅ {user} has been unbanned"
SUCCESS_MUTE = "🔇 {user} has been muted"
SUCCESS_UNMUTE = "🔊 {user} has been unmuted"
SUCCESS_WARN = "⚠️ {user} has been warned"
SUCCESS_KICK = "👢 {user} has been kicked"

