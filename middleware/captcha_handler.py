"""
Captcha verification handler - Challenge new members
"""
import logging
from datetime import datetime, timezone, timedelta
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus

from utils.captcha_generator import (
    generate_math_captcha,
    generate_text_captcha,
    generate_button_captcha,
    generate_number_button_captcha
)
from utils.rate_limiter import (
    check_rate_limit,
    log_captcha_attempt,
    handle_rate_limit_violation
)
from utils.crypto import (
    generate_salt,
    generate_secure_token,
    hash_answer
)

logger = logging.getLogger(__name__)


async def handle_new_member_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Challenge new members with captcha verification
    
    This is called when a new member joins the chat.
    If captcha is enabled, present them with a challenge.
    
    Args:
        update: Telegram update
        context: PTB context
    """
    # Only process chat_member updates for new joins
    if not update.chat_member:
        return
    
    chat_member_update = update.chat_member
    old_status = chat_member_update.old_chat_member.status
    new_status = chat_member_update.new_chat_member.status
    
    # Check if this is actually a new member join
    if old_status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return  # Already was a member
    
    if new_status not in [ChatMemberStatus.MEMBER]:
        return  # Not a regular member join
    
    chat = chat_member_update.chat
    new_member = chat_member_update.new_chat_member.user
    
    # Don't challenge bots
    if new_member.is_bot:
        return
    
    chat_id = chat.id
    user_id = new_member.id
    
    try:
        # Check if captcha is enabled
        db = context.application.bot_data.get('database')
        if db is None:
            return
        
        # Check rate limiting FIRST (before any other checks)
        if await check_rate_limit(db, chat_id, user_id):
            logger.warning(f"Rate limit exceeded for user {user_id} in chat {chat_id}")
            await handle_rate_limit_violation(context, chat_id, user_id, new_member.mention_html())
            return
        
        # Log this attempt
        await log_captcha_attempt(db, chat_id, user_id)
        
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        
        if not chat_doc or not chat_doc.get('captcha_enabled', False):
            return  # Captcha not enabled
        
        # Check if user is whitelisted (bypasses captcha permanently)
        whitelist = chat_doc.get("captcha_whitelist", [])
        if str(user_id) in whitelist:
            logger.info(f"User {user_id} is whitelisted, bypassing captcha in chat {chat_id}")
            return  # Whitelisted users bypass captcha
        
        # Check if user is approved (bypasses captcha)
        user_doc = await db.users.find_one({"_id": str(user_id)})
        if user_doc and user_doc.get('chat_data', {}).get(str(chat_id), {}).get('approved', False):
            logger.info(f"User {user_id} is approved, bypassing captcha in chat {chat_id}")
            return  # Approved users bypass captcha
        
        # Get captcha mode to determine permissions
        mode = chat_doc.get('captcha_mode', 'button')
        
        # For math/text mode, allow sending messages so they can answer
        # For button mode, restrict all permissions
        allow_messages = mode in ['math', 'text']
        
        # Restrict the new member until they solve captcha
        await chat.restrict_member(
            user_id,
            permissions=ChatPermissions(
                can_send_messages=allow_messages,  # Allow for math/text mode
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
                can_pin_messages=False,
                can_manage_topics=False
            ),
            until_date=None
        )
        
        # Get captcha settings (mode already retrieved above)
        timeout = chat_doc.get('captcha_timeout', 120)
        
        # Generate captcha based on mode
        if mode == 'math':
            question, answer = generate_math_captcha()
            
            message_text = (
                f"👋 Welcome {new_member.mention_html()}!\n\n"
                f"🔐 Please solve this math problem to verify you're human:\n\n"
                f"<b>{question}</b>\n\n"
                f"⏱️ You have {timeout} seconds to answer."
            )
            
            # Delete any existing captcha for this user first
            await db.captcha_pending.delete_many({
                "chat_id": str(chat_id),
                "user_id": str(user_id)
            })
            
            # Generate secure hash and token
            salt = generate_salt()
            answer_hash = hash_answer(answer.lower(), salt)
            token = generate_secure_token()
            
            # Store the answer in database
            created_at = datetime.now(timezone.utc)
            expires_at = created_at + timedelta(seconds=timeout)
            
            logger.info(
                f"Math captcha created for user {user_id} in chat {chat_id}"
            )
            
            await db.captcha_pending.insert_one({
                "chat_id": str(chat_id),
                "user_id": str(user_id),
                "answer_hash": answer_hash,
                "salt": salt,
                "token": token,
                "mode": mode,
                "attempts": 0,
                "max_attempts": 3,
                "expires_at": expires_at,
                "created_at": created_at
            })
            
            sent_message = await context.bot.send_message(
                chat_id,
                message_text,
                parse_mode='HTML'
            )
        
        elif mode == 'button':
            correct_emoji, options = generate_button_captcha()
            
            message_text = (
                f"👋 Welcome {new_member.mention_html()}!\n\n"
                f"🔐 Please click the <b>{correct_emoji}</b> button to verify you're human:\n\n"
                f"⏱️ You have {timeout} seconds to answer."
            )
            
            # Generate secure hash and token
            salt = generate_salt()
            answer_hash = hash_answer(correct_emoji, salt)
            token = generate_secure_token()
            
            # Create inline keyboard with secure token
            keyboard = []
            row = []
            for i, emoji in enumerate(options):
                row.append(InlineKeyboardButton(
                    emoji,
                    callback_data=f"cap_{token}_{emoji}"
                ))
                if (i + 1) % 2 == 0:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Delete any existing captcha for this user first
            await db.captcha_pending.delete_many({
                "chat_id": str(chat_id),
                "user_id": str(user_id)
            })
            
            # Store the answer
            created_at = datetime.now(timezone.utc)
            expires_at = created_at + timedelta(seconds=timeout)
            
            logger.info(
                f"Button captcha created for user {user_id} in chat {chat_id} (token: {token[:8]}...)"
            )
            
            await db.captcha_pending.insert_one({
                "chat_id": str(chat_id),
                "user_id": str(user_id),
                "answer_hash": answer_hash,
                "salt": salt,
                "token": token,
                "mode": mode,
                "attempts": 0,
                "max_attempts": 3,
                "expires_at": expires_at,
                "created_at": created_at
            })
            
            sent_message = await context.bot.send_message(
                chat_id,
                message_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        elif mode == 'text':
            captcha_text = generate_text_captcha(6)
            
            message_text = (
                f"👋 Welcome {new_member.mention_html()}!\n\n"
                f"🔐 Please type the following text to verify you're human:\n\n"
                f"<code>{captcha_text}</code>\n\n"
                f"⏱️ You have {timeout} seconds to answer."
            )
            
            # Generate secure hash and token
            salt = generate_salt()
            answer_hash = hash_answer(captcha_text.lower(), salt)
            token = generate_secure_token()
            
            # Delete any existing captcha for this user first
            await db.captcha_pending.delete_many({
                "chat_id": str(chat_id),
                "user_id": str(user_id)
            })
            
            # Store the answer
            created_at = datetime.now(timezone.utc)
            expires_at = created_at + timedelta(seconds=timeout)
            
            logger.info(
                f"Text captcha created for user {user_id} in chat {chat_id}"
            )
            
            await db.captcha_pending.insert_one({
                "chat_id": str(chat_id),
                "user_id": str(user_id),
                "answer_hash": answer_hash,
                "salt": salt,
                "token": token,
                "mode": mode,
                "attempts": 0,
                "max_attempts": 3,
                "expires_at": expires_at,
                "created_at": created_at
            })
            
            sent_message = await context.bot.send_message(
                chat_id,
                message_text,
                parse_mode='HTML'
            )
        
        # Schedule timeout action
        scheduler = context.application.bot_data.get('scheduler')
        if scheduler:
            scheduler.schedule_captcha_timeout(
                chat_id=chat_id,
                user_id=user_id,
                timeout_func=handle_captcha_timeout,
                duration=timeout,
                context=context
            )
        
        logger.info(
            f"Captcha challenge sent to user {user_id} in chat {chat_id} "
            f"(mode: {mode})"
        )
        
    except Exception as e:
        logger.error(f"Error in captcha handler for chat {chat_id}: {e}")


async def handle_captcha_timeout(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle captcha timeout - kick/ban user if they didn't solve it
    
    Args:
        chat_id: Chat ID
        user_id: User ID
        context: Bot context
    """
    logger.info(f"Captcha timeout for user {user_id} in chat {chat_id}")
    
    db = context.application.bot_data.get('database')
    if db is None:
        logger.error("Database not available for captcha timeout")
        return
    
    try:
        # Check if captcha still pending
        pending = await db.captcha_pending.find_one({
            "chat_id": str(chat_id),
            "user_id": str(user_id)
        })
        
        if not pending:
            logger.debug(f"No pending captcha for user {user_id} in chat {chat_id} (already solved)")
            return  # Already solved or removed
        
        # Get chat settings
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        kick_on_fail = chat_doc.get('captcha_kick', False) if chat_doc else False
        
        # Delete captcha message if exists
        message_id = pending.get('message_id')
        if message_id:
            try:
                await context.bot.delete_message(chat_id, message_id)
            except Exception as e:
                logger.debug(f"Could not delete captcha message {message_id}: {e}")
        
        # Remove pending captcha from database
        await db.captcha_pending.delete_one({
            "chat_id": str(chat_id),
            "user_id": str(user_id)
        })
        
        # Take action based on settings
        if kick_on_fail:
            try:
                # Kick user (ban then unban)
                await context.bot.ban_chat_member(chat_id, user_id)
                await context.bot.unban_chat_member(chat_id, user_id)
                
                await context.bot.send_message(
                    chat_id,
                    f"⏱️ <b>Verification timed out.</b>\n\nUser was removed from the chat.",
                    parse_mode='HTML'
                )
                
                logger.info(f"Kicked user {user_id} from chat {chat_id} (captcha timeout)")
                
            except Exception as e:
                logger.error(f"Failed to kick user {user_id} from chat {chat_id}: {e}")
        else:
            # Just notify, keep user muted
            try:
                await context.bot.send_message(
                    chat_id,
                    f"⏱️ <b>Captcha verification timed out.</b>\n\n"
                    f"Please contact an admin to be manually verified.",
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Failed to send timeout message to chat {chat_id}: {e}")
        
        # Log the timeout event
        await db.action_logs.insert_one({
            "chat_id": str(chat_id),
            "user_id": str(user_id),
            "action_type": "captcha_timeout",
            "kicked": kick_on_fail,
            "timestamp": datetime.now(timezone.utc)
        })
        
    except Exception as e:
        logger.error(f"Error handling captcha timeout for user {user_id} in chat {chat_id}: {e}", exc_info=True)