"""
Ban command - Ban users from the chat
Supports: /ban, /tban, /sban, /dban
"""
import logging
from datetime import timedelta
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, require_bot_admin, not_self, log_command
from utils.user_resolver import resolve_user, mention_user
from utils.time_parser import parse_time_with_reason, format_time, validate_duration, now_utc

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "ban",
    "aliases": ["tban", "sban", "dban"],
    "description": "Ban a user from the chat",
    "usage": "/ban <reply|@username|ID> [duration] [reason]\n"
             "/tban <reply|@username|ID> <duration> [reason] - Temporary ban\n"
             "/sban <reply|@username|ID> [duration] [reason] - Silent ban (no message)\n"
             "/dban <reply|@username|ID> [duration] [reason] - Delete message and ban",
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
    Handle /ban, /tban, /sban, /dban commands
    
    - /ban: Permanent ban
    - /tban: Temporary ban (requires duration)
    - /sban: Silent ban (no notification)
    - /dban: Delete command message and ban
    
    Args:
        update: Telegram update
        context: PTB context
    """
    chat_id = update.effective_chat.id
    admin_user = update.effective_user
    message = update.effective_message
    
    # Get command variant
    command = message.text.split()[0].lower().lstrip('/')
    is_tban = command == "tban"
    is_silent = command == "sban"
    is_delete = command == "dban"
    
    # Resolve target user
    target_user, resolve_method = await resolve_user(update, context)
    
    if not target_user:
        await message.reply_html(
            "❌ <b>Please specify a user to ban.</b>\n\n"
            "<b>Usage:</b>\n"
            "• Reply to user's message with /ban\n"
            "• /ban @username [duration] [reason]\n"
            "• /ban &lt;user_id&gt; [duration] [reason]\n\n"
            "<b>Examples:</b>\n"
            "• /ban @username spam\n"
            "• /tban @username 5d spamming\n"
            "• /ban 123456789 3h breaking rules"
        )
        return
    
    # Check if target is an admin
    try:
        target_member = await context.bot.get_chat_member(chat_id, target_user.id)
        if target_member.status in ["administrator", "creator"]:
            await message.reply_text(
                "❌ I cannot ban administrators."
            )
            return
    except Exception as e:
        logger.error(f"Error checking target member status: {e}")
    
    # Parse duration and reason
    args = context.args[1:] if resolve_method != "reply" else context.args
    duration_seconds, reason = parse_time_with_reason(args)
    
    # Validate requirements for tban
    if is_tban and not duration_seconds:
        await message.reply_html(
            "❌ <b>Temporary ban requires a duration.</b>\n\n"
            "<b>Usage:</b> /tban &lt;user&gt; &lt;duration&gt; [reason]\n\n"
            "<b>Duration formats:</b>\n"
            "• 5m = 5 minutes\n"
            "• 2h = 2 hours\n"
            "• 3d = 3 days\n"
            "• 1w = 1 week\n\n"
            "<b>Example:</b> /tban @username 3d spamming"
        )
        return
    
    # Validate duration if provided
    if duration_seconds:
        is_valid, error_msg = validate_duration(duration_seconds)
        if not is_valid:
            await message.reply_text(f"❌ {error_msg}")
            return
    
    # Perform ban
    try:
        # Calculate unban date for temporary bans
        until_date = None
        if duration_seconds:
            until_date = now_utc() + timedelta(seconds=duration_seconds)
        
        # Ban the user
        await context.bot.ban_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            until_date=until_date
        )
        
        # Delete command message if dban
        if is_delete:
            try:
                await message.delete()
            except Exception as e:
                logger.debug(f"Could not delete command message: {e}")
        
        # Send confirmation (unless silent)
        if not is_silent:
            target_mention = mention_user(target_user, use_html=True)
            admin_mention = mention_user(admin_user, use_html=True)
            
            ban_text = f"🔨 {target_mention} has been <b>banned</b>"
            
            if duration_seconds:
                ban_text += f" for <b>{format_time(duration_seconds)}</b>"
            else:
                ban_text += " <b>permanently</b>"
            
            ban_text += f" by {admin_mention}."
            
            if reason:
                ban_text += f"\n\n<b>Reason:</b> {reason}"
            
            await message.reply_html(ban_text)
        
        # Log to database
        try:
            db = context.application.bot_data.get('database')
            if db is not None:
                await db.action_logs.insert_one({
                    "chat_id": str(chat_id),
                    "action_type": "tban" if duration_seconds else "ban",
                    "performed_by": str(admin_user.id),
                    "target_user": str(target_user.id),
                    "reason": reason or "No reason provided",
                    "duration": duration_seconds,
                    "timestamp": now_utc()
                })
        except Exception as e:
            logger.error(f"Error logging ban action: {e}")
        
        logger.info(
            f"User {target_user.id} banned in chat {chat_id} by admin {admin_user.id} "
            f"{'for ' + format_time(duration_seconds) if duration_seconds else 'permanently'}"
        )
        
    except Exception as e:
        logger.error(f"Error banning user {target_user.id} in chat {chat_id}: {e}")
        await message.reply_html(
            f"❌ <b>Failed to ban user.</b>\n\n"
            f"Error: {str(e)}"
        )

