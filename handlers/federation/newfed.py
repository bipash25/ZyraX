"""
Create Federation command
"""
import logging
import uuid
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timezone

from core.decorators import log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "newfed",
    "aliases": ["createfed"],
    "description": "Create a new federation",
    "usage": "/newfed <federation_name>",
    "category": "federation"
}


@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /newfed command
    
    Creates a new federation with the user as owner
    """
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Check if user provided federation name
    if not context.args:
        await update.message.reply_html(
            "❌ <b>Please provide a federation name.</b>\n\n"
            "<b>Usage:</b> /newfed &lt;name&gt;\n\n"
            "<b>Example:</b>\n"
            "<code>/newfed My Federation</code>"
        )
        return
    
    fed_name = " ".join(context.args)
    
    # Validate name length
    if len(fed_name) < 3:
        await update.message.reply_text("❌ Federation name must be at least 3 characters.")
        return
    
    if len(fed_name) > 50:
        await update.message.reply_text("❌ Federation name must be less than 50 characters.")
        return
    
    # Check if user already owns a federation
    existing = await db.federations.find_one({"owner_id": str(user_id)})
    
    if existing:
        await update.message.reply_html(
            f"❌ You already own a federation: <b>{existing['name']}</b>\n\n"
            f"Federation ID: <code>{existing['_id']}</code>\n\n"
            f"You can only own one federation at a time."
        )
        return
    
    # Generate unique federation ID
    fed_id = str(uuid.uuid4())[:8]
    
    # Check if ID already exists (very unlikely)
    while await db.federations.find_one({"_id": fed_id}):
        fed_id = str(uuid.uuid4())[:8]
    
    # Create federation
    federation = {
        "_id": fed_id,
        "name": fed_name,
        "owner_id": str(user_id),
        "owner_name": user_name,
        "admins": [],  # Fed admins (not owner)
        "chats": [],  # List of chat IDs in federation
        "banned_users": [],  # List of banned user dicts
        "subscribed_feds": [],  # Federations subscribed to
        "settings": {
            "notify_bans": True,
            "require_reason": True,
            "log_channel_id": None
        },
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.federations.insert_one(federation)
    
    # Success message
    await update.message.reply_html(
        f"✅ <b>Federation created successfully!</b>\n\n"
        f"<b>Name:</b> {fed_name}\n"
        f"<b>Federation ID:</b> <code>{fed_id}</code>\n"
        f"<b>Owner:</b> {user_name}\n\n"
        f"<b>Next steps:</b>\n"
        f"• Add this federation to your groups: <code>/joinfed {fed_id}</code>\n"
        f"• Promote admins: <code>/fedpromote @username</code>\n"
        f"• Ban users across all groups: <code>/fban @user reason</code>\n\n"
        f"<b>Important:</b> Save your Federation ID!"
    )
    
    logger.info(f"Federation '{fed_name}' created with ID {fed_id} by user {user_id}")

