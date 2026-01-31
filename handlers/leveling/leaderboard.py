"""
Leaderboard command - Show top users by XP
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "leaderboard",
    "aliases": ["top", "lb", "top10"],
    "description": "Show top users by XP",
    "usage": "/leaderboard - Show top 10 users",
    "category": "leveling"
}


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leaderboard of top users"""
    message = update.message
    
    db = context.application.bot_data.get('database')
    if not db:
        await message.reply_text("❌ Database not available")
        return
    
    try:
        # Get top 10 users by XP
        top_users = await db.users.find(
            {},
            {"_id": 1, "first_name": 1, "username": 1, "xp": 1, "level": 1}
        ).sort("xp", -1).limit(10).to_list(length=10)
        
        if not top_users:
            await message.reply_html(
                "📊 <b>Leaderboard</b>\n\n"
                "No users have earned XP yet!"
            )
            return
        
        # Build leaderboard message
        msg = "🏆 <b>Top 10 Users - Leaderboard</b>\n\n"
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, user in enumerate(top_users, 1):
            # Medal for top 3
            if i <= 3:
                prefix = medals[i-1]
            else:
                prefix = f"<code>{i:2d}.</code>"
            
            name = user.get('first_name', 'Unknown')
            username = user.get('username')
            xp = user.get('xp', 0)
            level = user.get('level', 0)
            
            # Truncate long names
            if len(name) > 15:
                name = name[:12] + "..."
            
            msg += f"{prefix} <b>{name}</b>"
            
            if username:
                msg += f" (@{username})"
            
            msg += f"\n    ⭐ Level {level} • ✨ {xp:,} XP\n"
        
        # Show current user's rank if not in top 10
        user_id = str(update.effective_user.id)
        user_doc = await db.users.find_one({"_id": user_id})
        
        if user_doc:
            user_xp = user_doc.get('xp', 0)
            
            # Check if user is in top 10
            user_in_top_10 = any(str(u['_id']) == user_id for u in top_users)
            
            if not user_in_top_10:
                # Count users with higher XP
                rank = await db.users.count_documents({"xp": {"$gt": user_xp}}) + 1
                
                msg += f"\n━━━━━━━━━━━━━━━━━━\n"
                msg += f"<b>Your Rank:</b> #{rank}\n"
                msg += f"⭐ Level {user_doc.get('level', 0)} • ✨ {user_xp:,} XP"
        
        await message.reply_html(msg)
        
    except Exception as e:
        logger.error(f"Error in leaderboard command: {e}", exc_info=True)
        await message.reply_text("❌ Error retrieving leaderboard")

