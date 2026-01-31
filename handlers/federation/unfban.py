"""
Federation Unban command - Unban user from federation
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import log_command
from utils.user_resolver import resolve_user, mention_user

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "unfban",
    "aliases": ["fedunban"],
    "description": "Unban a user from the federation",
    "usage": "/unfban <reply|@username|ID>",
    "category": "federation"
}


@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /unfban command
    
    Unbans a user from the federation
    """
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Get user's federation (as owner or admin)
    federation = await db.federations.find_one({
        "$or": [
            {"owner_id": str(user_id)},
            {"admins": str(user_id)}
        ]
    })
    
    if not federation:
        await update.message.reply_text(
            "❌ You don't have permission to use federation bans.\n"
            "You must be a federation owner or admin."
        )
        return
    
    fed_id = federation['_id']
    fed_name = federation['name']
    
    # Resolve target user
    target_user, _ = await resolve_user(update, context)
    
    if not target_user:
        await update.message.reply_html(
            "❌ <b>Please specify a user to unban.</b>\n\n"
            "<b>Usage:</b> /unfban &lt;reply|@username|ID&gt;"
        )
        return
    
    # Check if user is banned
    ban_exists = any(
        ban['user_id'] == str(target_user.id)
        for ban in federation.get('banned_users', [])
    )
    
    if not ban_exists:
        await update.message.reply_html(
            f"❌ {mention_user(target_user, use_html=True)} is not fbanned in this federation."
        )
        return
    
    # Remove from federation ban list
    await db.federations.update_one(
        {"_id": fed_id},
        {"$pull": {"banned_users": {"user_id": str(target_user.id)}}}
    )
    
    # Unban user from all chats in federation
    chat_ids = federation.get('chats', [])
    unbanned_count = 0
    
    for chat_id_str in chat_ids:
        try:
            chat_id = int(chat_id_str)
            await context.bot.unban_chat_member(chat_id, target_user.id)
            unbanned_count += 1
        except Exception as e:
            logger.debug(f"Failed to unban user {target_user.id} from chat {chat_id}: {e}")
    
    # Send success message
    target_mention = mention_user(target_user, use_html=True)
    message = (
        f"✅ <b>Federation Unban Applied</b>\n\n"
        f"<b>User:</b> {target_mention}\n"
        f"<b>User ID:</b> <code>{target_user.id}</code>\n"
        f"<b>Federation:</b> {fed_name}\n"
        f"<b>Unbanned from:</b> {unbanned_count} chat(s)"
    )
    
    await update.message.reply_html(message)
    
    # Notify in log channel if configured
    log_channel_id = federation['settings'].get('log_channel_id')
    if log_channel_id:
        try:
            log_message = (
                f"✅ <b>Federation Unban</b>\n\n"
                f"<b>User:</b> {target_mention} (<code>{target_user.id}</code>)\n"
                f"<b>Federation:</b> {fed_name}\n"
                f"<b>Unbanned by:</b> {user_name} (<code>{user_id}</code>)\n"
                f"<b>Chats affected:</b> {unbanned_count}"
            )
            await context.bot.send_message(log_channel_id, log_message, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Failed to send to fed log channel: {e}")
    
    logger.info(
        f"User {target_user.id} unfbanned from federation {fed_id} by {user_id}. "
        f"Unbanned from {unbanned_count} chats."
    )

