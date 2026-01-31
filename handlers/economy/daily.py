"""
Daily reward command - Claim daily coins
"""
import logging
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "daily",
    "aliases": ["dailyreward", "claim"],
    "description": "Claim your daily reward",
    "usage": "/daily - Claim 500 coins (once per day)",
    "category": "economy"
}

DAILY_REWARD = 500
DAILY_COOLDOWN_HOURS = 24


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Claim daily reward"""
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
                "last_daily": None
            }
        
        last_daily = user_doc.get('last_daily')
        
        # Check cooldown
        if last_daily:
            if isinstance(last_daily, str):
                last_daily = datetime.fromisoformat(last_daily.replace('Z', '+00:00'))
            elif last_daily.tzinfo is None:
                last_daily = last_daily.replace(tzinfo=timezone.utc)
            
            time_since = (now - last_daily).total_seconds() / 3600  # hours
            
            if time_since < DAILY_COOLDOWN_HOURS:
                hours_left = DAILY_COOLDOWN_HOURS - time_since
                minutes_left = int((hours_left % 1) * 60)
                hours_left = int(hours_left)
                
                await message.reply_html(
                    f"⏰ <b>Daily Reward</b>\n\n"
                    f"You've already claimed your daily reward!\n\n"
                    f"⏳ <b>Come back in:</b> {hours_left}h {minutes_left}m"
                )
                return
        
        # Calculate reward (bonus for streak)
        current_balance = user_doc.get('currency', 0)
        reward = DAILY_REWARD
        
        # Level bonus
        level = user_doc.get('level', 0)
        level_bonus = level * 10
        total_reward = reward + level_bonus
        
        # Award reward
        new_balance = current_balance + total_reward
        
        await db.users.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "username": user.username,
                    "first_name": user.first_name,
                    "currency": new_balance,
                    "last_daily": now
                }
            },
            upsert=True
        )
        
        # Build message
        msg = f"🎁 <b>Daily Reward Claimed!</b>\n\n"
        msg += f"💰 <b>Base Reward:</b> {reward:,} 🪙\n"
        
        if level_bonus > 0:
            msg += f"⭐ <b>Level Bonus ({level}):</b> +{level_bonus:,} 🪙\n"
        
        msg += f"\n<b>Total Earned:</b> {total_reward:,} 🪙\n"
        msg += f"<b>New Balance:</b> {new_balance:,} 🪙\n\n"
        msg += f"⏰ Come back in {DAILY_COOLDOWN_HOURS} hours!"
        
        await message.reply_html(msg)
        
    except Exception as e:
        logger.error(f"Error in daily command: {e}", exc_info=True)
        await message.reply_text("❌ Error claiming daily reward")

