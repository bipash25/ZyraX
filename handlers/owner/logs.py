"""
Get recent log files
"""
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import owner_only, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "logs",
    "aliases": ["getlogs", "log"],
    "description": "Get recent bot logs",
    "usage": "/logs [lines]",
    "category": "owner",
    "scope": ["private"]
}


@log_command
@owner_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Send recent log file to owner
    """
    try:
        # Get number of lines
        lines = 100
        if context.args and context.args[0].isdigit():
            lines = min(int(context.args[0]), 1000)  # Max 1000 lines
        
        # Get log file path
        log_file = Path("data/logs/bot.log")
        
        if not log_file.exists():
            await update.message.reply_text("❌ Log file not found")
            return
        
        # Read last N lines
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]
        
        # Create temporary file with recent logs
        temp_log = Path("data/logs/recent.log")
        with open(temp_log, 'w', encoding='utf-8') as f:
            f.writelines(recent_lines)
        
        # Send file
        await update.message.reply_document(
            document=open(temp_log, 'rb'),
            filename=f"bot_logs_last_{lines}_lines.log",
            caption=f"📝 Last {lines} lines of bot logs"
        )
        
        # Clean up
        temp_log.unlink()
        
    except Exception as e:
        logger.error(f"Error sending logs: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

