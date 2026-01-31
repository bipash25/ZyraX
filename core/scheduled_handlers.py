"""
Scheduled action handlers
Executes actions that were scheduled (unbans, unmutes, antiraid disable, etc.)
"""
import logging
from telegram import Bot, ChatPermissions
from config import settings
from utils.time_parser import now_utc

logger = logging.getLogger(__name__)


async def execute_scheduled_unban(chat_id: int, user_id: int, db=None):
    """
    Execute scheduled unban action
    
    Args:
        chat_id: Chat ID
        user_id: User ID to unban
        db: Database instance (optional)
    """
    try:
        bot = Bot(token=settings.BOT_TOKEN)
        
        await bot.unban_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            only_if_banned=True
        )
        
        logger.info(f"Executed scheduled unban for user {user_id} in chat {chat_id}")
        
        # Log to database
        if db:
            await db.action_logs.insert_one({
                "chat_id": str(chat_id),
                "action_type": "scheduled_unban",
                "performed_by": "system",
                "target_user": str(user_id),
                "timestamp": now_utc()
            })
        
        # Delete scheduled action from database
        if db:
            await db.scheduled_actions.delete_many({
                "action_type": "unban",
                "chat_id": str(chat_id),
                "user_id": str(user_id)
            })
        
    except Exception as e:
        logger.error(f"Error executing scheduled unban for user {user_id} in chat {chat_id}: {e}")


async def execute_scheduled_unmute(chat_id: int, user_id: int, db=None):
    """
    Execute scheduled unmute action
    
    Args:
        chat_id: Chat ID
        user_id: User ID to unmute
        db: Database instance (optional)
    """
    try:
        bot = Bot(token=settings.BOT_TOKEN)
        
        # Restore full permissions
        permissions = ChatPermissions(
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
            can_invite_users=True
        )
        
        await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=permissions
        )
        
        logger.info(f"Executed scheduled unmute for user {user_id} in chat {chat_id}")
        
        # Log to database
        if db:
            await db.action_logs.insert_one({
                "chat_id": str(chat_id),
                "action_type": "scheduled_unmute",
                "performed_by": "system",
                "target_user": str(user_id),
                "timestamp": now_utc()
            })
        
        # Delete scheduled action from database
        if db:
            await db.scheduled_actions.delete_many({
                "action_type": "unmute",
                "chat_id": str(chat_id),
                "user_id": str(user_id)
            })
        
    except Exception as e:
        logger.error(f"Error executing scheduled unmute for user {user_id} in chat {chat_id}: {e}")


async def execute_scheduled_antiraid_disable(chat_id: int, db=None):
    """
    Execute scheduled antiraid disable
    
    Args:
        chat_id: Chat ID
        db: Database instance (optional)
    """
    try:
        if db:
            await db.chats.update_one(
                {"_id": str(chat_id)},
                {
                    "$set": {
                        "antiraid_enabled": False,
                        "antiraid_expires": None
                    }
                }
            )
            
            logger.info(f"Executed scheduled antiraid disable for chat {chat_id}")
            
            # Log to database
            await db.action_logs.insert_one({
                "chat_id": str(chat_id),
                "action_type": "scheduled_antiraid_disable",
                "performed_by": "system",
                "timestamp": now_utc()
            })
            
            # Delete scheduled action
            await db.scheduled_actions.delete_many({
                "action_type": "disable_antiraid",
                "chat_id": str(chat_id)
            })
        
    except Exception as e:
        logger.error(f"Error executing scheduled antiraid disable for chat {chat_id}: {e}")


async def execute_scheduled_action(action_type: str, chat_id: int, user_id: int = None, metadata: dict = None, db=None):
    """
    Generic executor for scheduled actions
    
    Args:
        action_type: Type of action (unban, unmute, disable_antiraid)
        chat_id: Chat ID
        user_id: User ID (for user-specific actions)
        metadata: Additional metadata
        db: Database instance
    """
    try:
        if action_type == "unban":
            await execute_scheduled_unban(chat_id, user_id, db)
        
        elif action_type == "unmute":
            await execute_scheduled_unmute(chat_id, user_id, db)
        
        elif action_type == "disable_antiraid":
            await execute_scheduled_antiraid_disable(chat_id, db)
        
        else:
            logger.warning(f"Unknown scheduled action type: {action_type}")
        
    except Exception as e:
        logger.error(f"Error executing scheduled action {action_type}: {e}")

