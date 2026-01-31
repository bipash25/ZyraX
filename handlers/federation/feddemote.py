"""
Federation Demote command - Demote fed admin
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import log_command
from utils.user_resolver import resolve_user, mention_user

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "feddemote",
    "aliases": ["fdemote"],
    "description": "Demote a federation admin",
    "usage": "/feddemote <reply|@username|ID>",
    "category": "federation"
}


@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Demote federation admin - Only owner can do this"""
    user_id = update.effective_user.id
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Get user's federation (must be owner)
    federation = await db.federations.find_one({"owner_id": str(user_id)})
    
    if not federation:
        await update.message.reply_text(
            "❌ You don't own any federation.\n"
            "Only federation owners can demote admins."
        )
        return
    
    fed_id = federation['_id']
    fed_name = federation['name']
    
    # Resolve target user
    target_user, _ = await resolve_user(update, context)
    
    if not target_user:
        await update.message.reply_html(
            "❌ <b>Please specify a user to demote.</b>\n\n"
            "<b>Usage:</b> /feddemote &lt;reply|@username|ID&gt;"
        )
        return
    
    # Can't demote yourself (owner)
    if target_user.id == user_id:
        await update.message.reply_text("❌ You cannot demote yourself.")
        return
    
    # Check if user is an admin
    if str(target_user.id) not in federation.get('admins', []):
        await update.message.reply_html(
            f"❌ {mention_user(target_user, use_html=True)} is not a federation admin."
        )
        return
    
    # Demote from admin
    await db.federations.update_one(
        {"_id": fed_id},
        {"$pull": {"admins": str(target_user.id)}}
    )
    
    target_mention = mention_user(target_user, use_html=True)
    
    await update.message.reply_html(
        f"✅ <b>Federation Admin Demoted</b>\n\n"
        f"<b>User:</b> {target_mention}\n"
        f"<b>User ID:</b> <code>{target_user.id}</code>\n"
        f"<b>Federation:</b> {fed_name}\n\n"
        f"They can no longer use federation ban commands."
    )
    
    logger.info(f"User {target_user.id} demoted from fed admin in {fed_id} by {user_id}")

