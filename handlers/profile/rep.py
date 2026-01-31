"""
Rep command - Give reputation points
"""
import logging
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import ContextTypes

from utils.user_resolver import resolve_user
from core.decorators import group_only

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "rep",
    "aliases": ["reputation"],
    "description": "Give reputation point (1 per 24h)",
    "usage": "/rep <user> - Give +1 rep",
    "category": "profile",
    "group_only": True
}

REP_COOLDOWN_HOURS = 24


@group_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Give reputation to user"""
    user = update.effective_user
    message = update.message
    chat_id = update.effective_chat.id
    
    db = context.application.bot_data.get('database')
    if not db:
        await message.reply_text("❌ Database not available")
        return
    
    # Resolve target user
    target_user, _ = await resolve_user(update, context)
    
    if not target_user:
        await message.reply_html(
            "📝 <b>Give Reputation</b>\n\n"
            "<b>Usage:</b> Reply to a user or mention them\n"
            "<code>/rep @user</code>"
        )
        return
    
    # Can't rep yourself
    if target_user.id == user.id:
        await message.reply_text("❌ You can't give reputation to yourself!")
        return
    
    # Can't rep bots
    if target_user.is_bot:
        await message.reply_text("❌ You can't give reputation to bots!")
        return
    
    user_id = str(user.id)
    target_id = str(target_user.id)
    now = datetime.now(timezone.utc)
    
    try:
        # Get user data
        user_doc = await db.users.find_one({"_id": user_id})
        
        if not user_doc:
            user_doc = {"_id": user_id, "last_rep_given": {}}
        
        last_rep_given = user_doc.get('last_rep_given', {})
        
        # Check cooldown
        last_rep_time = last_rep_given.get(target_id)
        
        if last_rep_time:
            if isinstance(last_rep_time, str):
                last_rep_time = datetime.fromisoformat(last_rep_time.replace('Z', '+00:00'))
            elif last_rep_time.tzinfo is None:
                last_rep_time = last_rep_time.replace(tzinfo=timezone.utc)
            
            time_since = (now - last_rep_time).total_seconds() / 3600  # hours
            
            if time_since < REP_COOLDOWN_HOURS:
                hours_left = int(REP_COOLDOWN_HOURS - time_since)
                minutes_left = int((REP_COOLDOWN_HOURS - time_since - hours_left) * 60)
                
                await message.reply_html(
                    f"⏰ <b>Cooldown Active</b>\n\n"
                    f"You already gave reputation to {target_user.mention_html()} recently!\n\n"
                    f"⏳ <b>Try again in:</b> {hours_left}h {minutes_left}m"
                )
                return
        
        # Give reputation!
        await db.users.update_one(
            {"_id": target_id},
            {
                "$inc": {"reputation": 1},
                "$set": {
                    "username": target_user.username,
                    "first_name": target_user.first_name
                }
            },
            upsert=True
        )
        
        # Update last rep given time
        last_rep_given[target_id] = now
        
        await db.users.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "last_rep_given": last_rep_given,
                    "username": user.username,
                    "first_name": user.first_name
                }
            },
            upsert=True
        )
        
        # Get new rep count
        target_doc = await db.users.find_one({"_id": target_id})
        new_rep = target_doc.get('reputation', 1)
        
        await message.reply_html(
            f"💎 <b>Reputation Given!</b>\n\n"
            f"{user.mention_html()} gave +1 rep to {target_user.mention_html()}\n\n"
            f"<b>Total Reputation:</b> {new_rep} 💎"
        )
        
    except Exception as e:
        logger.error(f"Error in rep command: {e}", exc_info=True)
        await message.reply_text("❌ Error giving reputation")

