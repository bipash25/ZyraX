"""
Antiflood middleware - Track and enforce message flood limits
"""
import logging
from datetime import timedelta
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from telegram.constants import ChatType
from utils.time_parser import now_utc

logger = logging.getLogger(__name__)

# In-memory flood tracking (chat_id -> user_id -> message_data)
flood_tracker = {}


async def cleanup_flood_tracker():
    """
    Clean up old entries from flood tracker to prevent memory leak
    Removes entries older than 5 minutes
    """
    from core.constants import FLOOD_TRACKER_CLEANUP_THRESHOLD
    
    now = now_utc()
    cleanup_threshold = timedelta(seconds=FLOOD_TRACKER_CLEANUP_THRESHOLD)
    
    # Create list of keys to avoid RuntimeError during iteration
    chat_ids = list(flood_tracker.keys())
    
    removed_users = 0
    removed_chats = 0
    
    for chat_id in chat_ids:
        if chat_id not in flood_tracker:
            continue
            
        user_ids = list(flood_tracker[chat_id].keys())
        
        for user_id in user_ids:
            if user_id not in flood_tracker[chat_id]:
                continue
                
            user_data = flood_tracker[chat_id][user_id]
            
            # Check if user has recent messages
            if user_data['messages']:
                last_msg = max(user_data['messages'])
                if now - last_msg > cleanup_threshold:
                    del flood_tracker[chat_id][user_id]
                    removed_users += 1
        
        # Remove empty chats
        if not flood_tracker[chat_id]:
            del flood_tracker[chat_id]
            removed_chats += 1
    
    if removed_users > 0 or removed_chats > 0:
        logger.debug(f"Flood tracker cleanup: removed {removed_users} users, {removed_chats} chats. "
                    f"Remaining: {len(flood_tracker)} chats")
    
    return removed_users, removed_chats


async def antiflood_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Middleware to track message frequency and take action on floods
    
    This runs before command handlers to prevent flooding.
    Approved users and admins bypass flood checks.
    
    Args:
        update: Telegram update
        context: PTB context
    
    Returns:
        bool: True to continue processing, False to stop
    """
    # Only process regular messages in groups
    if not update.message or not update.message.text:
        return True
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Only apply in groups
    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return True
    
    # Don't track bots
    if user.is_bot:
        return True
    
    chat_id = chat.id
    user_id = user.id
    
    try:
        # Check if user is admin
        member = await chat.get_member(user_id)
        if member.status in ['administrator', 'creator']:
            return True
        
        # Get flood settings
        db = context.application.bot_data.get('database')
        if db is None:
            return True
        
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        
        if not chat_doc:
            return True
        
        flood_limit = chat_doc.get('flood_limit', 0)
        
        # If flood protection disabled
        if flood_limit == 0:
            return True
        
        # Check if user is approved (bypasses flood)
        user_doc = await db.users.find_one({"_id": str(user_id)})
        if user_doc and user_doc.get('chat_data', {}).get(str(chat_id), {}).get('approved', False):
            return True
        
        # Initialize tracker for this chat
        if chat_id not in flood_tracker:
            flood_tracker[chat_id] = {}
        
        # Initialize tracker for this user
        if user_id not in flood_tracker[chat_id]:
            flood_tracker[chat_id][user_id] = {
                'messages': [],
                'warned': False
            }
        
        user_data = flood_tracker[chat_id][user_id]
        now = now_utc()
        
        # Get flood timeframe (default 10 seconds)
        flood_timeframe = chat_doc.get('flood_timeframe', 10)
        
        # Clean old messages (outside timeframe)
        user_data['messages'] = [
            msg_time for msg_time in user_data['messages']
            if (now - msg_time).total_seconds() < flood_timeframe
        ]
        
        # Add current message
        user_data['messages'].append(now)
        
        # Check if limit exceeded
        if len(user_data['messages']) > flood_limit:
            # Take action
            flood_mode = chat_doc.get('flood_mode', 'mute')
            
            try:
                # Take action based on mode
                if flood_mode == 'ban':
                    await chat.ban_member(user_id)
                    action_text = "banned"
                
                elif flood_mode == 'kick':
                    await chat.ban_member(user_id)
                    await chat.unban_member(user_id)
                    action_text = "kicked"
                
                elif flood_mode == 'mute':
                    await chat.restrict_member(
                        user_id,
                        permissions=ChatPermissions(can_send_messages=False),
                        until_date=None
                    )
                    action_text = "muted"
                
                elif flood_mode == 'tban':
                    # Temporary ban for 1 hour
                    until = now_utc() + timedelta(hours=1)
                    await chat.ban_member(user_id, until_date=until)
                    action_text = "temporarily banned (1h)"
                
                elif flood_mode == 'tmute':
                    # Temporary mute for 1 hour
                    until = now_utc() + timedelta(hours=1)
                    await chat.restrict_member(
                        user_id,
                        permissions=ChatPermissions(can_send_messages=False),
                        until_date=until
                    )
                    action_text = "temporarily muted (1h)"
                
                else:
                    action_text = "warned"
                
                # Delete the flood message first
                try:
                    await update.message.delete()
                except Exception:
                    pass
                
                # Send notification in chat (not as reply since message is deleted)
                notification = await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"🌊 <b>Flood detected!</b>\n\n"
                         f"User {user.mention_html()} has been {action_text} for flooding.\n"
                         f"Limit: {flood_limit} messages in {flood_timeframe}s",
                    parse_mode='HTML'
                )
                
                # Auto-delete notification after 10 seconds
                import asyncio
                asyncio.create_task(delete_after_delay(notification, 10))
                
                # Clear user's flood tracker
                flood_tracker[chat_id][user_id] = {'messages': [], 'warned': False}
                
                logger.info(
                    f"Flood action taken in chat {chat_id}: "
                    f"user {user_id} {action_text}"
                )
                
                # Log to database
                if db is not None:
                    await db.action_logs.insert_one({
                        "chat_id": str(chat_id),
                        "action_type": f"antiflood_{flood_mode}",
                        "performed_by": "system",
                        "target_user": str(user_id),
                        "reason": f"Flooding: {len(user_data['messages'])} messages in {flood_timeframe}s",
                        "metadata": {
                            "flood_limit": flood_limit,
                            "message_count": len(user_data['messages'])
                        },
                        "timestamp": now
                    })
                
                return False  # Stop processing this message
                
            except Exception as e:
                logger.error(f"Error taking flood action in chat {chat_id}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in antiflood middleware: {e}")
        return True


async def delete_after_delay(message, seconds: int):
    """Helper to delete a message after a delay"""
    import asyncio
    try:
        await asyncio.sleep(seconds)
        await message.delete()
    except Exception:
        pass


# Export cleanup function for scheduler
__all__ = ['antiflood_middleware', 'cleanup_flood_tracker']