"""
Mute command - Restrict users from sending messages
Supports: /mute, /tmute, /smute, /dmute
"""
import logging
from datetime import timedelta
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, require_bot_admin, not_self, log_command
from utils.user_resolver import resolve_user, mention_user
from utils.time_parser import parse_time_with_reason, format_time, validate_duration, now_utc

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "mute",
    "aliases": ["tmute", "smute", "dmute"],
    "description": "Mute a user in the chat",
    "usage": "/mute <reply|@username|ID> [duration] [reason]\n"
             "/tmute <reply|@username|ID> <duration> [reason] - Temporary mute\n"
             "/smute <reply|@username|ID> [duration] [reason] - Silent mute (no message)\n"
             "/dmute <reply|@username|ID> [duration] [reason] - Delete message and mute",
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
    Handle /mute, /tmute, /smute, /dmute commands
    
    - /mute: Permanent mute (until manually unmuted)
    - /tmute: Temporary mute (requires duration)
    - /smute: Silent mute (no notification)
    - /dmute: Delete command message and mute
    
    Args:
        update: Telegram update
        context: PTB context
    """
    chat_id = update.effective_chat.id
    admin_user = update.effective_user
    message = update.effective_message
    
    # Get command variant
    command = message.text.split()[0].lower().lstrip('/')
    is_tmute = command == "tmute"
    is_silent = command == "smute"
    is_delete = command == "dmute"
    
    # Resolve target user
    target_user, resolve_method = await resolve_user(update, context)
    
    if not target_user:
        await message.reply_html(
            "❌ <b>Please specify a user to mute.</b>\n\n"
            "<b>Usage:</b>\n"
            "• Reply to user's message with /mute\n"
            "• /mute @username [duration] [reason]\n"
            "• /mute &lt;user_id&gt; [duration] [reason]\n\n"
            "<b>Examples:</b>\n"
            "• /mute @username spam\n"
            "• /tmute @username 5m flood\n"
            "• /mute 123456789 1h off-topic"
        )
        return
    
    # Check if target is an admin
    try:
        target_member = await context.bot.get_chat_member(chat_id, target_user.id)
        if target_member.status in ["administrator", "creator"]:
            await message.reply_text(
                "❌ I cannot mute administrators."
            )
            return
    except Exception as e:
        logger.error(f"Error checking target member status: {e}")
    
    # Parse duration and reason
    args = context.args[1:] if resolve_method != "reply" else context.args
    duration_seconds, reason = parse_time_with_reason(args)
    
    # Validate requirements for tmute
    if is_tmute and not duration_seconds:
        await message.reply_html(
            "❌ <b>Temporary mute requires a duration.</b>\n\n"
            "<b>Usage:</b> /tmute &lt;user&gt; &lt;duration&gt; [reason]\n\n"
            "<b>Duration formats:</b>\n"
            "• 5m = 5 minutes\n"
            "• 2h = 2 hours\n"
            "• 3d = 3 days\n"
            "• 1w = 1 week\n\n"
            "<b>Example:</b> /tmute @username 30m flooding"
        )
        return
    
    # Validate duration if provided
    if duration_seconds:
        is_valid, error_msg = validate_duration(duration_seconds)
        if not is_valid:
            await message.reply_text(f"❌ {error_msg}")
            return
    
    # Perform mute
    try:
        # Calculate unmute date for temporary mutes
        until_date = None
        if duration_seconds:
            until_date = now_utc() + timedelta(seconds=duration_seconds)
        
        # Create restricted permissions (no messages, no media, no other content)
        # Note: PTB v20+ uses different permission structure
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_audios=False,
            can_send_documents=False,
            can_send_photos=False,
            can_send_videos=False,
            can_send_video_notes=False,
            can_send_voice_notes=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )
        
        # Restrict the user
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            permissions=permissions,
            until_date=until_date
        )
        
        # Delete command message if dmute
        if is_delete:
            try:
                await message.delete()
            except Exception as e:
                logger.debug(f"Could not delete command message: {e}")
        
        # Send confirmation (unless silent)
        if not is_silent:
            target_mention = mention_user(target_user, use_html=True)
            admin_mention = mention_user(admin_user, use_html=True)
            
            mute_text = f"🔇 {target_mention} has been <b>muted</b>"
            
            if duration_seconds:
                mute_text += f" for <b>{format_time(duration_seconds)}</b>"
            else:
                mute_text += " <b>permanently</b>"
            
            mute_text += f" by {admin_mention}."
            
            if reason:
                mute_text += f"\n\n<b>Reason:</b> {reason}"
            
            await message.reply_html(mute_text)
        
        # Log to database
        try:
            db = context.application.bot_data.get('database')
            if db is not None:
                await db.action_logs.insert_one({
                    "chat_id": str(chat_id),
                    "action_type": "tmute" if duration_seconds else "mute",
                    "performed_by": str(admin_user.id),
                    "target_user": str(target_user.id),
                    "reason": reason or "No reason provided",
                    "duration": duration_seconds,
                    "timestamp": now_utc()
                })
        except Exception as e:
            logger.error(f"Error logging mute action: {e}")
        
        logger.info(
            f"User {target_user.id} muted in chat {chat_id} by admin {admin_user.id} "
            f"{'for ' + format_time(duration_seconds) if duration_seconds else 'permanently'}"
        )
        
    except Exception as e:
        logger.error(f"Error muting user {target_user.id} in chat {chat_id}: {e}")
        await message.reply_html(
            f"❌ <b>Failed to mute user.</b>\n\n"
            f"Error: {str(e)}"
        )