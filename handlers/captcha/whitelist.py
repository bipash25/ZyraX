"""
Whitelist a user from captcha permanently
Command: /whitelist <user>
"""

from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import require_admin, group_only, log_command
from utils.user_resolver import resolve_user
from utils.time_parser import now_utc
import logging

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "whitelist",
    "aliases": ["unwhitelist"],
    "description": "Whitelist/unwhitelist user from captcha",
    "usage": "/whitelist <user> or /unwhitelist <user>",
    "category": "captcha",
    "permissions": ["can_restrict_members"],
    "admin_only": True,
    "group_only": True
}

@require_admin(permissions=["can_restrict_members"])
@group_only
@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Whitelist or unwhitelist user from captcha"""
    chat_id = str(update.effective_chat.id)
    message = update.message
    command = message.text.split()[0].lower().replace('/', '')
    
    is_whitelist = command == "whitelist"
    
    # Resolve target user
    target_user = await resolve_user(update, context)
    
    if not target_user:
        action = "whitelist" if is_whitelist else "unwhitelist"
        await message.reply_text(
            f"❌ Please specify a user to {action}.\n\n"
            "<b>Usage:</b>\n"
            f"• Reply to the user's message with <code>/{action}</code>\n"
            f"• <code>/{action} @username</code>\n"
            f"• <code>/{action} userid</code>",
            parse_mode="HTML"
        )
        return
    
    user_id = str(target_user.id)
    
    try:
        # Get database
        db = context.application.bot_data.get('database')
        if not db:
            await message.reply_text("❌ Database not available")
            return
        
        # Get or create chat settings
        chat_settings = await db.chats.find_one({"_id": chat_id})
        
        if not chat_settings:
            chat_settings = {
                "_id": chat_id,
                "captcha_enabled": False,
                "captcha_whitelist": []
            }
            await db.chats.insert_one(chat_settings)
        
        # Get current whitelist
        whitelist = chat_settings.get("captcha_whitelist", [])
        
        if is_whitelist:
            # Add to whitelist
            if user_id in whitelist:
                await message.reply_text(
                    f"ℹ️ {target_user.mention_html()} is already whitelisted.",
                    parse_mode="HTML"
                )
                return
            
            whitelist.append(user_id)
            
            # Update database
            await db.chats.update_one(
                {"_id": chat_id},
                {"$set": {"captcha_whitelist": whitelist}}
            )
            
            # If user is currently pending, verify them
            pending = await db.captcha_pending.find_one({
                "chat_id": chat_id,
                "user_id": user_id
            })
            
            if pending:
                # Remove from pending
                await db.captcha_pending.delete_one({
                    "chat_id": chat_id,
                    "user_id": user_id
                })
                
                # Unmute the user
                try:
                    await context.bot.restrict_chat_member(
                        chat_id=int(chat_id),
                        user_id=target_user.id,
                        permissions={
                            'can_send_messages': True,
                            'can_send_media_messages': True,
                            'can_send_polls': True,
                            'can_send_other_messages': True,
                            'can_add_web_page_previews': True,
                            'can_change_info': False,
                            'can_invite_users': True,
                            'can_pin_messages': False
                        }
                    )
                except Exception as e:
                    logger.error(f"Error unmuting whitelisted user: {e}")
                
                # Delete captcha message
                if pending.get("message_id"):
                    try:
                        await context.bot.delete_message(
                            chat_id=int(chat_id),
                            message_id=pending["message_id"]
                        )
                    except Exception:
                        pass
            
            # Log the action
            await db.action_logs.insert_one({
                "chat_id": chat_id,
                "action_type": "captcha_whitelist",
                "performed_by": str(message.from_user.id),
                "target_user": user_id,
                "timestamp": now_utc()
            })
            
            await message.reply_text(
                f"✅ {target_user.mention_html()} has been whitelisted from captcha!\n\n"
                "This user will bypass captcha verification on all future joins.",
                parse_mode="HTML"
            )
        
        else:
            # Remove from whitelist
            if user_id not in whitelist:
                await message.reply_text(
                    f"ℹ️ {target_user.mention_html()} is not whitelisted.",
                    parse_mode="HTML"
                )
                return
            
            whitelist.remove(user_id)
            
            # Update database
            await db.chats.update_one(
                {"_id": chat_id},
                {"$set": {"captcha_whitelist": whitelist}}
            )
            
            # Log the action
            await db.action_logs.insert_one({
                "chat_id": chat_id,
                "action_type": "captcha_unwhitelist",
                "performed_by": str(message.from_user.id),
                "target_user": user_id,
                "timestamp": now_utc()
            })
            
            await message.reply_text(
                f"✅ {target_user.mention_html()} has been removed from captcha whitelist.\n\n"
                "This user will now be required to complete captcha on future joins.",
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.error(f"Error in whitelist command: {e}")
        await message.reply_text(
            f"❌ Error updating whitelist: {str(e)}"
        )