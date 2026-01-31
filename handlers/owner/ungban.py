"""
Remove global ban from user
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import owner_only, log_command
from utils.user_resolver import resolve_user, mention_user
from utils.time_parser import now_utc

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "ungban",
    "aliases": ["unglobalban"],
    "description": "Remove global ban from a user",
    "usage": "/ungban <reply|@username|ID>",
    "category": "owner",
    "scope": ["private", "group", "supergroup"]
}


@log_command
@owner_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Remove global ban from a user
    """
    db = context.application.bot_data.get('database')
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Resolve target user
    target_user, resolve_method = await resolve_user(update, context)
    
    if not target_user:
        await update.message.reply_html(
            "❌ <b>Please specify a user to ungban.</b>\n\n"
            "<b>Usage:</b>\n"
            "• /ungban @username\n"
            "• /ungban &lt;user_id&gt;"
        )
        return
    
    # Check if gbanned
    user_doc = await db.users.find_one({
        "_id": str(target_user.id),
        "gbanned": True
    })
    
    if not user_doc:
        await update.message.reply_text("⚠️ This user is not globally banned")
        return
    
    # Remove gban
    await db.users.update_one(
        {"_id": str(target_user.id)},
        {
            "$set": {
                "gbanned": False
            },
            "$unset": {
                "gban_reason": "",
                "gbanned_at": "",
                "gbanned_by": ""
            }
        }
    )
    
    # Log action
    await db.action_logs.insert_one({
        "action_type": "global_unban",
        "performed_by": str(update.effective_user.id),
        "target_user": str(target_user.id),
        "timestamp": now_utc()
    })
    
    target_mention = mention_user(target_user, use_html=True)
    await update.message.reply_html(
        f"✅ <b>Global Ban Removed</b>\n\n"
        f"User: {target_mention}\n\n"
        f"Note: User may still be banned in individual chats.\n"
        f"They will need to be manually unbanned or rejoin."
    )
    
    logger.info(f"Global unban: User {target_user.id} unbanned by owner")

