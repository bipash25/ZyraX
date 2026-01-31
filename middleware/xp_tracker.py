"""
XP Tracking Middleware - Award experience points for activity
Tracks message activity and awards XP with cooldown
"""
import logging
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus

logger = logging.getLogger(__name__)

# XP Configuration
XP_PER_MESSAGE = 5
XP_COOLDOWN_SECONDS = 60  # 1 minute between XP awards
MIN_MESSAGE_LENGTH = 5  # Minimum characters to earn XP

# Level calculation
def calculate_level(xp: int) -> int:
    """Calculate level from XP using exponential curve"""
    # Level formula: level = floor(0.1 * sqrt(xp))
    # This means: L1=100xp, L2=400xp, L3=900xp, L4=1600xp, etc.
    import math
    if xp < 100:
        return 0
    return int(0.1 * math.sqrt(xp))

def xp_for_level(level: int) -> int:
    """Calculate XP needed for a specific level"""
    return (level * 10) ** 2


async def track_xp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Track user activity and award XP
    
    Runs for every message to track engagement.
    Awards XP with cooldown to prevent spam.
    """
    # Only track regular messages in groups
    if not update.message or not update.effective_chat:
        return
    
    chat = update.effective_chat
    if chat.type == 'private':
        return  # Don't track XP in private chats
    
    message = update.message
    user = update.effective_user
    
    # Don't track bots
    if not user or user.is_bot:
        return
    
    # Don't track commands
    if message.text and message.text.startswith('/'):
        return
    
    chat_id = chat.id
    user_id = user.id
    
    try:
        db = context.application.bot_data.get('database')
        if db is None:
            return
        
        # Get chat settings
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        
        # Check if XP system is enabled for this chat
        if chat_doc and not chat_doc.get('xp_enabled', True):
            return  # XP disabled
        
        # Check if admins are exempt
        if chat_doc and chat_doc.get('xp_exempt_admins', False):
            try:
                member = await chat.get_member(user_id)
                if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                    return  # Admins don't earn XP
            except Exception:
                pass
        
        # Get user data
        user_doc = await db.users.find_one({"_id": str(user_id)})
        
        now = datetime.now(timezone.utc)
        
        # Initialize user data if not exists
        if not user_doc:
            user_doc = {
                "_id": str(user_id),
                "username": user.username,
                "first_name": user.first_name,
                "xp": 0,
                "level": 0,
                "messages": 0,
                "last_xp_time": None,
                "currency": 0,
                "last_daily": None,
                "inventory": [],
                "chat_data": {}
            }
        
        # Get per-chat data
        chat_data = user_doc.get('chat_data', {}).get(str(chat_id), {})
        last_xp_time = chat_data.get('last_xp_time')
        
        # Check cooldown
        if last_xp_time:
            if isinstance(last_xp_time, str):
                last_xp_time = datetime.fromisoformat(last_xp_time.replace('Z', '+00:00'))
            elif last_xp_time.tzinfo is None:
                last_xp_time = last_xp_time.replace(tzinfo=timezone.utc)
            
            time_since_last = (now - last_xp_time).total_seconds()
            if time_since_last < XP_COOLDOWN_SECONDS:
                return  # Still in cooldown
        
        # Check message length
        message_text = message.text or message.caption or ""
        if len(message_text) < MIN_MESSAGE_LENGTH:
            return  # Message too short
        
        # Calculate XP to award
        xp_multiplier = chat_doc.get('xp_multiplier', 1.0) if chat_doc else 1.0
        xp_to_award = int(XP_PER_MESSAGE * xp_multiplier)
        
        # Current stats
        current_xp = user_doc.get('xp', 0)
        current_level = user_doc.get('level', 0)
        messages = user_doc.get('messages', 0)
        
        # Award XP
        new_xp = current_xp + xp_to_award
        new_level = calculate_level(new_xp)
        
        # Update per-chat data
        if 'chat_data' not in user_doc:
            user_doc['chat_data'] = {}
        if str(chat_id) not in user_doc['chat_data']:
            user_doc['chat_data'][str(chat_id)] = {}
        
        user_doc['chat_data'][str(chat_id)]['last_xp_time'] = now
        user_doc['chat_data'][str(chat_id)]['messages'] = chat_data.get('messages', 0) + 1
        
        # Update user document
        await db.users.update_one(
            {"_id": str(user_id)},
            {
                "$set": {
                    "username": user.username,
                    "first_name": user.first_name,
                    "xp": new_xp,
                    "level": new_level,
                    "messages": messages + 1,
                    f"chat_data.{chat_id}.last_xp_time": now,
                    f"chat_data.{chat_id}.messages": chat_data.get('messages', 0) + 1
                }
            },
            upsert=True
        )
        
        # Check for level up
        if new_level > current_level:
            await handle_level_up(
                context,
                chat_id,
                user_id,
                user,
                current_level,
                new_level,
                chat_doc
            )
            
            logger.info(f"User {user_id} leveled up to {new_level} in chat {chat_id}")
        
    except Exception as e:
        logger.error(f"Error tracking XP: {e}", exc_info=True)


async def handle_level_up(
    context,
    chat_id: int,
    user_id: int,
    user,
    old_level: int,
    new_level: int,
    chat_doc
):
    """Handle level up - send notification and give rewards"""
    try:
        db = context.application.bot_data.get('database')
        
        # Check if notifications are enabled
        if chat_doc and not chat_doc.get('levelup_notifications', True):
            return
        
        # Currency reward for leveling up
        currency_reward = new_level * 100  # 100 coins per level
        
        if db:
            await db.users.update_one(
                {"_id": str(user_id)},
                {"$inc": {"currency": currency_reward}}
            )
        
        # Get custom rank name if set
        rank_name = None
        if chat_doc and chat_doc.get('rank_names'):
            rank_name = chat_doc.get('rank_names', {}).get(str(new_level))
        
        # Send notification
        message = f"🎉 <b>Level Up!</b>\n\n"
        message += f"{user.mention_html()} reached <b>Level {new_level}</b>!"
        
        if rank_name:
            message += f"\n\n🏆 <b>Rank:</b> {rank_name}"
        
        if currency_reward > 0:
            message += f"\n💰 <b>Reward:</b> {currency_reward:,} coins"
        
        await context.bot.send_message(
            chat_id,
            message,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error handling level up: {e}")

