"""
Permapin Enforcer Middleware - Automatically re-pin permapinned messages
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


async def check_permapin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Monitor message_pinned events and re-pin if a permapinned message was unpinned
    """
    # Only process pinned_message updates
    if not update.message or not hasattr(update.message, 'pinned_message'):
        return
    
    # Check if this is an unpin event (pinned_message is None in some cases)
    # We'll monitor via a separate handler for message updates
    pass


async def monitor_unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Monitor for unpin events and re-pin if permapin is enabled
    
    This runs on channel_post updates to detect when linked channels unpin messages
    """
    try:
        # Only process in groups/supergroups
        if not update.effective_chat or update.effective_chat.type not in ['group', 'supergroup']:
            return
        
        chat_id = update.effective_chat.id
        
        # Get chat settings
        db = context.application.bot_data.get('database')
        if db is None:
            return
        
        chat_settings = await db.chats.find_one({"_id": str(chat_id)})
        
        # Check if permapin is enabled
        if not chat_settings or not chat_settings.get("permapin_enabled"):
            return
        
        permapin_message_id = chat_settings.get("permapin_message_id")
        if not permapin_message_id:
            return
        
        # Try to get current pinned message
        try:
            chat = await context.bot.get_chat(chat_id)
            current_pinned = chat.pinned_message
            
            # If no message is pinned or different message is pinned, re-pin the permapin message
            if not current_pinned or current_pinned.message_id != permapin_message_id:
                await context.bot.pin_chat_message(
                    chat_id=chat_id,
                    message_id=permapin_message_id,
                    disable_notification=True  # Always silent re-pin
                )
                
                logger.info(
                    f"Re-pinned permapinned message {permapin_message_id} in chat {chat_id}"
                )
                
                # Log action
                from datetime import datetime, timezone
                await db.action_logs.insert_one({
                    "chat_id": str(chat_id),
                    "action_type": "permapin_repin",
                    "message_id": permapin_message_id,
                    "performed_by": "bot_automatic",
                    "timestamp": datetime.now(timezone.utc)
                })
        
        except TelegramError as e:
            # Message might have been deleted or bot lost permissions
            if "message not found" in str(e).lower() or "message to pin not found" in str(e).lower():
                # Disable permapin since message no longer exists
                await db.chats.update_one(
                    {"_id": str(chat_id)},
                    {"$set": {"permapin_enabled": False}}
                )
                logger.warning(
                    f"Disabled permapin in chat {chat_id} - message {permapin_message_id} not found"
                )
            else:
                logger.error(f"Failed to re-pin message in chat {chat_id}: {e}")
    
    except Exception as e:
        logger.error(f"Error in permapin enforcer: {e}")


# This function will be called periodically by the scheduler
async def periodic_permapin_check(app):
    """
    Periodically check all chats with permapin enabled and ensure message is pinned
    
    This is a backup mechanism in case the event-based monitoring misses something
    
    Args:
        app: PTB Application instance
    """
    try:
        db = app.bot_data.get('database')
        bot = app.bot
        if db is None:
            return
        
        # Find all chats with permapin enabled
        cursor = db.chats.find({"permapin_enabled": True})
        
        async for chat_settings in cursor:
            chat_id = int(chat_settings["_id"])
            permapin_message_id = chat_settings.get("permapin_message_id")
            
            if not permapin_message_id:
                continue
            
            try:
                # Get current pinned message
                chat = await bot.get_chat(chat_id)
                current_pinned = chat.pinned_message
                
                # If no message is pinned or different message is pinned, re-pin
                if not current_pinned or current_pinned.message_id != permapin_message_id:
                    await bot.pin_chat_message(
                        chat_id=chat_id,
                        message_id=permapin_message_id,
                        disable_notification=True
                    )
                    
                    logger.info(
                        f"[Periodic] Re-pinned permapinned message {permapin_message_id} in chat {chat_id}"
                    )
            
            except TelegramError as e:
                # Message might have been deleted
                if "message not found" in str(e).lower() or "message to pin not found" in str(e).lower():
                    await db.chats.update_one(
                        {"_id": str(chat_id)},
                        {"$set": {"permapin_enabled": False}}
                    )
                    logger.warning(
                        f"[Periodic] Disabled permapin in chat {chat_id} - message not found"
                    )
    
    except Exception as e:
        logger.error(f"Error in periodic permapin check: {e}")