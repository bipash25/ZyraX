"""
Locktypes command - Show all available lock types
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, log_command
from .commands import LOCK_TYPES

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "locktypes",
    "description": "Show all available lock types",
    "usage": "/locktypes - List all lockable content types",
    "category": "locks",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /locktypes command
    
    Show all available lock types.
    """
    # Group lock types by category
    media_types = {
        'photo': 'Photos/Images',
        'video': 'Videos',
        'audio': 'Audio files',
        'document': 'Documents/Files',
        'sticker': 'Stickers',
        'animation': 'GIFs/Animations',
        'voice': 'Voice messages',
        'video_note': 'Video notes/circles'
    }
    
    message_types = {
        'url': 'URLs/Links',
        'forward': 'Forwarded messages',
        'mention': 'Mentions (@username)',
        'hashtag': 'Hashtags (#tag)',
        'command': 'Bot commands',
        'text': 'Text messages'
    }
    
    special_types = {
        'poll': 'Polls',
        'location': 'Location sharing',
        'contact': 'Contact sharing',
        'game': 'Games',
        'invoice': 'Payment invoices'
    }
    
    permission_types = {
        'invite': 'Adding members',
        'pin': 'Pinning messages',
        'info': 'Changing chat info'
    }
    
    combination_types = {
        'media': 'All media types',
        'all': 'All message types'
    }
    
    message = "🔒 <b>Available Lock Types</b>\n\n"
    
    message += "<b>📸 Media Types:</b>\n"
    for key, value in media_types.items():
        message += f"  • <code>{key}</code> - {value}\n"
    message += "\n"
    
    message += "<b>💬 Message Types:</b>\n"
    for key, value in message_types.items():
        message += f"  • <code>{key}</code> - {value}\n"
    message += "\n"
    
    message += "<b>🎯 Special Types:</b>\n"
    for key, value in special_types.items():
        message += f"  • <code>{key}</code> - {value}\n"
    message += "\n"
    
    message += "<b>🔧 Permission Types:</b>\n"
    for key, value in permission_types.items():
        message += f"  • <code>{key}</code> - {value}\n"
    message += "\n"
    
    message += "<b>📦 Combinations:</b>\n"
    for key, value in combination_types.items():
        message += f"  • <code>{key}</code> - {value}\n"
    message += "\n"
    
    message += (
        "💡 <b>Usage:</b>\n"
        "  • <code>/lock &lt;type&gt;</code> - Lock a type\n"
        "  • <code>/unlock &lt;type&gt;</code> - Unlock a type\n"
        "  • <code>/locks</code> - Show active locks\n\n"
        "Example: <code>/lock photo</code>"
    )
    
    await update.message.reply_html(message)