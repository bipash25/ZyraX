"""
My Federations command - Show user's federations
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "myfeds",
    "aliases": ["myfederations"],
    "description": "Show federations you own or admin",
    "usage": "/myfeds",
    "category": "federation"
}


@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's federations"""
    user_id = update.effective_user.id
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Find federations where user is owner or admin
    owned_feds = await db.federations.find({"owner_id": str(user_id)}).to_list(length=None)
    admin_feds = await db.federations.find({"admins": str(user_id)}).to_list(length=None)
    
    if not owned_feds and not admin_feds:
        await update.message.reply_text(
            "❌ You don't own or admin any federations.\n\n"
            "Create one with /newfed <name>"
        )
        return
    
    message = "📋 <b>Your Federations</b>\n\n"
    
    if owned_feds:
        message += "<b>👑 Owned:</b>\n"
        for fed in owned_feds:
            fed_id = fed['_id']
            fed_name = fed['name']
            chats = len(fed.get('chats', []))
            bans = len(fed.get('banned_users', []))
            message += f"• <b>{fed_name}</b>\n"
            message += f"  ID: <code>{fed_id}</code>\n"
            message += f"  Chats: {chats} | Bans: {bans}\n"
        message += "\n"
    
    if admin_feds:
        message += "<b>🛡️ Admin in:</b>\n"
        for fed in admin_feds:
            fed_id = fed['_id']
            fed_name = fed['name']
            owner_name = fed.get('owner_name', 'Unknown')
            message += f"• <b>{fed_name}</b>\n"
            message += f"  ID: <code>{fed_id}</code>\n"
            message += f"  Owner: {owner_name}\n"
    
    await update.message.reply_html(message)

