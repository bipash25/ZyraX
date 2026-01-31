"""
Richest command - Leaderboard by coins
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "richest",
    "aliases": ["topmoney", "wealthiest"],
    "description": "Show richest users by coins",
    "usage": "/richest - Show top 10 by coins",
    "category": "economy"
}


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show richest users"""
    message = update.message
    
    db = context.application.bot_data.get('database')
    if not db:
        await message.reply_text("❌ Database not available")
        return
    
    try:
        # Get top 10 users by currency
        top_users = await db.users.find(
            {},
            {"_id": 1, "first_name": 1, "username": 1, "currency": 1, "level": 1}
        ).sort("currency", -1).limit(10).to_list(length=10)
        
        if not top_users:
            await message.reply_html(
                "💰 <b>Richest Users</b>\n\n"
                "No one has earned coins yet!"
            )
            return
        
        # Build leaderboard
        msg = "💰 <b>Top 10 Richest Users</b>\n\n"
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, user in enumerate(top_users, 1):
            if i <= 3:
                prefix = medals[i-1]
            else:
                prefix = f"<code>{i:2d}.</code>"
            
            name = user.get('first_name', 'Unknown')
            username = user.get('username')
            coins = user.get('currency', 0)
            level = user.get('level', 0)
            
            # Truncate long names
            if len(name) > 15:
                name = name[:12] + "..."
            
            msg += f"{prefix} <b>{name}</b>"
            
            if username:
                msg += f" (@{username})"
            
            msg += f"\n    💰 {coins:,} 🪙 • ⭐ Level {level}\n"
        
        # Show current user's rank
        user_id = str(update.effective_user.id)
        user_doc = await db.users.find_one({"_id": user_id})
        
        if user_doc:
            user_coins = user_doc.get('currency', 0)
            
            # Check if in top 10
            user_in_top_10 = any(str(u['_id']) == user_id for u in top_users)
            
            if not user_in_top_10:
                # Count users with more coins
                rank = await db.users.count_documents({"currency": {"$gt": user_coins}}) + 1
                
                msg += f"\n━━━━━━━━━━━━━━━━━━\n"
                msg += f"<b>Your Rank:</b> #{rank}\n"
                msg += f"💰 {user_coins:,} 🪙"
        
        await message.reply_html(msg)
        
    except Exception as e:
        logger.error(f"Error in richest command: {e}", exc_info=True)
        await message.reply_text("❌ Error retrieving leaderboard")

