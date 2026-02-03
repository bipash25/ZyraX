"""
ZyraX Bot

All-in-one Telegram bot with admin tools, games, music, AI, and more.
"""

__version__ = "2.1.0"
__author__ = "bipash25"
__license__ = "MIT"

VERSION_INFO = {
    "major": 2,
    "minor": 1,
    "patch": 0,
    "release": "stable",
    "codename": "Phoenix"
}


def get_version() -> str:
    """Get the current version string."""
    return __version__


def get_version_info() -> dict:
    """Get detailed version information."""
    return VERSION_INFO.copy()
