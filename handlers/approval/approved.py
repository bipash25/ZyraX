"""
Approved command - List all approved users
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "approved",
    "aliases": [],
    "description": "List all approved users in chat",
    "usage": "/approved - Show whitelisted users",
    "category": "approval",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /approved command
    
    Show all approved users in the current chat.
    
    Args:
        update: Telegram update
        context: PTB context
    """
    chat_id = update.effective_chat.id
    
    # Get database
    db = context.application.bot_data.get('database')
    if db is None:
        await update.message.reply_html("❌ Database not available")
        return
    
    try:
        # Find all users with approval in this chat
        cursor = db.users.find({
            f"chat_data.{chat_id}.approved": True
        })
        
        approved_users = []
        async for user_doc in cursor:
            user_id = user_doc['_id']
            chat_data = user_doc.get('chat_data', {}).get(str(chat_id), {})
            
            # Try to get user info
            try:
                user = await context.bot.get_chat(int(user_id))
                name = user.full_name or user.username or f"User {user_id}"
                approved_users.append({
                    'id': user_id,
                    'name': name,
                    'username': user.username,
                    'approved_at': chat_data.get('approved_at')
                })
            except Exception:
                # User might have deleted account or blocked bot
                approved_users.append({
                    'id': user_id,
                    'name': f"User {user_id}",
                    'username': None,
                    'approved_at': chat_data.get('approved_at')
                })
        
        if not approved_users:
            await update.message.reply_html(
                "📋 <b>No approved users</b>\n\n"
                "No users are currently whitelisted in this chat."
            )
            return
        
        # Build message
        message = f"✅ <b>Approved Users ({len(approved_users)})</b>\n\n"
        
        for user in approved_users[:50]:  # Limit to 50 to avoid message length issues
            user_text = f"• <code>{user['id']}</code> - {user['name']}"
            if user['username']:
                user_text += f" (@{user['username']})"
            message += user_text + "\n"
        
        if len(approved_users) > 50:
            message += f"\n<i>...and {len(approved_users) - 50} more</i>"
        
        message += "\n\n💡 Use /unapprove to remove users from whitelist"
        
        await update.message.reply_html(message)
        
    except Exception as e:
        logger.error(f"Error listing approved users in chat {chat_id}: {e}")
        await update.message.reply_html(
            "❌ Failed to list approved users"
        )