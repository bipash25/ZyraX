"""
Transfer command - Send coins to another user
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from utils.user_resolver import resolve_user

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "transfer",
    "aliases": ["pay", "send", "give"],
    "description": "Transfer coins to another user",
    "usage": "/transfer <@user> <amount>",
    "category": "economy"
}


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Transfer coins to another user"""
    user = update.effective_user
    message = update.message
    
    db = context.application.bot_data.get('database')
    if not db:
        await message.reply_text("❌ Database not available")
        return
    
    # Resolve target user
    target_user, resolution_method = await resolve_user(update, context)
    
    if not target_user:
        await message.reply_html(
            "❌ <b>Please specify a user to transfer coins to.</b>\n\n"
            "<b>Usage:</b> <code>/transfer @user amount</code>"
        )
        return
    
    # Can't transfer to self
    if target_user.id == user.id:
        await message.reply_text("❌ You cannot transfer coins to yourself!")
        return
    
    # Can't transfer to bots
    if target_user.is_bot:
        await message.reply_text("❌ You cannot transfer coins to bots!")
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
            "❌ <b>Please specify an amount to transfer.</b>\n\n"
            "<b>Usage:</b> <code>/transfer @user amount</code>"
        )
        return
    
    try:
        amount = int(context.args[arg_offset])
    except (ValueError, IndexError):
        await message.reply_text("❌ Invalid amount! Please provide a number.")
        return
    
    if amount <= 0:
        await message.reply_text("❌ Amount must be greater than 0!")
        return
    
    if amount > 1000000:
        await message.reply_text("❌ Maximum transfer amount is 1,000,000 coins!")
        return
    
    try:
        # Get sender's balance
        sender_doc = await db.users.find_one({"_id": str(user.id)})
        
        sender_balance = sender_doc.get('currency', 0) if sender_doc else 0
        
        if sender_balance < amount:
            await message.reply_html(
                f"❌ <b>Insufficient balance!</b>\n\n"
                f"<b>Your balance:</b> {sender_balance:,} 🪙\n"
                f"<b>Transfer amount:</b> {amount:,} 🪙\n"
                f"<b>Missing:</b> {amount - sender_balance:,} 🪙"
            )
            return
        
        # Perform transfer
        # Deduct from sender
        await db.users.update_one(
            {"_id": str(user.id)},
            {"$inc": {"currency": -amount}},
            upsert=True
        )
        
        # Add to recipient
        await db.users.update_one(
            {"_id": str(target_user.id)},
            {
                "$inc": {"currency": amount},
                "$set": {
                    "username": target_user.username,
                    "first_name": target_user.first_name
                }
            },
            upsert=True
        )
        
        # Success message
        new_balance = sender_balance - amount
        
        await message.reply_html(
            f"✅ <b>Transfer Successful!</b>\n\n"
            f"<b>Sent to:</b> {target_user.mention_html()}\n"
            f"<b>Amount:</b> {amount:,} 🪙\n\n"
            f"<b>Your new balance:</b> {new_balance:,} 🪙"
        )
        
        logger.info(f"User {user.id} transferred {amount} coins to {target_user.id}")
        
    except Exception as e:
        logger.error(f"Error in transfer command: {e}", exc_info=True)
        await message.reply_text("❌ Error processing transfer")

