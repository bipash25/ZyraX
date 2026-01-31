"""
Reports toggle command
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from telegram.constants import ChatType
from datetime import datetime, timezone

from core.decorators import group_only, require_admin, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "reports",
    "aliases": ["report_toggle"],
    "description": "Toggle user reports in chat",
    "usage": "/reports <on/off> - Enable/disable user reports",
    "category": "reports"
}


@log_command
@group_only
@require_admin()
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /reports command
    
    Toggles whether users can report messages/users to admins
    """
    chat_id = update.effective_chat.id
    db = context.application.bot_data.get('database')
    
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    # Check arguments
    if not context.args:
        # Show current status
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        current = chat_doc.get('reports_enabled', True) if chat_doc else True
        
        await update.message.reply_html(
            f"📢 <b>Reports:</b> {'Enabled' if current else 'Disabled'}\n\n"
            f"<b>Usage:</b> /reports &lt;on/off&gt;"
        )
        return
    
    # Parse argument
    arg = context.args[0].lower()
    
    if arg in ['on', 'yes', 'true', '1', 'enable']:
        enabled = True
    elif arg in ['off', 'no', 'false', '0', 'disable']:
        enabled = False
    else:
        await update.message.reply_text(
            "❌ Invalid argument. Use: /reports <on/off>"
        )
        return
    
    # Update database
    await db.chats.update_one(
        {"_id": str(chat_id)},
        {
            "$set": {
                "reports_enabled": enabled,
                "updated_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    
    status = "enabled" if enabled else "disabled"
    message = f"✅ User reports {status}.\n\n"
    
    if enabled:
        message += "Users can now report messages using:\n"
        message += "• /report (reply to message)\n"
        message += "• @admin (mention in message)"
    else:
        message += "User reports are now disabled."
    
    await update.message.reply_text(message)
    
    logger.info(f"Reports {status} in chat {chat_id}")


async def handle_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /report command when user replies to a message
    """
    message = update.message
    chat = update.effective_chat
    reporter = update.effective_user
    
    # Only in groups
    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return
    
    # Must be a reply
    if not message.reply_to_message:
        await message.reply_text(
            "ℹ️ Reply to a message with /report to report it to admins."
        )
        return
    
    chat_id = chat.id
    reported_message = message.reply_to_message
    reported_user = reported_message.from_user
    
    # Check if reports enabled
    db = context.application.bot_data.get('database')
    if db:
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        if chat_doc and not chat_doc.get('reports_enabled', True):
            return  # Reports disabled, silently ignore
    
    # Don't allow reporting admins
    try:
        member = await chat.get_member(reported_user.id)
        if member.status in ['administrator', 'creator']:
            await message.reply_text("❌ You cannot report administrators.")
            return
    except Exception:
        pass
    
    # Get all admins
    try:
        admins = await chat.get_administrators()
        admin_mentions = []
        
        for admin in admins:
            if not admin.user.is_bot:  # Don't mention bots
                admin_mentions.append(admin.user.mention_html())
        
        # Build report message
        report_text = (
            f"📢 <b>Report from {reporter.mention_html()}</b>\n\n"
            f"<b>Reported user:</b> {reported_user.mention_html()}\n"
            f"<b>Message:</b> <a href='{reported_message.link}'>Jump to message</a>\n\n"
        )
        
        if len(admin_mentions) > 0:
            report_text += f"<b>Admins:</b> {', '.join(admin_mentions[:5])}"  # Limit to first 5
        
        # Send report
        report_msg = await context.bot.send_message(
            chat_id,
            report_text,
            parse_mode='HTML',
            reply_to_message_id=reported_message.message_id
        )
        
        # Delete the /report command message
        try:
            await message.delete()
        except Exception:
            pass
        
        # Auto-delete report after 5 minutes
        import asyncio
        asyncio.create_task(delete_after_delay(report_msg, 300))
        
        # Log the report
        if db:
            await db.action_logs.insert_one({
                "chat_id": str(chat_id),
                "action_type": "user_report",
                "performed_by": str(reporter.id),
                "target_user": str(reported_user.id),
                "metadata": {
                    "message_id": reported_message.message_id,
                    "reporter_username": reporter.username,
                    "reported_username": reported_user.username
                },
                "timestamp": datetime.now(timezone.utc)
            })
        
        logger.info(
            f"User {reporter.id} reported user {reported_user.id} in chat {chat_id}"
        )
        
    except Exception as e:
        logger.error(f"Error handling report: {e}")
        await message.reply_text("❌ Error sending report.")


async def handle_admin_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle @admin mentions in messages
    """
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    
    # Only in groups
    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return
    
    # Check if message contains @admin
    if not message.text or '@admin' not in message.text.lower():
        return
    
    chat_id = chat.id
    
    # Check if reports enabled
    db = context.application.bot_data.get('database')
    if db:
        chat_doc = await db.chats.find_one({"_id": str(chat_id)})
        if chat_doc and not chat_doc.get('reports_enabled', True):
            return  # Reports disabled
    
    # Get all admins
    try:
        admins = await chat.get_administrators()
        admin_mentions = []
        
        for admin in admins:
            if not admin.user.is_bot:
                admin_mentions.append(admin.user.mention_html())
        
        # Send notification
        if len(admin_mentions) > 0:
            report_text = (
                f"📢 <b>Admin attention requested by {user.mention_html()}</b>\n\n"
                f"<b>Admins:</b> {', '.join(admin_mentions[:5])}"
            )
            
            report_msg = await message.reply_html(report_text)
            
            # Auto-delete after 2 minutes
            import asyncio
            asyncio.create_task(delete_after_delay(report_msg, 120))
            
    except Exception as e:
        logger.error(f"Error handling @admin mention: {e}")


async def delete_after_delay(message, seconds: int):
    """Helper to delete a message after a delay"""
    import asyncio
    try:
        await asyncio.sleep(seconds)
        await message.delete()
    except Exception:
        pass


def get_report_handlers():
    """Get all report-related handlers"""
    import re
    # Create case-insensitive regex pattern for @admin mention
    admin_pattern = re.compile(r'@admin', re.IGNORECASE)
    
    return [
        MessageHandler(filters.COMMAND & filters.Regex(r'^/report'), handle_report_command),
        MessageHandler(filters.TEXT & filters.Regex(admin_pattern), handle_admin_mention),
    ]

