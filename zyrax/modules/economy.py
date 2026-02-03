"""
Economy Module

User wallet, earnings, transfers, and leaderboard commands.
"""

import random
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.database.mongo import db
from zyrax.utils.ratelimit import rate_limit
from zyrax.utils.users import extract_user
from zyrax.utils.errors import error_handler
from zyrax.utils.validators import InputValidator
from zyrax.constants import Rewards, Limits, WORK_JOBS, CURRENCY_NAME, CURRENCY_SYMBOL


__mod_name__ = "Economy"
__help__ = """
/balance - Check your wallet balance
/work - Work to earn coins (cooldown: 5m)
/daily - Claim your daily reward
/pay <user> <amount> - Transfer coins to another user
/rich - View the richest users
"""


@Client.on_message(filters.command(["balance", "bal", "wallet"]))
@rate_limit(max_attempts=10, window=60)
@error_handler
async def balance_command(client: Client, message: Message):
    """Check wallet balance."""
    user = await extract_user(client, message)
    target_id = user.id if user else message.from_user.id
    name = user.first_name if user else message.from_user.first_name
    
    data = await db.get_user_data(target_id)
    balance = data.get("balance", 0) if data else 0
    
    await message.reply_text(
        f"{CURRENCY_SYMBOL} **{name}'s Balance:** `{balance:,}` {CURRENCY_NAME}"
    )


@Client.on_message(filters.command("daily"))
@rate_limit(max_attempts=3, window=60)
@error_handler
async def daily_reward(client: Client, message: Message):
    """Claim daily reward."""
    user_id = message.from_user.id
    today = time.strftime("%Y-%m-%d")
    cache_key = f"daily:{user_id}:{today}"
    
    if await db.cache.get(cache_key):
        return await message.reply_text(
            "You have already claimed your daily reward today!\n"
            "Come back tomorrow!"
        )
    
    reward = random.randint(Rewards.DAILY_MIN, Rewards.DAILY_MAX)
    await db.add_balance(user_id, reward)
    
    # Set cache until end of day (24 hours)
    await db.cache.set(cache_key, 1, ttl=86400)
    
    # Get new balance
    data = await db.get_user_data(user_id)
    new_balance = data.get("balance", 0) if data else 0
    
    await message.reply_text(
        f"**Daily Reward Claimed!**\n\n"
        f"{CURRENCY_SYMBOL} You received `{reward:,}` {CURRENCY_NAME}!\n"
        f"New balance: `{new_balance:,}` {CURRENCY_NAME}"
    )


@Client.on_message(filters.command("work"))
@rate_limit(max_attempts=1, window=Rewards.WORK_COOLDOWN)
@error_handler
async def work_command(client: Client, message: Message):
    """Work to earn coins."""
    user_id = message.from_user.id
    earnings = random.randint(Rewards.WORK_MIN, Rewards.WORK_MAX)
    
    await db.add_balance(user_id, earnings)
    
    job = random.choice(WORK_JOBS)
    
    await message.reply_text(
        f"You worked as a **{job}** and earned **{earnings:,} {CURRENCY_NAME}**!"
    )


@Client.on_message(filters.command("pay"))
@rate_limit(max_attempts=5, window=60)
@error_handler
async def pay_command(client: Client, message: Message):
    """Transfer coins to another user."""
    # Args: /pay amount (reply) OR /pay user amount
    if len(message.command) < 2:
        return await message.reply_text(
            "Usage: /pay <amount> (reply) OR /pay <user> <amount>"
        )
    
    sender_id = message.from_user.id
    recipient = None
    amount_str = None
    
    if message.reply_to_message:
        recipient = message.reply_to_message.from_user
        amount_str = message.command[1]
    elif len(message.command) > 2:
        recipient = await extract_user(client, message)  # Uses arg 1
        amount_str = message.command[2]
    else:
        return await message.reply_text(
            "Usage: /pay <amount> (reply) OR /pay <user> <amount>"
        )
    
    if not recipient:
        return await message.reply_text("Recipient not found.")
    
    if recipient.is_bot:
        return await message.reply_text("You can't pay bots.")
    
    if sender_id == recipient.id:
        return await message.reply_text("You can't pay yourself.")
    
    # Validate amount
    is_valid, amount, error = InputValidator.validate_amount(
        amount_str,
        min_amount=1,
        max_amount=Limits.MAX_TRANSFER_AMOUNT
    )
    
    if not is_valid:
        return await message.reply_text(error)
    
    # Check sender balance
    sender_data = await db.get_user_data(sender_id)
    sender_balance = sender_data.get("balance", 0) if sender_data else 0
    
    if sender_balance < amount:
        return await message.reply_text(
            f"{CURRENCY_SYMBOL} **Insufficient funds!**\n"
            f"You have `{sender_balance:,}` {CURRENCY_NAME}."
        )
    
    # Execute transfer
    await db.add_balance(sender_id, -amount)
    await db.add_balance(recipient.id, amount)
    
    # Get new balances
    new_sender_data = await db.get_user_data(sender_id)
    new_balance = new_sender_data.get("balance", 0) if new_sender_data else 0
    
    await message.reply_text(
        f"{CURRENCY_SYMBOL} **Transfer Successful!**\n\n"
        f"Paid `{amount:,}` {CURRENCY_NAME} to {recipient.mention}\n"
        f"Your new balance: `{new_balance:,}` {CURRENCY_NAME}"
    )


@Client.on_message(filters.command(["rich", "leaderboard", "top"]))
@rate_limit(max_attempts=5, window=60)
@error_handler
async def rich_list(client: Client, message: Message):
    """Display the richest users."""
    users = await db.get_top_users(limit=10, sort_by="balance")
    
    if not users:
        return await message.reply_text("No users found in the leaderboard yet!")
    
    lines = []
    medals = ["", "", ""]
    
    for i, user in enumerate(users, 1):
        name = user.get("username") or user.get("first_name") or f"User {user['user_id']}"
        balance = user.get("balance", 0)
        
        if i <= 3:
            prefix = medals[i - 1]
        else:
            prefix = f"{i}."
        
        lines.append(f"{prefix} **{name}** - `{balance:,}`")
    
    text = (
        f"**Richest Users** ({CURRENCY_NAME})\n\n"
        + "\n".join(lines)
    )
    
    await message.reply_text(text)
