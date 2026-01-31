"""
Rate limiting utilities for captcha system
Prevents join/leave spam attacks
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Rate limiting constants
CAPTCHA_RATE_LIMIT_WINDOW = 300  # 5 minutes
MAX_JOINS_PER_WINDOW = 3
TEMP_BAN_DURATION = 3600  # 1 hour


async def check_rate_limit(db, chat_id: int, user_id: int) -> bool:
    """
    Check if user exceeded rate limit for captcha attempts
    
    Args:
        db: Database instance
        chat_id: Chat ID
        user_id: User ID
    
    Returns:
        True if rate limited (exceeded limit), False otherwise
    """
    if db is None:
        return False
    
    try:
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=CAPTCHA_RATE_LIMIT_WINDOW)
        
        # Count recent attempts
        recent_attempts = await db.captcha_attempts.count_documents({
            "chat_id": str(chat_id),
            "user_id": str(user_id),
            "timestamp": {"$gte": window_start}
        })
        
        is_limited = recent_attempts >= MAX_JOINS_PER_WINDOW
        
        if is_limited:
            logger.warning(
                f"Rate limit exceeded for user {user_id} in chat {chat_id}: "
                f"{recent_attempts} attempts in last {CAPTCHA_RATE_LIMIT_WINDOW}s"
            )
        
        return is_limited
        
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}")
        return False


async def log_captcha_attempt(db, chat_id: int, user_id: int) -> bool:
    """
    Log a captcha attempt for rate limiting
    
    Args:
        db: Database instance
        chat_id: Chat ID
        user_id: User ID
    
    Returns:
        True if logged successfully
    """
    if db is None:
        return False
    
    try:
        # Insert attempt record
        await db.captcha_attempts.insert_one({
            "chat_id": str(chat_id),
            "user_id": str(user_id),
            "timestamp": datetime.now(timezone.utc)
        })
        
        # Cleanup old attempts (older than 2x window for safety)
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=CAPTCHA_RATE_LIMIT_WINDOW * 2)
        await db.captcha_attempts.delete_many({
            "timestamp": {"$lt": cutoff}
        })
        
        logger.debug(f"Logged captcha attempt for user {user_id} in chat {chat_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error logging captcha attempt: {e}")
        return False


async def handle_rate_limit_violation(context, chat_id: int, user_id: int, user_mention: str):
    """
    Handle a rate limit violation - temp ban user
    
    Args:
        context: Bot context
        chat_id: Chat ID
        user_id: User ID
        user_mention: User mention HTML
    """
    try:
        # Temp ban for 1 hour
        ban_until = datetime.now(timezone.utc) + timedelta(seconds=TEMP_BAN_DURATION)
        
        await context.bot.ban_chat_member(
            chat_id,
            user_id,
            until_date=ban_until
        )
        
        await context.bot.send_message(
            chat_id,
            f"⚠️ <b>Suspicious Activity Detected</b>\n\n"
            f"{user_mention} was temporarily banned for {TEMP_BAN_DURATION // 3600} hour(s) "
            f"due to excessive join attempts.\n\n"
            f"<i>Reason: Potential spam/bot behavior</i>",
            parse_mode='HTML'
        )
        
        # Log the ban
        db = context.application.bot_data.get('database')
        if db is not None:
            await db.action_logs.insert_one({
                "chat_id": str(chat_id),
                "user_id": str(user_id),
                "action_type": "rate_limit_ban",
                "duration": TEMP_BAN_DURATION,
                "timestamp": datetime.now(timezone.utc)
            })
        
        logger.info(
            f"Temp banned user {user_id} in chat {chat_id} for rate limit violation "
            f"({TEMP_BAN_DURATION}s)"
        )
        
    except Exception as e:
        logger.error(f"Failed to handle rate limit violation: {e}")


async def get_rate_limit_stats(db, chat_id: int, hours: int = 24) -> dict:
    """
    Get rate limiting statistics for a chat
    
    Args:
        db: Database instance
        chat_id: Chat ID
        hours: Number of hours to look back
    
    Returns:
        Dictionary with statistics
    """
    if db is None:
        return {}
    
    try:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Total attempts
        total_attempts = await db.captcha_attempts.count_documents({
            "chat_id": str(chat_id),
            "timestamp": {"$gte": since}
        })
        
        # Unique users
        pipeline = [
            {
                "$match": {
                    "chat_id": str(chat_id),
                    "timestamp": {"$gte": since}
                }
            },
            {
                "$group": {
                    "_id": "$user_id"
                }
            },
            {
                "$count": "unique_users"
            }
        ]
        
        result = await db.captcha_attempts.aggregate(pipeline).to_list(length=1)
        unique_users = result[0]['unique_users'] if result else 0
        
        # Rate limit violations
        violations = await db.action_logs.count_documents({
            "chat_id": str(chat_id),
            "action_type": "rate_limit_ban",
            "timestamp": {"$gte": since}
        })
        
        return {
            "total_attempts": total_attempts,
            "unique_users": unique_users,
            "violations": violations,
            "period_hours": hours
        }
        
    except Exception as e:
        logger.error(f"Error getting rate limit stats: {e}")
        return {}