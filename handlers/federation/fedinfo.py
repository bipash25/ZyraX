"""
Federation Info command - Show federation details
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "fedinfo",
    "aliases": ["federation_info"],
    "description": "Show federation information",
    "usage": "/fedinfo [federation_id]",
    "category": "federation"
}


@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show federation information"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    fed_id = None
    
    # If fed ID provided as argument
    if context.args:
        fed_id = context.args[0]
    # Otherwise, try to get from current chat
    else:
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        if chat_doc:
            fed_id = chat_doc.get('fed_id')
    
    if not fed_id:
        await update.message.reply_text(
            "❌ No federation specified and this chat is not in a federation.\n"
            "Usage: /fedinfo <federation_id>"
        )
        return
    
    # Get federation
    federation = await db.federations.find_one({"_id": fed_id})
    
    if not federation:
        await update.message.reply_text(f"❌ Federation not found: {fed_id}")
        return
    
    # Build info message
    fed_name = federation['name']
    owner_id = federation['owner_id']
    owner_name = federation.get('owner_name', 'Unknown')
    admins = federation.get('admins', [])
    chats = federation.get('chats', [])
    banned_users = federation.get('banned_users', [])
    subscribed_feds = federation.get('subscribed_feds', [])
    created_at = federation.get('created_at')
    
    message = f"ℹ️ <b>Federation Information</b>\n\n"
    message += f"<b>Name:</b> {fed_name}\n"
    message += f"<b>ID:</b> <code>{fed_id}</code>\n"
    message += f"<b>Owner:</b> {owner_name} (<code>{owner_id}</code>)\n"
    message += f"<b>Admins:</b> {len(admins)}\n"
    message += f"<b>Connected Chats:</b> {len(chats)}\n"
    message += f"<b>Banned Users:</b> {len(banned_users)}\n"
    
    if subscribed_feds:
        message += f"<b>Subscribed Federations:</b> {len(subscribed_feds)}\n"
    
    if created_at:
        message += f"\n<b>Created:</b> {created_at.strftime('%Y-%m-%d')}"
    
    await update.message.reply_html(message)

