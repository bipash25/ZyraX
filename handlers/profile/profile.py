"""
Profile command - Show user profile card
"""
import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes

from utils.user_resolver import resolve_user

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "profile",
    "aliases": ["me", "myprofile"],
    "description": "View user profile",
    "usage": "/profile [@user] - View profile",
    "category": "profile"
}


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user profile"""
    message = update.message
    
    db = context.application.bot_data.get('database')
    if not db:
        await message.reply_text("❌ Database not available")
        return
    
    # Resolve target user
    target_user, _ = await resolve_user(update, context)
    
    if not target_user:
        target_user = update.effective_user
    
    user_id = str(target_user.id)
    
    try:
        # Get user data
        user_doc = await db.users.find_one({"_id": user_id})
        
        if not user_doc:
            await message.reply_html(
                f"❌ <b>{target_user.first_name}</b> doesn't have a profile yet!"
            )
            return
        
        # Extract data
        name = user_doc.get('first_name', 'Unknown')
        username = user_doc.get('username')
        bio = user_doc.get('bio', 'No bio set.')
        
        level = user_doc.get('level', 0)
        xp = user_doc.get('xp', 0)
        currency = user_doc.get('currency', 0)
        rep = user_doc.get('reputation', 0)
        
        # Messages sent
        messages = user_doc.get('messages_sent', 0)
        
        # Marriage
        married_to = user_doc.get('married_to')
        marriage_partner = None
        if married_to:
            partner_doc = await db.users.find_one({"_id": married_to})
            if partner_doc:
                marriage_partner = partner_doc.get('first_name', 'Unknown')
        
        # Calculate XP for next level
        xp_needed = (level + 1) * 100
        xp_progress = (xp / xp_needed) * 100 if xp_needed > 0 else 0
        
        # Build profile card
        msg = f"👤 <b>Profile Card</b>\n\n"
        msg += f"<b>Name:</b> {name}\n"
        
        if username:
            msg += f"<b>Username:</b> @{username}\n"
        
        msg += f"<b>ID:</b> <code>{target_user.id}</code>\n\n"
        
        msg += f"📝 <b>Bio:</b>\n<i>{bio}</i>\n\n"
        
        msg += f"━━━━━━━━━━━━━━━━━━\n"
        msg += f"⭐ <b>Level:</b> {level}\n"
        msg += f"✨ <b>XP:</b> {xp:,} / {xp_needed:,} ({xp_progress:.1f}%)\n"
        msg += f"💰 <b>Coins:</b> {currency:,} 🪙\n"
        msg += f"💎 <b>Reputation:</b> {rep}\n"
        msg += f"💬 <b>Messages:</b> {messages:,}\n"
        
        if marriage_partner:
            msg += f"💕 <b>Married to:</b> {marriage_partner}\n"
        
        # Get ranks for various leaderboards
        xp_rank = await db.users.count_documents({"xp": {"$gt": xp}}) + 1
        coin_rank = await db.users.count_documents({"currency": {"$gt": currency}}) + 1
        
        msg += f"\n<b>Rankings:</b>\n"
        msg += f"🏆 XP Rank: #{xp_rank}\n"
        msg += f"💰 Wealth Rank: #{coin_rank}\n"
        
        await message.reply_html(msg)
        
    except Exception as e:
        logger.error(f"Error in profile command: {e}", exc_info=True)
        await message.reply_text("❌ Error retrieving profile")

