"""
Broadcast message to all chats or users
"""
import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import owner_only, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "broadcast",
    "aliases": ["announce"],
    "description": "Broadcast a message to all chats/users",
    "usage": "/broadcast <chats|users|all> <message>\n"
             "Reply to a message with /broadcast <target>",
    "category": "owner",
    "scope": ["private"]
}


@log_command
@owner_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Broadcast message to all chats or users
    """
    db = context.application.bot_data.get('database')
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    if not context.args:
        await update.message.reply_html(
            "📢 <b>Broadcast Command</b>\n\n"
            "<b>Usage:</b>\n"
            "• /broadcast chats <message>\n"
            "• /broadcast users <message>\n"
            "• /broadcast all <message>\n\n"
            "Or reply to a message with:\n"
            "• /broadcast chats\n"
            "• /broadcast users\n"
            "• /broadcast all"
        )
        return
    
    target = context.args[0].lower()
    if target not in ['chats', 'users', 'all']:
        await update.message.reply_text("❌ Invalid target. Use: chats, users, or all")
        return
    
    # Get message to broadcast
    if update.message.reply_to_message:
        broadcast_msg = update.message.reply_to_message
        message_text = broadcast_msg.text or broadcast_msg.caption
    elif len(context.args) > 1:
        message_text = " ".join(context.args[1:])
        broadcast_msg = None
    else:
        await update.message.reply_text("❌ Please provide a message or reply to one")
        return
    
    # Confirm broadcast
    import html
    preview = html.escape(message_text[:100] if message_text else "")
    await update.message.reply_html(
        f"📢 <b>Starting broadcast to {target}...</b>\n\n"
        f"Message: {preview}..."
    )
    
    success_count = 0
    fail_count = 0
    
    try:
        if target in ['chats', 'all']:
            # Broadcast to chats
            cursor = db.chats.find({})
            async for chat_doc in cursor:
                chat_id = int(chat_doc['_id'])
                try:
                    if broadcast_msg:
                        await broadcast_msg.copy(chat_id)
                    else:
                        await context.bot.send_message(chat_id, message_text)
                    success_count += 1
                    await asyncio.sleep(0.05)  # Rate limiting
                except Exception as e:
                    logger.debug(f"Failed to broadcast to chat {chat_id}: {e}")
                    fail_count += 1
        
        if target in ['users', 'all']:
            # Broadcast to users (private chats only)
            cursor = db.users.find({})
            async for user_doc in cursor:
                user_id = int(user_doc['_id'])
                try:
                    if broadcast_msg:
                        await broadcast_msg.copy(user_id)
                    else:
                        await context.bot.send_message(user_id, message_text)
                    success_count += 1
                    await asyncio.sleep(0.05)  # Rate limiting
                except Exception as e:
                    logger.debug(f"Failed to broadcast to user {user_id}: {e}")
                    fail_count += 1
        
        await update.message.reply_html(
            f"✅ <b>Broadcast Complete!</b>\n\n"
            f"✓ Successful: <code>{success_count}</code>\n"
            f"✗ Failed: <code>{fail_count}</code>"
        )
        
    except Exception as e:
        logger.error(f"Error during broadcast: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

