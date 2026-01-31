"""
List all chats the bot is in
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import owner_only, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "chatlist",
    "aliases": ["chats", "listchats"],
    "description": "List all chats bot is in",
    "usage": "/chatlist",
    "category": "owner",
    "scope": ["private"]
}


@log_command
@owner_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    List all chats bot is in
    """
    db = context.application.bot_data.get('database')
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    msg = await update.message.reply_text("⏳ Fetching chat list...")
    
    try:
        # Get all chats
        cursor = db.chats.find({})
        chats = await cursor.to_list(length=None)
        
        if not chats:
            await msg.edit_text("No chats found in database")
            return
        
        # Categorize chats
        groups = []
        supergroups = []
        
        for chat_doc in chats:
            chat_id = chat_doc['_id']
            title = chat_doc.get('title', 'Unknown')
            
            try:
                # Try to get fresh chat info
                chat = await context.bot.get_chat(int(chat_id))
                title = chat.title or title
                
                if chat.type == 'group':
                    groups.append((chat_id, title))
                elif chat.type == 'supergroup':
                    supergroups.append((chat_id, title))
                    
            except Exception as e:
                logger.debug(f"Could not get info for chat {chat_id}: {e}")
                # Use cached data
                if chat_id.startswith("-100"):
                    supergroups.append((chat_id, title))
                else:
                    groups.append((chat_id, title))
        
        # Build response
        response = f"💬 <b>Chat List ({len(chats)} total)</b>\n\n"
        
        if supergroups:
            response += f"<b>Supergroups ({len(supergroups)}):</b>\n"
            for chat_id, title in supergroups[:30]:
                response += f"• {title}\n  <code>{chat_id}</code>\n"
            if len(supergroups) > 30:
                response += f"\n<i>...and {len(supergroups) - 30} more</i>\n"
        
        if groups:
            response += f"\n<b>Groups ({len(groups)}):</b>\n"
            for chat_id, title in groups[:20]:
                response += f"• {title}\n  <code>{chat_id}</code>\n"
            if len(groups) > 20:
                response += f"\n<i>...and {len(groups) - 20} more</i>\n"
        
        await msg.edit_text(response, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error fetching chat list: {e}")
        await msg.edit_text(f"❌ Error: {str(e)}")

