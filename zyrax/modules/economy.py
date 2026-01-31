from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.database.mongo import db
import time
import random

__mod_name__ = "Economy"
__help__ = """
/bf - Check your wallet balance
/daily - Claim your daily reward
/pay <user> <amount> - Transfer coins to another user
"""

@Client.on_message(filters.command(["bf", "balance"]))
async def balance_command(client: Client, message: Message):
    user_id = message.from_user.id
    target_id = user_id
    
    if len(message.command) > 1 and message.reply_to_message:
         target_id = message.reply_to_message.from_user.id
         
    data = await db.get_user_data(target_id)
    bal = data.get("balance", 0) if data else 0
    
    await message.reply_text(f"💰 **Balance:** `{bal}` ZyraCoins")

@Client.on_message(filters.command("daily") & filters.group)
async def daily_reward(client: Client, message: Message):
    user_id = message.from_user.id
    today = time.strftime("%Y-%m-%d")
    cache_key = f"daily:{user_id}:{today}"
    
    if await db.cache.get(cache_key):
        await message.reply_text("⏳ You have already claimed your daily reward today!")
        return
        
    reward = random.randint(100, 500)
    await db.add_balance(user_id, reward)
    
    # Set cache for 24 hours (approx, actually just until end of day is better but TTL is simple)
    # Using 86400 seconds for now to prevent multiple claims
    await db.cache.set(cache_key, 1, ttl=86400)
    
    await message.reply_text(f"✅ **Daily Claimed!**\nYou received `{reward}` ZyraCoins!")

@Client.on_message(filters.command("pay") & filters.group)
async def pay_command(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("Reply to a user to pay them!")
        return
        
    sender_id = message.from_user.id
    recipient_id = message.reply_to_message.from_user.id
    
    if sender_id == recipient_id:
        await message.reply_text("You can't pay yourself.")
        return
        
    if message.reply_to_message.from_user.is_bot:
        await message.reply_text("You can't pay bots.")
        return
        
    try:
        amount = int(message.command[1])
    except (IndexError, ValueError):
        await message.reply_text("Usage: /pay <amount>")
        return
        
    if amount <= 0:
        await message.reply_text("Amount must be positive.")
        return
        
    # Check balance
    sender_data = await db.get_user_data(sender_id)
    sender_bal = sender_data.get("balance", 0) if sender_data else 0
    
    if sender_bal < amount:
        await message.reply_text("💸 Insufficient funds!")
        return
        
    # Transfer
    await db.add_balance(sender_id, -amount)
    await db.add_balance(recipient_id, amount)
    
    await message.reply_text(
        f"💸 **Transfer Successful!**\n"
        f"Paid `{amount}` ZyraCoins to {message.reply_to_message.from_user.mention}"
    )
