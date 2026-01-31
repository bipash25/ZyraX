"""
Federation Ban command - Ban user across all federated chats
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timezone

from core.decorators import log_command
from utils.user_resolver import resolve_user, mention_user

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "fban",
    "aliases": ["fedban"],
    "description": "Ban a user across all chats in the federation",
    "usage": "/fban <reply|@username|ID> [reason]",
    "category": "federation"
}


@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /fban command
    
    Bans a user across all chats in the federation
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
            "❌ <b>Please specify a user to ban.</b>\n\n"
            "<b>Usage:</b> /fban &lt;reply|@username|ID&gt; [reason]"
        )
        return
    
    # Can't fban yourself
    if target_user.id == user_id:
        await update.message.reply_text("❌ You cannot fban yourself.")
        return
    
    # Can't fban the federation owner
    if str(target_user.id) == federation['owner_id']:
        await update.message.reply_text("❌ You cannot fban the federation owner.")
        return
    
    # Extract reason
    reason = None
    if update.message.reply_to_message:
        if context.args:
            reason = " ".join(context.args)
    else:
        if len(context.args) > 1:
            reason = " ".join(context.args[1:])
    
    # Check if reason is required
    if federation['settings'].get('require_reason', True) and not reason:
        await update.message.reply_text(
            "❌ This federation requires a reason for bans.\n"
            "Usage: /fban <user> <reason>"
        )
        return
    
    # Check if already banned
    existing_ban = next(
        (ban for ban in federation['banned_users'] if ban['user_id'] == str(target_user.id)),
        None
    )
    
    if existing_ban:
        await update.message.reply_html(
            f"❌ {mention_user(target_user, use_html=True)} is already fbanned.\n\n"
            f"<b>Reason:</b> {existing_ban.get('reason', 'No reason')}\n"
            f"<b>Banned by:</b> {existing_ban.get('banned_by_name', 'Unknown')}"
        )
        return
    
    # Add to federation ban list
    ban_entry = {
        "user_id": str(target_user.id),
        "username": target_user.username,
        "first_name": target_user.first_name,
        "reason": reason or "No reason provided",
        "banned_by": str(user_id),
        "banned_by_name": user_name,
        "banned_at": datetime.now(timezone.utc)
    }
    
    await db.federations.update_one(
        {"_id": fed_id},
        {"$push": {"banned_users": ban_entry}}
    )
    
    # Ban user from all chats in federation
    chat_ids = federation.get('chats', [])
    banned_count = 0
    failed_count = 0
    
    for chat_id_str in chat_ids:
        try:
            chat_id = int(chat_id_str)
            await context.bot.ban_chat_member(chat_id, target_user.id)
            banned_count += 1
        except Exception as e:
            logger.debug(f"Failed to ban user {target_user.id} from chat {chat_id}: {e}")
            failed_count += 1
    
    # Send success message
    target_mention = mention_user(target_user, use_html=True)
    message = (
        f"✅ <b>Federation Ban Applied</b>\n\n"
        f"<b>User:</b> {target_mention}\n"
        f"<b>User ID:</b> <code>{target_user.id}</code>\n"
        f"<b>Federation:</b> {fed_name}\n"
    )
    
    if reason:
        message += f"<b>Reason:</b> {reason}\n"
    
    message += f"\n<b>Banned from:</b> {banned_count} chat(s)"
    
    if failed_count > 0:
        message += f"\n<b>Failed:</b> {failed_count} chat(s)"
    
    await update.message.reply_html(message)
    
    # Notify in log channel if configured
    log_channel_id = federation['settings'].get('log_channel_id')
    if log_channel_id:
        try:
            log_message = (
                f"🚫 <b>Federation Ban</b>\n\n"
                f"<b>User:</b> {target_mention} (<code>{target_user.id}</code>)\n"
                f"<b>Federation:</b> {fed_name}\n"
                f"<b>Banned by:</b> {user_name} (<code>{user_id}</code>)\n"
                f"<b>Reason:</b> {reason or 'No reason'}\n"
                f"<b>Chats affected:</b> {banned_count}"
            )
            await context.bot.send_message(log_channel_id, log_message, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Failed to send to fed log channel: {e}")
    
    logger.info(
        f"User {target_user.id} fbanned from federation {fed_id} by {user_id}. "
        f"Banned from {banned_count} chats."
    )

