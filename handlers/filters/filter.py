"""
Filter command - Create custom auto-reply triggers
"""
import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import group_only, require_admin, log_command
from utils.message_parser import extract_filter_content

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "filter",
    "description": "Create a custom filter that auto-replies to trigger words",
    "usage": "/filter <trigger> - Reply to a message to set it as the response\n\n"
             "<b>Features:</b>\n"
             "• Supports text, media, buttons\n"
             "• Use variables: {first}, {last}, {mention}, {username}\n"
             "• Add buttons: [Text](buttonurl://url)\n"
             "• Use :same for same row: [Text](buttonurl://url:same)\n\n"
             "<b>Examples:</b>\n"
             "• <code>/filter hello</code> - Reply with welcome message\n"
             "• <code>/filter rules</code> - Reply with rules text",
    "category": "filters",
    "scope": ["group", "supergroup"]
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /filter command
    
    Create a custom filter trigger that auto-replies with specified content.
    """
    chat_id = update.effective_chat.id
    
    # Check if trigger word provided
    if not context.args:
        await update.message.reply_html(
            "❌ <b>Please specify a trigger word</b>\n\n"
            "<b>Usage:</b> <code>/filter &lt;trigger&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "Reply to a message with <code>/filter hello</code>"
        )
        return
    
    # Get trigger word (lowercase for case-insensitive matching)
    trigger = ' '.join(context.args).lower().strip()
    
    # Must be a reply to set the response
    if not update.message.reply_to_message:
        await update.message.reply_html(
            "❌ <b>Reply to a message to set it as the filter response</b>\n\n"
            f"<b>Trigger:</b> <code>{trigger}</code>\n\n"
            "<b>How to use:</b>\n"
            "1. Type the message you want as response\n"
            "2. Reply to it with <code>/filter {trigger}</code>"
        )
        return
    
    reply_msg = update.message.reply_to_message
    
    # Extract content from reply
    content = extract_filter_content(reply_msg)
    
    # Validate content
    if not content['text'] and not content['file_id']:
        await update.message.reply_html(
            "❌ <b>Reply message must contain text or media</b>"
        )
        return
    
    # Save filter to database
    db = context.application.bot_data.get('database')
    if db is not None:
        # Check if filter already exists
        existing = await db.filters.find_one({
            "chat_id": str(chat_id),
            "trigger": trigger
        })
        
        filter_doc = {
            "chat_id": str(chat_id),
            "trigger": trigger,
            "response_text": content['text'],
            "file_id": content['file_id'],
            "file_type": content['file_type'],
            "created_by": str(update.effective_user.id),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        if existing:
            # Update existing filter
            await db.filters.update_one(
                {
                    "chat_id": str(chat_id),
                    "trigger": trigger
                },
                {"$set": filter_doc}
            )
            action = "updated"
        else:
            # Create new filter
            await db.filters.insert_one(filter_doc)
            action = "created"
        
        # Build response message
        response = f"✅ <b>Filter {action}</b>\n\n"
        response += f"<b>Trigger:</b> <code>{trigger}</code>\n"
        response += f"<b>Type:</b> {content['type']}\n"
        
        if content['text']:
            # Show preview (truncated)
            preview = content['text'][:100]
            if len(content['text']) > 100:
                preview += "..."
            response += f"\n<b>Preview:</b>\n{preview}"
        
        await update.message.reply_html(response)
        
        logger.info(
            f"Filter {action}: '{trigger}' in chat {chat_id} by user {update.effective_user.id}"
        )
    else:
        await update.message.reply_html(
            "❌ <b>Database connection error</b>"
        )