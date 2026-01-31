"""
Rank command - Show user's XP, level, and stats
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from utils.user_resolver import resolve_user
from middleware.xp_tracker import calculate_level, xp_for_level

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "rank",
    "aliases": ["level", "xp", "myrank"],
    "description": "Show your or another user's rank and stats",
    "usage": "/rank [@user]",
    "category": "leveling"
}


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's rank, XP, and level"""
    chat = update.effective_chat
    message = update.message
    
    db = context.application.bot_data.get('database')
    if not db:
        await message.reply_text("❌ Database not available")
        return
    
    # Resolve target user (self if not specified)
    target_user, _ = await resolve_user(update, context)
    if not target_user:
        target_user = update.effective_user
    
    user_id = target_user.id
    
    try:
        # Get user data
        user_doc = await db.users.find_one({"_id": str(user_id)})
        
        if not user_doc:
            if user_id == update.effective_user.id:
                await message.reply_html(
                    "📊 <b>Your Stats</b>\n\n"
                    "You haven't earned any XP yet!\n"
                    "Start chatting to earn experience."
                )
            else:
                await message.reply_html(
                    f"📊 <b>{target_user.first_name}'s Stats</b>\n\n"
                    f"This user hasn't earned any XP yet."
                )
            return
        
        # Extract stats
        xp = user_doc.get('xp', 0)
        level = user_doc.get('level', 0)
        messages = user_doc.get('messages', 0)
        currency = user_doc.get('currency', 0)
        
        # Calculate progress to next level
        next_level = level + 1
        xp_needed = xp_for_level(next_level)
        xp_current_level = xp_for_level(level)
        xp_progress = xp - xp_current_level
        xp_for_next = xp_needed - xp_current_level
        progress_percent = (xp_progress / xp_for_next * 100) if xp_for_next > 0 else 0
        
        # Get rank in chat
        chat_rank = None
        if chat.type in ['group', 'supergroup']:
            # Count users with higher XP in this chat
            users_above = await db.users.count_documents({
                "xp": {"$gt": xp}
            })
            chat_rank = users_above + 1
        
        # Build progress bar
        bar_length = 10
        filled = int(progress_percent / 10)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        # Get custom rank name
        rank_name = None
        if chat.type in ['group', 'supergroup']:
            chat_doc = await db.chats.find_one({"_id": str(chat.id)})
            if chat_doc and chat_doc.get('rank_names'):
                rank_name = chat_doc.get('rank_names', {}).get(str(level))
        
        # Build message
        is_self = user_id == update.effective_user.id
        name = "Your" if is_self else f"{target_user.first_name}'s"
        
        msg = f"📊 <b>{name} Stats</b>\n\n"
        msg += f"👤 <b>User:</b> {target_user.mention_html()}\n"
        msg += f"⭐ <b>Level:</b> {level}\n"
        
        if rank_name:
            msg += f"🏆 <b>Rank:</b> {rank_name}\n"
        
        msg += f"✨ <b>XP:</b> {xp:,}\n"
        
        if chat_rank:
            msg += f"🏅 <b>Chat Rank:</b> #{chat_rank}\n"
        
        msg += f"💬 <b>Messages:</b> {messages:,}\n"
        msg += f"💰 <b>Coins:</b> {currency:,}\n\n"
        
        msg += f"<b>Progress to Level {next_level}:</b>\n"
        msg += f"{bar} {progress_percent:.1f}%\n"
        msg += f"<code>{xp_progress:,}/{xp_for_next:,} XP</code>"
        
        await message.reply_html(msg)
        
    except Exception as e:
        logger.error(f"Error in rank command: {e}", exc_info=True)
        await message.reply_text("❌ Error retrieving rank information")

