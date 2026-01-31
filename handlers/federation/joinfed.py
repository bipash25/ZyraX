"""
Join Federation command - Add chat to federation
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timezone

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "joinfed",
    "aliases": ["connectfed"],
    "description": "Connect this chat to a federation",
    "usage": "/joinfed <federation_id>",
    "category": "federation"
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /joinfed command
    
    Adds the current chat to a federation
    """
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title
    admin_user = update.effective_user
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Check if federation ID provided
    if not context.args:
        await update.message.reply_html(
            "❌ <b>Please provide a Federation ID.</b>\n\n"
            "<b>Usage:</b> /joinfed &lt;federation_id&gt;\n\n"
            "<b>Example:</b>\n"
            "<code>/joinfed a1b2c3d4</code>\n\n"
            "Get the Federation ID from the federation owner."
        )
        return
    
    fed_id = context.args[0]
    
    # Check if federation exists
    federation = await db.federations.find_one({"_id": fed_id})
    
    if not federation:
        await update.message.reply_text(
            f"❌ Federation not found with ID: {fed_id}\n\n"
            "Please check the ID and try again."
        )
        return
    
    # Check if chat is already in a federation
    chat_doc = await db.chats.find_one({"_id": str(chat_id)})
    
    if chat_doc and chat_doc.get('fed_id'):
        current_fed = await db.federations.find_one({"_id": chat_doc['fed_id']})
        current_fed_name = current_fed['name'] if current_fed else "Unknown"
        
        await update.message.reply_html(
            f"❌ This chat is already connected to a federation:\n\n"
            f"<b>Federation:</b> {current_fed_name}\n"
            f"<b>ID:</b> <code>{chat_doc['fed_id']}</code>\n\n"
            f"Use <code>/leavefed</code> first to disconnect."
        )
        return
    
    # Add chat to federation's chat list
    await db.federations.update_one(
        {"_id": fed_id},
        {"$addToSet": {"chats": str(chat_id)}}
    )
    
    # Update chat document
    await db.chats.update_one(
        {"_id": str(chat_id)},
        {
            "$set": {
                "fed_id": fed_id,
                "updated_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    
    # Success message
    fed_name = federation['name']
    owner_id = federation['owner_id']
    
    await update.message.reply_html(
        f"✅ <b>Chat connected to federation!</b>\n\n"
        f"<b>Federation:</b> {fed_name}\n"
        f"<b>ID:</b> <code>{fed_id}</code>\n"
        f"<b>Owner ID:</b> <code>{owner_id}</code>\n\n"
        f"Federation bans will now be applied to this chat.\n"
        f"Use <code>/fedinfo</code> for more information."
    )
    
    # Log the connection
    await db.action_logs.insert_one({
        "chat_id": str(chat_id),
        "action_type": "fed_join",
        "performed_by": str(admin_user.id),
        "metadata": {
            "fed_id": fed_id,
            "fed_name": fed_name,
            "chat_title": chat_title
        },
        "timestamp": datetime.now(timezone.utc)
    })
    
    logger.info(f"Chat {chat_id} ({chat_title}) joined federation {fed_id}")

