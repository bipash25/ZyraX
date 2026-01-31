"""
Chat Federation command - Show chat's federation
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "chatfed",
    "aliases": ["thisfed"],
    "description": "Show this chat's federation",
    "usage": "/chatfed",
    "category": "federation"
}


@log_command
@group_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show chat's federation"""
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Get chat's federation
    chat_doc = await db.chats.find_one({"_id": str(chat_id)})
    
    if not chat_doc or not chat_doc.get('fed_id'):
        await update.message.reply_text(
            "❌ This chat is not connected to any federation.\n\n"
            "Admins can connect with: /joinfed <federation_id>"
        )
        return
    
    fed_id = chat_doc['fed_id']
    
    # Get federation info
    federation = await db.federations.find_one({"_id": fed_id})
    
    if not federation:
        await update.message.reply_text(
            f"❌ Federation data not found: {fed_id}\n"
            "The federation may have been deleted."
        )
        return
    
    # Build info message
    fed_name = federation['name']
    owner_id = federation['owner_id']
    owner_name = federation.get('owner_name', 'Unknown')
    admins = len(federation.get('admins', []))
    chats = len(federation.get('chats', []))
    banned_users = len(federation.get('banned_users', []))
    
    message = f"🔗 <b>Federation Information</b>\n\n"
    message += f"<b>Chat:</b> {chat_title}\n"
    message += f"<b>Federation:</b> {fed_name}\n"
    message += f"<b>ID:</b> <code>{fed_id}</code>\n"
    message += f"<b>Owner:</b> {owner_name} (<code>{owner_id}</code>)\n\n"
    message += f"<b>Statistics:</b>\n"
    message += f"• Admins: {admins}\n"
    message += f"• Connected Chats: {chats}\n"
    message += f"• Banned Users: {banned_users}\n\n"
    message += f"Use <code>/fedinfo {fed_id}</code> for more details."
    
    await update.message.reply_html(message)

