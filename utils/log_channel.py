"""
Log channel utility - Send logs to configured channel
"""
import logging
from typing import Optional
from utils.time_parser import now_utc
from telegram import Bot

logger = logging.getLogger(__name__)


async def send_log_message(
    bot: Bot,
    db,
    chat_id: int,
    action_type: str,
    admin_mention: str,
    target_mention: Optional[str] = None,
    reason: Optional[str] = None,
    extra_info: Optional[str] = None
) -> bool:
    """
    Send action log to configured log channel
    
    Args:
        bot: Bot instance
        db: Database instance
        chat_id: Source chat ID
        action_type: Type of action (ban, warn, etc.)
        admin_mention: HTML mention of admin who performed action
        target_mention: HTML mention of target user (if applicable)
        reason: Reason for action
        extra_info: Additional information
        
    Returns:
        True if sent successfully
    """
    if not db:
        return False
    
    try:
        # Get chat settings
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        
        if not chat_doc or not chat_doc.get('log_channel_id'):
            return False  # No log channel set
        
        log_channel_id = chat_doc['log_channel_id']
        
        # Build log message
        timestamp = now_utc().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        message = f"📋 <b>Admin Action Log</b>\n\n"
        message += f"<b>Action:</b> {action_type.replace('_', ' ').title()}\n"
        message += f"<b>Time:</b> {timestamp}\n"
        message += f"<b>Admin:</b> {admin_mention}\n"
        
        if target_mention:
            message += f"<b>Target:</b> {target_mention}\n"
        
        if reason:
            message += f"<b>Reason:</b> {reason}\n"
        
        if extra_info:
            message += f"\n{extra_info}"
        
        # Send to log channel
        await bot.send_message(
            log_channel_id,
            message,
            parse_mode='HTML'
        )
        
        logger.debug(f"Sent log message to channel {log_channel_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending log message: {e}")
        return False

