"""
SetXP command - Set user's XP (admin only)
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.decorators import require_admin, log_command
from utils.user_resolver import resolve_user
from middleware.xp_tracker import calculate_level

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "setxp",
    "aliases": [],
    "description": "Set a user's XP (admin only)",
    "usage": "/setxp <@user> <amount>",
    "category": "leveling"
}


@require_admin(permissions=["can_restrict_members"])
@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set user's XP"""
    message = update.message
    
    db = context.application.bot_data.get('database')
    if not db:
        await message.reply_text("❌ Database not available")
        return
    
    # Resolve user
    target_user, resolution_method = await resolve_user(update, context)
    
    if not target_user:
        await message.reply_html(
            "❌ <b>Please specify a user.</b>\n\n"
            "<b>Usage:</b> <code>/setxp @user amount</code>"
        )
        return
    
    # Determine argument offset based on resolution method
    # If resolved from reply or text_mention, amount is in args[0]
    # If resolved from username/ID, amount is in args[1]
    if resolution_method in ["reply", "text_mention"]:
        arg_offset = 0
    else:
        arg_offset = 1
    
    if len(context.args) <= arg_offset:
        await message.reply_html(
            "❌ <b>Please specify XP amount.</b>\n\n"
            "<b>Usage:</b> <code>/setxp @user amount</code>"
        )
        return
    
    try:
        amount = int(context.args[arg_offset])
    except (ValueError, IndexError):
        await message.reply_text("❌ Invalid amount! Please provide a number.")
        return
    
    if amount < 0:
        await message.reply_text("❌ XP cannot be negative!")
        return
    
    if amount > 10000000:
        await message.reply_text("❌ Maximum XP is 10,000,000!")
        return
    
    try:
        # Calculate new level
        new_level = calculate_level(amount)
        
        # Update user XP
        await db.users.update_one(
            {"_id": str(target_user.id)},
            {
                "$set": {
                    "username": target_user.username,
                    "first_name": target_user.first_name,
                    "xp": amount,
                    "level": new_level
                }
            },
            upsert=True
        )
        
        await message.reply_html(
            f"✅ <b>XP Set Successfully!</b>\n\n"
            f"<b>User:</b> {target_user.mention_html()}\n"
            f"<b>New XP:</b> {amount:,}\n"
            f"<b>New Level:</b> {new_level}"
        )
        
        logger.info(f"Admin {update.effective_user.id} set {target_user.id}'s XP to {amount}")
        
    except Exception as e:
        logger.error(f"Error in setxp command: {e}", exc_info=True)
        await message.reply_text("❌ Error setting XP")

