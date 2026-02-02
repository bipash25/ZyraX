from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.database.mongo import db
from zyrax.utils.ratelimit import rate_limit
from zyrax.utils.users import extract_user
from zyrax.utils.errors import error_handler
import random
import time

__mod_name__ = "Economy"
__help__ = """
/balance - Check your wallet balance
/work - Work to earn coins (cooldown: 5m)
/daily - Claim your daily reward
/pay <user> <amount> - Transfer coins to another user
/rich - View the richest users
"""

CURRENCY = "ZyraCoins"

@Client.on_message(filters.command(["balance", "bal", "bf"]))
@error_handler
async def balance_command(client: Client, message: Message):
    user = await extract_user(client, message)
    target_id = user.id if user else message.from_user.id
    name = user.first_name if user else message.from_user.first_name
         
    data = await db.get_user_data(target_id)
    bal = data.get("balance", 0) if data else 0
    
    await message.reply_text(f"💰 **{name}'s Balance:** `{bal}` {CURRENCY}")

@Client.on_message(filters.command("daily"))
@error_handler
async def daily_reward(client: Client, message: Message):
    user_id = message.from_user.id
    today = time.strftime("%Y-%m-%d")
    cache_key = f"daily:{user_id}:{today}"
    
    if await db.cache.get(cache_key):
        await message.reply_text("⏳ You have already claimed your daily reward today!")
        return
        
    reward = random.randint(100, 500)
    await db.add_balance(user_id, reward)
    
    # Set cache for 24 hours (approx)
    await db.cache.set(cache_key, 1, ttl=86400)
    
    await message.reply_text(f"✅ **Daily Claimed!**\nYou received `{reward}` {CURRENCY}!")

@Client.on_message(filters.command("work"))
@rate_limit(max_attempts=1, window=300) # 5 min cooldown
@error_handler
async def work_command(client: Client, message: Message):
    earnings = random.randint(10, 100)
    await db.add_balance(message.from_user.id, earnings)
    
    jobs = ["barista", "programmer", "taxi driver", "chef", "stripper", "teacher", "hitman", "discord mod"]
    job = random.choice(jobs)
    
    await message.reply_text(f"🔨 You worked as a **{job}** and earned **{earnings} {CURRENCY}**!")

@Client.on_message(filters.command("pay"))
@error_handler
async def pay_command(client: Client, message: Message):
    # Args: /pay amount reply OR /pay user amount
    if len(message.command) < 2:
        return await message.reply_text("Usage: /pay <amount> (reply) OR /pay <user> <amount>")
        
    sender_id = message.from_user.id
    recipient = None
    amount = 0
    
    if message.reply_to_message:
        recipient = message.reply_to_message.from_user
        try:
            amount = int(message.command[1])
        except:
            return await message.reply_text("Invalid amount.")
    elif len(message.command) > 2:
        recipient = await extract_user(client, message) # Uses arg 1
        try:
            amount = int(message.command[2])
        except:
            return await message.reply_text("Invalid amount.")
    else:
        return await message.reply_text("Invalid usage.")
        
    if not recipient:
        return await message.reply_text("Recipient not found.")
        
    if recipient.is_bot:
        return await message.reply_text("You can't pay bots.")
        
    if sender_id == recipient.id:
        return await message.reply_text("You can't pay yourself.")
        
    if amount <= 0:
        return await message.reply_text("Amount must be positive.")
        
    # Check balance
    sender_data = await db.get_user_data(sender_id)
    sender_bal = sender_data.get("balance", 0) if sender_data else 0
    
    if sender_bal < amount:
        return await message.reply_text("💸 Insufficient funds!")
        
    # Transfer
    await db.add_balance(sender_id, -amount)
    await db.add_balance(recipient.id, amount)
    
    await message.reply_text(
        f"💸 **Transfer Successful!**\n"
        f"Paid `{amount}` {CURRENCY} to {recipient.mention}"
    )

@Client.on_message(filters.command("rich"))
@error_handler
async def rich_list(client: Client, message: Message):
    users = await db.get_top_users(limit=10, sort_by="balance")
    text = f"💎 **Richest Users ({CURRENCY})**\n\n"
    for i, u in enumerate(users, 1):
        name = u.get("username") or f"User {u['user_id']}"
        bal = u.get("balance", 0)
        text += f"{i}. **{name}** - `{bal}`\n"
        
    await message.reply_text(text)
