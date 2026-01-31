"""
Federation Admins command - Show federation admins
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "fedadmins",
    "aliases": ["fadmins"],
    "description": "List federation admins",
    "usage": "/fedadmins [federation_id]",
    "category": "federation"
}


@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show federation admins"""
    chat_id = update.effective_chat.id
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    fed_id = None
    
    # If fed ID provided
    if context.args:
        fed_id = context.args[0]
    # Otherwise, try current chat
    else:
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        if chat_doc:
            fed_id = chat_doc.get('fed_id')
    
    if not fed_id:
        await update.message.reply_text(
            "❌ No federation specified and this chat is not in a federation.\n"
            "Usage: /fedadmins <federation_id>"
        )
        return
    
    # Get federation
    federation = await db.federations.find_one({"_id": fed_id})
    
    if not federation:
        await update.message.reply_text(f"❌ Federation not found: {fed_id}")
        return
    
    # Build admin list
    fed_name = federation['name']
    owner_id = federation['owner_id']
    owner_name = federation.get('owner_name', 'Unknown')
    admins = federation.get('admins', [])
    
    message = f"👥 <b>Federation Admins</b>\n\n"
    message += f"<b>Federation:</b> {fed_name}\n"
    message += f"<b>ID:</b> <code>{fed_id}</code>\n\n"
    message += f"<b>👑 Owner:</b>\n"
    message += f"• {owner_name} (<code>{owner_id}</code>)\n\n"
    
    if admins:
        message += f"<b>🛡️ Admins ({len(admins)}):</b>\n"
        for admin_id in admins:
            message += f"• <code>{admin_id}</code>\n"
    else:
        message += "<i>No admins appointed</i>"
    
    await update.message.reply_html(message)

