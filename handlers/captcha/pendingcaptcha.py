"""
List users currently awaiting captcha verification
Command: /pendingcaptcha
"""

from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import require_admin, group_only, log_command
from utils.time_parser import now_utc
import logging

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "pendingcaptcha",
    "aliases": ["pending_captcha", "captcha_pending"],
    "description": "List users awaiting captcha verification",
    "usage": "/pendingcaptcha",
    "category": "captcha",
    "permissions": ["can_restrict_members"],
    "admin_only": True,
    "group_only": True
}

@require_admin(permissions=["can_restrict_members"])
@group_only
@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List pending captcha verifications"""
    chat_id = str(update.effective_chat.id)
    message = update.message
    
    try:
        # Get database
        db = context.application.bot_data.get('database')
        if not db:
            await message.reply_text("❌ Database not available")
            return
        
        # Get all pending verifications for this chat
        cursor = db.captcha_pending.find({"chat_id": chat_id}).sort("created_at", 1)
        
        pending_users = []
        async for doc in cursor:
            pending_users.append(doc)
        
        if not pending_users:
            await message.reply_text(
                "✅ No users are currently awaiting verification.\n\n"
                "All members have completed the captcha!"
            )
            return
        
        # Build the message
        response = (
            f"⏳ <b>Pending Captcha Verifications</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Total:</b> {len(pending_users)}\n\n"
        )
        
        # Add each user
        for i, user_doc in enumerate(pending_users, 1):
            user_id = user_doc["user_id"]
            created_at = user_doc.get("created_at", now_utc())
            captcha_type = user_doc.get("captcha_type", "unknown")
            expires_at = user_doc.get("expires_at")
            
            # Try to get user info
            try:
                user = await context.bot.get_chat_member(int(chat_id), int(user_id))
                user_name = user.user.full_name
                username = f"@{user.user.username}" if user.user.username else "No username"
            except Exception:
                user_name = "Unknown User"
                username = "N/A"
            
            # Calculate time elapsed
            elapsed = now_utc() - created_at
            minutes_elapsed = int(elapsed.total_seconds() // 60)
            
            # Calculate time remaining
            time_remaining = "N/A"
            if expires_at:
                remaining = expires_at - now_utc()
                if remaining.total_seconds() > 0:
                    minutes_remaining = int(remaining.total_seconds() // 60)
                    time_remaining = f"{minutes_remaining}m"
                else:
                    time_remaining = "Expired"
            
            # Add to response
            response += (
                f"<b>{i}.</b> {user_name}\n"
                f"   • ID: <code>{user_id}</code>\n"
                f"   • Username: {username}\n"
                f"   • Type: {captcha_type.title()}\n"
                f"   • Waiting: {minutes_elapsed}m\n"
            )
            
            if time_remaining != "N/A":
                response += f"   • Timeout: {time_remaining}\n"
            
            response += "\n"
            
            # Limit to 15 users per message
            if i >= 15:
                response += f"<i>... and {len(pending_users) - 15} more</i>\n"
                break
        
        response += (
            "\n💡 <b>Actions:</b>\n"
            "• Use /verify &lt;user&gt; to manually verify\n"
            "• Use /whitelist &lt;user&gt; to bypass captcha"
        )
        
        await message.reply_text(response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in pendingcaptcha command: {e}")
        await message.reply_text(
            f"❌ Error fetching pending verifications: {str(e)}"
        )