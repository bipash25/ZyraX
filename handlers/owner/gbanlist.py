"""
List all globally banned users
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import owner_only, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "gbanlist",
    "aliases": ["gbans", "globalbans"],
    "description": "List all globally banned users",
    "usage": "/gbanlist",
    "category": "owner",
    "scope": ["private"]
}


@log_command
@owner_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    List all globally banned users
    """
    db = context.application.bot_data.get('database')
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    msg = await update.message.reply_text("⏳ Fetching global ban list...")
    
    try:
        # Get all gbanned users
        cursor = db.users.find({"gbanned": True})
        gbanned_users = await cursor.to_list(length=None)
        
        if not gbanned_users:
            await msg.edit_text("✅ No users are currently globally banned")
            return
        
        # Build response
        response = f"🔨 <b>Global Ban List ({len(gbanned_users)} users)</b>\n\n"
        
        for i, user_doc in enumerate(gbanned_users[:50], 1):  # Limit to 50
            user_id = user_doc['_id']
            reason = user_doc.get('gban_reason', 'No reason')
            gbanned_at = user_doc.get('gbanned_at')
            
            response += f"{i}. User ID: <code>{user_id}</code>\n"
            response += f"   Reason: {reason}\n"
            if gbanned_at:
                response += f"   Date: {gbanned_at.strftime('%Y-%m-%d')}\n"
            response += "\n"
        
        if len(gbanned_users) > 50:
            response += f"\n<i>...and {len(gbanned_users) - 50} more</i>"
        
        await msg.edit_text(response, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error fetching gban list: {e}")
        await msg.edit_text(f"❌ Error: {str(e)}")

