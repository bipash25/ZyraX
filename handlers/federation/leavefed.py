"""
Leave Federation command - Remove chat from federation
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timezone

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "leavefed",
    "aliases": ["disconnectfed"],
    "description": "Disconnect this chat from its federation",
    "usage": "/leavefed",
    "category": "federation"
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /leavefed command
    
    Removes the current chat from its federation
    """
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title
    admin_user = update.effective_user
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Check if chat is in a federation
    chat_doc = await db.chats.find_one({"_id": str(chat_id)})
    
    if not chat_doc or not chat_doc.get('fed_id'):
        await update.message.reply_text(
            "❌ This chat is not connected to any federation."
        )
        return
    
    fed_id = chat_doc['fed_id']
    
    # Get federation info
    federation = await db.federations.find_one({"_id": fed_id})
    fed_name = federation['name'] if federation else "Unknown"
    
    # Remove chat from federation's chat list
    await db.federations.update_one(
        {"_id": fed_id},
        {"$pull": {"chats": str(chat_id)}}
    )
    
    # Remove fed_id from chat document
    await db.chats.update_one(
        {"_id": str(chat_id)},
        {
            "$unset": {"fed_id": ""},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    
    await update.message.reply_html(
        f"✅ <b>Chat disconnected from federation.</b>\n\n"
        f"<b>Federation:</b> {fed_name}\n"
        f"<b>ID:</b> <code>{fed_id}</code>\n\n"
        f"Federation bans will no longer be applied to this chat."
    )
    
    # Log the disconnection
    await db.action_logs.insert_one({
        "chat_id": str(chat_id),
        "action_type": "fed_leave",
        "performed_by": str(admin_user.id),
        "metadata": {
            "fed_id": fed_id,
            "fed_name": fed_name,
            "chat_title": chat_title
        },
        "timestamp": datetime.now(timezone.utc)
    })
    
    logger.info(f"Chat {chat_id} ({chat_title}) left federation {fed_id}")

