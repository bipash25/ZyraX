"""
Federation Promote command - Promote user to fed admin
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import log_command
from utils.user_resolver import resolve_user, mention_user

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "fedpromote",
    "aliases": ["fpromote"],
    "description": "Promote a user to federation admin",
    "usage": "/fedpromote <reply|@username|ID>",
    "category": "federation"
}


@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Promote user to federation admin - Only owner can do this"""
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
            "Only federation owners can promote admins."
        )
        return
    
    fed_id = federation['_id']
    fed_name = federation['name']
    
    # Resolve target user
    target_user, _ = await resolve_user(update, context)
    
    if not target_user:
        await update.message.reply_html(
            "❌ <b>Please specify a user to promote.</b>\n\n"
            "<b>Usage:</b> /fedpromote &lt;reply|@username|ID&gt;"
        )
        return
    
    # Can't promote yourself
    if target_user.id == user_id:
        await update.message.reply_text("❌ You are already the owner.")
        return
    
    # Check if already an admin
    if str(target_user.id) in federation.get('admins', []):
        await update.message.reply_html(
            f"❌ {mention_user(target_user, use_html=True)} is already a federation admin."
        )
        return
    
    # Promote to admin
    await db.federations.update_one(
        {"_id": fed_id},
        {"$addToSet": {"admins": str(target_user.id)}}
    )
    
    target_mention = mention_user(target_user, use_html=True)
    
    await update.message.reply_html(
        f"✅ <b>Federation Admin Promoted</b>\n\n"
        f"<b>User:</b> {target_mention}\n"
        f"<b>User ID:</b> <code>{target_user.id}</code>\n"
        f"<b>Federation:</b> {fed_name}\n\n"
        f"They can now use federation ban commands."
    )
    
    logger.info(f"User {target_user.id} promoted to fed admin in {fed_id} by {user_id}")

