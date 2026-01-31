"""
Topchat command - Chat-specific XP leaderboard
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "topchat",
    "aliases": ["chatleaderboard", "chatlb"],
    "description": "Show top users in this chat by XP",
    "usage": "/topchat - Show top 10 in this chat",
    "category": "leveling",
    "group_only": True
}


@group_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show chat-specific leaderboard"""
    message = update.message
    chat_id = str(update.effective_chat.id)
    
    db = context.application.bot_data.get('database')
    if not db:
        await message.reply_text("❌ Database not available")
        return
    
    try:
        # Get all users with activity in this chat
        users = await db.users.find().to_list(length=None)
        
        # Filter users who have sent messages in this chat
        chat_users = []
        for user in users:
            chat_data = user.get('chat_data', {})
            if chat_id in chat_data:
                user_chat_data = chat_data[chat_id]
                messages = user_chat_data.get('messages_sent', 0)
                if messages > 0:
                    chat_users.append({
                        'user_id': user['_id'],
                        'first_name': user.get('first_name', 'Unknown'),
                        'username': user.get('username'),
                        'xp': user.get('xp', 0),
                        'level': user.get('level', 0),
                        'messages': messages
                    })
        
        # Sort by XP
        chat_users.sort(key=lambda x: x['xp'], reverse=True)
        top_users = chat_users[:10]
        
        if not top_users:
            await message.reply_html(
                f"🏆 <b>Top Users in This Chat</b>\n\n"
                f"No one has earned XP in this chat yet!"
            )
            return
        
        # Build leaderboard
        chat_name = update.effective_chat.title or "this chat"
        msg = f"🏆 <b>Top 10 in {chat_name}</b>\n\n"
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, user in enumerate(top_users, 1):
            if i <= 3:
                prefix = medals[i-1]
            else:
                prefix = f"<code>{i:2d}.</code>"
            
            name = user['first_name']
            username = user['username']
            xp = user['xp']
            level = user['level']
            messages = user['messages']
            
            # Truncate long names
            if len(name) > 15:
                name = name[:12] + "..."
            
            msg += f"{prefix} <b>{name}</b>"
            
            if username:
                msg += f" (@{username})"
            
            msg += f"\n    ⭐ Level {level} • ✨ {xp:,} XP • 💬 {messages:,} msgs\n"
        
        # Show current user's rank in this chat
        user_id = str(update.effective_user.id)
        user_in_top = any(u['user_id'] == user_id for u in top_users)
        
        if not user_in_top:
            # Find user's rank
            for i, user in enumerate(chat_users, 1):
                if user['user_id'] == user_id:
                    msg += f"\n━━━━━━━━━━━━━━━━━━\n"
                    msg += f"<b>Your Rank:</b> #{i}\n"
                    msg += f"⭐ Level {user['level']} • ✨ {user['xp']:,} XP"
                    break
        
        await message.reply_html(msg)
        
    except Exception as e:
        logger.error(f"Error in topchat command: {e}", exc_info=True)
        await message.reply_text("❌ Error retrieving chat leaderboard")

