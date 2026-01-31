"""
Kick command - Remove users from the chat temporarily
Supports: /kick, /skick, /dkick
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, require_bot_admin, not_self, log_command
from utils.user_resolver import resolve_user, mention_user
from utils.time_parser import now_utc

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "kick",
    "aliases": ["skick", "dkick"],
    "description": "Kick a user from the chat",
    "usage": "/kick <reply|@username|ID> [reason]\n"
             "/skick <reply|@username|ID> [reason] - Silent kick (no message)\n"
             "/dkick <reply|@username|ID> [reason] - Delete message and kick",
    "category": "moderation",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin(permissions=["can_restrict_members"])
@require_bot_admin(permissions=["can_restrict_members"])
@not_self
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /kick, /skick, /dkick commands
    
    Kick removes user from chat but they can rejoin via invite link
    Unlike ban, kick allows the user to return
    
    Args:
        update: Telegram update
        context: PTB context
    """
    chat_id = update.effective_chat.id
    admin_user = update.effective_user
    message = update.effective_message
    
    # Get command variant
    command = message.text.split()[0].lower().lstrip('/')
    is_silent = command == "skick"
    is_delete = command == "dkick"
    
    # Resolve target user
    target_user, resolve_method = await resolve_user(update, context)
    
    if not target_user:
        await message.reply_html(
            "❌ <b>Please specify a user to kick.</b>\n\n"
            "<b>Usage:</b>\n"
            "• Reply to user's message with /kick\n"
            "• /kick @username [reason]\n"
            "• /kick &lt;user_id&gt; [reason]\n\n"
            "<b>Examples:</b>\n"
            "• /kick @username spam\n"
            "• /skick @username\n"
            "• /dkick 123456789 off-topic"
        )
        return
    
    # Check if target is an admin
    try:
        target_member = await context.bot.get_chat_member(chat_id, target_user.id)
        if target_member.status in ["administrator", "creator"]:
            await message.reply_text(
                "❌ I cannot kick administrators."
            )
            return
    except Exception as e:
        logger.error(f"Error checking target member status: {e}")
    
    # Parse reason
    args = context.args[1:] if resolve_method != "reply" else context.args
    reason = " ".join(args) if args else None
    
    # Perform kick
    try:
        # Kick = ban then immediately unban
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=target_user.id)
        await context.bot.unban_chat_member(chat_id=chat_id, user_id=target_user.id)
        
        # Delete command message if dkick
        if is_delete:
            try:
                await message.delete()
            except Exception as e:
                logger.debug(f"Could not delete command message: {e}")
        
        # Send confirmation (unless silent)
        if not is_silent:
            target_mention = mention_user(target_user, use_html=True)
            admin_mention = mention_user(admin_user, use_html=True)
            
            kick_text = f"👢 {target_mention} has been <b>kicked</b> by {admin_mention}."
            
            if reason:
                kick_text += f"\n\n<b>Reason:</b> {reason}"
            
            await message.reply_html(kick_text)
        
        # Log to database
        try:
            db = context.application.bot_data.get('database')
            if db is not None:
                await db.action_logs.insert_one({
                    "chat_id": str(chat_id),
                    "action_type": "kick",
                    "performed_by": str(admin_user.id),
                    "target_user": str(target_user.id),
                    "reason": reason or "No reason provided",
                    "timestamp": now_utc()
                })
        except Exception as e:
            logger.error(f"Error logging kick action: {e}")
        
        logger.info(
            f"User {target_user.id} kicked from chat {chat_id} by admin {admin_user.id}"
        )
        
    except Exception as e:
        logger.error(f"Error kicking user {target_user.id} from chat {chat_id}: {e}")
        await message.reply_html(
            f"❌ <b>Failed to kick user.</b>\n\n"
            f"Error: {str(e)}"
        )