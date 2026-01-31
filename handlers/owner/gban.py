"""
Global ban - Ban user from all chats where bot is admin
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import owner_only, log_command
from utils.user_resolver import resolve_user, mention_user
from utils.time_parser import now_utc

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "gban",
    "aliases": ["globalban"],
    "description": "Globally ban a user from all chats",
    "usage": "/gban <reply|@username|ID> [reason]",
    "category": "owner",
    "scope": ["private", "group", "supergroup"]
}


@log_command
@owner_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Global ban a user across all chats
    """
    db = context.application.bot_data.get('database')
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Resolve target user
    target_user, resolve_method = await resolve_user(update, context)
    
    if not target_user:
        await update.message.reply_html(
            "❌ <b>Please specify a user to gban.</b>\n\n"
            "<b>Usage:</b>\n"
            "• Reply to user's message with /gban\n"
            "• /gban @username [reason]\n"
            "• /gban &lt;user_id&gt; [reason]"
        )
        return
    
    # Get reason
    args = context.args[1:] if resolve_method != "reply" else context.args
    reason = " ".join(args) if args else "No reason provided"
    
    # Check if already gbanned
    existing_gban = await db.users.find_one({
        "_id": str(target_user.id),
        "gbanned": True
    })
    
    if existing_gban:
        await update.message.reply_text("⚠️ This user is already globally banned")
        return
    
    # Add to gban list
    await db.users.update_one(
        {"_id": str(target_user.id)},
        {
            "$set": {
                "gbanned": True,
                "gban_reason": reason,
                "gbanned_at": now_utc(),
                "gbanned_by": str(update.effective_user.id)
            }
        },
        upsert=True
    )
    
    # Ban from all chats
    msg = await update.message.reply_text("⏳ Globally banning user from all chats...")
    
    banned_count = 0
    fail_count = 0
    
    try:
        cursor = db.chats.find({})
        async for chat_doc in cursor:
            chat_id = int(chat_doc['_id'])
            try:
                # Check if bot is admin
                bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
                if bot_member.status in ['administrator', 'creator']:
                    if bot_member.can_restrict_members:
                        await context.bot.ban_chat_member(chat_id, target_user.id)
                        banned_count += 1
            except Exception as e:
                logger.debug(f"Failed to ban user {target_user.id} from chat {chat_id}: {e}")
                fail_count += 1
        
        # Log action
        await db.action_logs.insert_one({
            "action_type": "global_ban",
            "performed_by": str(update.effective_user.id),
            "target_user": str(target_user.id),
            "reason": reason,
            "chats_affected": banned_count,
            "timestamp": now_utc()
        })
        
        target_mention = mention_user(target_user, use_html=True)
        await msg.edit_text(
            f"🔨 <b>Global Ban Complete</b>\n\n"
            f"User: {target_mention}\n"
            f"Reason: {reason}\n\n"
            f"✅ Banned from <code>{banned_count}</code> chats\n"
            f"❌ Failed in <code>{fail_count}</code> chats",
            parse_mode='HTML'
        )
        
        logger.info(f"Global ban: User {target_user.id} banned from {banned_count} chats by owner")
        
    except Exception as e:
        logger.error(f"Error during global ban: {e}")
        await msg.edit_text(f"❌ Error: {str(e)}")

