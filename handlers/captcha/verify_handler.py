"""
Captcha verification handlers - Process user answers
Handles both callback queries (buttons) and text messages (math/text captcha)
"""
import logging
import asyncio
from datetime import timezone
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, MessageHandler, CallbackQueryHandler, filters

from utils.crypto import verify_answer
from utils.time_parser import now_utc

logger = logging.getLogger(__name__)

# Lock to prevent race conditions during captcha verification
# Key format: "chat_id:user_id"
_captcha_locks = {}
_locks_lock = asyncio.Lock()  # Lock for the locks dict itself


async def get_captcha_lock(chat_id: int, user_id: int):
    """Get or create a lock for a specific user's captcha verification"""
    key = f"{chat_id}:{user_id}"
    async with _locks_lock:
        if key not in _captcha_locks:
            _captcha_locks[key] = asyncio.Lock()
        return _captcha_locks[key]


async def release_captcha_lock(chat_id: int, user_id: int):
    """Release and cleanup a captcha lock"""
    key = f"{chat_id}:{user_id}"
    async with _locks_lock:
        if key in _captcha_locks:
            del _captcha_locks[key]


async def handle_captcha_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle text answer for math/text captcha
    
    Args:
        update: Telegram update
        context: PTB context
    """
    if not update.message or not update.message.text:
        return
    
    user = update.effective_user
    chat = update.effective_chat
    user_answer = update.message.text.strip().lower()
    
    # Check if user has pending captcha
    db = context.application.bot_data.get('database')
    if db is None:
        return
    
    # Acquire lock to prevent race conditions
    lock = await get_captcha_lock(chat.id, user.id)
    async with lock:
        try:
            pending = await db.captcha_pending.find_one({
                "chat_id": str(chat.id),
                "user_id": str(user.id)
            })
        
            if not pending:
                return  # No pending captcha for this user
            
            # Check if expired
            expires_at = pending['expires_at'].replace(tzinfo=timezone.utc) if pending['expires_at'].tzinfo is None else pending['expires_at']
            now = now_utc()
            
            if expires_at < now:
                await update.message.reply_html(
                    "⏱️ <b>Captcha expired!</b> Please contact an admin."
                )
                return
            
            # Verify answer using hash
            answer_hash = pending.get('answer_hash')
            salt = pending.get('salt')
            
            # Backward compatibility: check if old plaintext answer exists
            if answer_hash and salt:
                is_correct = verify_answer(user_answer, answer_hash, salt)
            else:
                # Fallback to plaintext comparison (for migration period)
                correct_answer = pending.get('answer', '').lower()
                is_correct = user_answer == correct_answer
            
            if is_correct:
                # Correct! Unmute the user
                await chat.restrict_member(
                    user.id,
                    permissions=ChatPermissions(
                        can_send_messages=True,
                        can_send_audios=True,
                        can_send_documents=True,
                        can_send_photos=True,
                        can_send_videos=True,
                        can_send_video_notes=True,
                        can_send_voice_notes=True,
                        can_send_polls=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True,
                        can_change_info=False,
                        can_invite_users=True,
                        can_pin_messages=False,
                        can_manage_topics=False
                    ),
                    until_date=None
                )
                
                # Remove pending captcha
                await db.captcha_pending.delete_one({
                    "chat_id": str(chat.id),
                    "user_id": str(user.id)
                })
                
                # Cancel timeout job
                scheduler = context.application.bot_data.get('scheduler')
                if scheduler:
                    scheduler.cancel_action(f"captcha_timeout_{chat.id}_{user.id}")
                
                await update.message.reply_html(
                    f"✅ <b>Welcome, {user.mention_html()}!</b>\n\n"
                    f"You have been verified successfully."
                )
                
                # Delete captcha messages
                try:
                    await update.message.delete()
                except Exception:
                    pass
                
                logger.info(f"User {user.id} passed captcha in chat {chat.id}")
            
            else:
                # Wrong answer - increment attempts
                attempts = pending.get('attempts', 0) + 1
                max_attempts = pending.get('max_attempts', 3)
                
                if attempts >= max_attempts:
                    # Max attempts reached - kick user
                    await db.captcha_pending.delete_one({
                        "chat_id": str(chat.id),
                        "user_id": str(user.id)
                    })
                    
                    # Cancel timeout job
                    scheduler = context.application.bot_data.get('scheduler')
                    if scheduler:
                        scheduler.cancel_action(f"captcha_timeout_{chat.id}_{user.id}")
                    
                    # Kick user (ban then unban)
                    try:
                        await chat.ban_member(user.id)
                        await chat.unban_member(user.id)
                        
                        await context.bot.send_message(
                            chat.id,
                            f"❌ {user.mention_html()} failed verification after {max_attempts} attempts and was removed.",
                            parse_mode='HTML'
                        )
                        
                        # Log failure
                        await db.action_logs.insert_one({
                            "chat_id": str(chat.id),
                            "user_id": str(user.id),
                            "action_type": "captcha_failed",
                            "attempts": attempts,
                            "timestamp": now_utc()
                        })
                        
                        logger.info(f"User {user.id} failed captcha in chat {chat.id} after {attempts} attempts")
                        
                    except Exception as e:
                        logger.error(f"Failed to kick user after max attempts: {e}")
                    
                    # Delete wrong answer
                    try:
                        await update.message.delete()
                    except Exception:
                        pass
                else:
                    # Increment attempts
                    await db.captcha_pending.update_one(
                        {"chat_id": str(chat.id), "user_id": str(user.id)},
                        {"$set": {"attempts": attempts}}
                    )
                    
                    remaining = max_attempts - attempts
                    await update.message.reply_html(
                        f"❌ <b>Wrong answer!</b>\n\n"
                        f"🔄 You have {remaining} attempt{'s' if remaining != 1 else ''} remaining.\n"
                        f"Please try again carefully."
                    )
                    
                    # Delete wrong answer
                    try:
                        await update.message.delete()
                    except Exception:
                        pass
        
        except Exception as e:
            logger.error(f"Error handling captcha answer: {e}")
    
    await release_captcha_lock(chat.id, user.id)


async def handle_captcha_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle button click for button captcha
    
    Args:
        update: Telegram update
        context: PTB context
    """
    query = update.callback_query
    await query.answer()
    
    # Check if this is a captcha button (format: cap_{token}_{answer})
    if not query.data.startswith("cap_"):
        return
    
    user = update.effective_user
    chat = update.effective_chat
    
    # Acquire lock to prevent race conditions
    lock = await get_captcha_lock(chat.id, user.id)
    async with lock:
        # Parse callback data: cap_{token}_{answer}
        parts = query.data.split("_", 2)
        if len(parts) != 3:
            return
        
        token = parts[1]
        user_answer = parts[2]
        
        user = query.from_user
        chat = query.message.chat
        
        # Check if user has pending captcha
        db = context.application.bot_data.get('database')
        if db is None:
            return
        
        try:
            # Find pending captcha by token
            pending = await db.captcha_pending.find_one({
                "chat_id": str(chat.id),
                "token": token
            })
            
            if not pending:
                await query.answer("❌ No pending captcha found!", show_alert=True)
                return
            
            # Check if the person clicking is the one who should solve it
            expected_user_id = int(pending['user_id'])
            if user.id != expected_user_id:
                await query.answer("❌ This captcha is not for you!", show_alert=True)
                return
        
            # Debug: Log what we retrieved from database
            logger.info(
            f"[CAPTCHA DEBUG] Retrieved from DB (button click):\n"
            f"  Chat ID: {chat.id}\n"
            f"  User ID: {user.id}\n"
            f"  Pending Data: {pending}\n"
            f"  Expires At (raw): {pending['expires_at']} (type: {type(pending['expires_at'])})\n"
            f"  Expires At tzinfo: {pending['expires_at'].tzinfo if hasattr(pending['expires_at'], 'tzinfo') else 'N/A'}"
            )
            
            # Check if expired (MongoDB stores naive UTC, convert to aware)
            expires_at = pending['expires_at'].replace(tzinfo=timezone.utc) if pending['expires_at'].tzinfo is None else pending['expires_at']
            now = now_utc()
            
            logger.info(
            f"[CAPTCHA DEBUG] Expiration check (button click):\n"
            f"  Now: {now} (type: {type(now)}, tz: {now.tzinfo})\n"
            f"  Expires At (converted): {expires_at} (type: {type(expires_at)}, tz: {expires_at.tzinfo})\n"
            f"  Is Expired: {expires_at < now}\n"
            f"  Time Remaining: {(expires_at - now).total_seconds()}s"
            )
            
            if expires_at < now:
                await query.answer("⏱️ Captcha expired! Contact an admin.", show_alert=True)
                return
            
            # Check answer using secure hash
            answer_hash = pending.get('answer_hash')
            salt = pending.get('salt')
            
            # Verify the answer
            from utils.crypto import verify_answer
            is_correct = verify_answer(user_answer, answer_hash, salt)
            
            if is_correct:
                # Correct! Unmute the user
                await chat.restrict_member(
                user.id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_audios=True,
                    can_send_documents=True,
                    can_send_photos=True,
                    can_send_videos=True,
                    can_send_video_notes=True,
                    can_send_voice_notes=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_change_info=False,
                    can_invite_users=True,
                    can_pin_messages=False,
                    can_manage_topics=False
                    ),
                    until_date=None
                )
                
                # Remove pending captcha
                await db.captcha_pending.delete_one({
                    "chat_id": str(chat.id),
                    "user_id": str(user.id)
                })
                
                # Cancel timeout job
                scheduler = context.application.bot_data.get('scheduler')
                if scheduler:
                    scheduler.cancel_action(f"captcha_timeout_{chat.id}_{user.id}")
                
                # Update message
                await query.edit_message_text(
                    f"✅ <b>Welcome, {user.mention_html()}!</b>\n\n"
                    f"You have been verified successfully.",
                    parse_mode='HTML'
                )
                
                logger.info(f"User {user.id} passed button captcha in chat {chat.id}")
            
            else:
                # Wrong answer - increment attempts
                attempts = pending.get('attempts', 0) + 1
                max_attempts = pending.get('max_attempts', 3)
                
                if attempts >= max_attempts:
                    # Max attempts reached - kick user
                    await db.captcha_pending.delete_one({
                        "chat_id": str(chat.id),
                        "user_id": str(user.id)
                    })
                    
                    # Cancel timeout job
                    scheduler = context.application.bot_data.get('scheduler')
                    if scheduler:
                        scheduler.cancel_action(f"captcha_timeout_{chat.id}_{user.id}")
                    
                    # Kick user (ban then unban)
                    try:
                        await chat.ban_member(user.id)
                        await chat.unban_member(user.id)
                        
                        # Update message
                        await query.edit_message_text(
                            f"❌ {user.mention_html()} failed verification after {max_attempts} attempts and was removed.",
                            parse_mode='HTML'
                        )
                        
                        # Log failure
                        await db.action_logs.insert_one({
                            "chat_id": str(chat.id),
                            "user_id": str(user.id),
                            "action_type": "captcha_failed",
                            "attempts": attempts,
                            "timestamp": now_utc()
                        })
                        
                        logger.info(f"User {user.id} failed button captcha in chat {chat.id} after {attempts} attempts")
                        
                    except Exception as e:
                        logger.error(f"Failed to kick user after max attempts: {e}")
                        await query.answer("❌ Verification failed. You were removed.", show_alert=True)
                else:
                    # Increment attempts
                    await db.captcha_pending.update_one(
                        {"chat_id": str(chat.id), "user_id": str(user.id)},
                        {"$set": {"attempts": attempts}}
                    )
                    
                    remaining = max_attempts - attempts
                    await query.answer(
                        f"❌ Wrong! {remaining} attempt{'s' if remaining != 1 else ''} remaining.",
                        show_alert=True
                    )
        
        except Exception as e:
            logger.error(f"Error handling captcha button: {e}")


def get_message_handler():
    """Get the message handler for text captcha answers"""
    return MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
        handle_captcha_answer
    )


def get_callback_handler():
    """Get the callback handler for button captcha"""
    return CallbackQueryHandler(handle_captcha_button, pattern="^cap_")