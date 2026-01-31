"""
Work command - Earn coins by working
"""
import logging
import random
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "work",
    "aliases": ["job"],
    "description": "Work to earn coins (1 hour cooldown)",
    "usage": "/work - Earn 50-200 coins",
    "category": "economy"
}

WORK_COOLDOWN_HOURS = 1
WORK_MIN = 50
WORK_MAX = 200

# Fun work responses
WORK_RESPONSES = [
    ("programmer", "💻 You fixed some bugs and earned"),
    ("chef", "👨‍🍳 You cooked delicious meals and earned"),
    ("doctor", "👨‍⚕️ You saved lives and earned"),
    ("teacher", "👨‍🏫 You taught a class and earned"),
    ("artist", "🎨 You sold a painting and earned"),
    ("musician", "🎵 You performed a concert and earned"),
    ("writer", "📝 You published an article and earned"),
    ("gamer", "🎮 You won a tournament and earned"),
    ("streamer", "📹 You streamed for donations and earned"),
    ("trader", "📈 You made successful trades and earned"),
]


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Work to earn coins"""
    user = update.effective_user
    message = update.message
    
    db = context.application.bot_data.get('database')
    if not db:
        await message.reply_text("❌ Database not available")
        return
    
    user_id = str(user.id)
    now = datetime.now(timezone.utc)
    
    try:
        # Get user data
        user_doc = await db.users.find_one({"_id": user_id})
        
        if not user_doc:
            user_doc = {
                "_id": user_id,
                "username": user.username,
                "first_name": user.first_name,
                "currency": 0,
                "last_work": None
            }
        
        last_work = user_doc.get('last_work')
        
        # Check cooldown
        if last_work:
            if isinstance(last_work, str):
                last_work = datetime.fromisoformat(last_work.replace('Z', '+00:00'))
            elif last_work.tzinfo is None:
                last_work = last_work.replace(tzinfo=timezone.utc)
            
            time_since = (now - last_work).total_seconds() / 3600  # hours
            
            if time_since < WORK_COOLDOWN_HOURS:
                minutes_left = int((WORK_COOLDOWN_HOURS - time_since) * 60)
                
                await message.reply_html(
                    f"⏰ <b>You're tired!</b>\n\n"
                    f"You need to rest before working again.\n\n"
                    f"⏳ <b>Come back in:</b> {minutes_left} minutes"
                )
                return
        
        # Work and earn!
        earned = random.randint(WORK_MIN, WORK_MAX)
        job, response = random.choice(WORK_RESPONSES)
        
        # Level bonus
        level = user_doc.get('level', 0)
        level_bonus = level * 5
        total_earned = earned + level_bonus
        
        current_balance = user_doc.get('currency', 0)
        new_balance = current_balance + total_earned
        
        # Update user
        await db.users.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "username": user.username,
                    "first_name": user.first_name,
                    "currency": new_balance,
                    "last_work": now
                }
            },
            upsert=True
        )
        
        # Send message
        msg = f"💼 <b>Work Complete!</b>\n\n"
        msg += f"{response} <b>{earned:,} 🪙</b>\n"
        
        if level_bonus > 0:
            msg += f"⭐ <b>Level Bonus ({level}):</b> +{level_bonus:,} 🪙\n"
        
        msg += f"\n<b>Total Earned:</b> {total_earned:,} 🪙\n"
        msg += f"<b>New Balance:</b> {new_balance:,} 🪙\n\n"
        msg += f"⏰ Come back in {WORK_COOLDOWN_HOURS} hour!"
        
        await message.reply_html(msg)
        
    except Exception as e:
        logger.error(f"Error in work command: {e}", exc_info=True)
        await message.reply_text("❌ Error processing work")

