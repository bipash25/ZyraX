from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.database.mongo import db
import time
import asyncio

__mod_name__ = "Levels"
__help__ = """
/rank - View your current level and XP
/top - View the leaderboard
"""

# Simple in-memory cooldown to prevent spam-farming
cooldowns = {}

def get_level_from_xp(xp):
    # Reverse of: 5 * (level^2) + 50 * level + 100 roughly
    # Simplified logic: XP increases complexity
    # Level 1 = 0-100 XP
    # Level 2 = 100+
    level = 1
    while True:
        req = 5 * (level ** 2) + 50 * level + 100
        if xp < req:
            return level
        level += 1

def get_xp_for_level(level):
    return 5 * (level ** 2) + 50 * level + 100

@Client.on_message(filters.group & ~filters.bot, group=1)
async def xp_handler(client: Client, message: Message):
    if not message.from_user:
        return
        
    user_id = message.from_user.id
    current_time = time.time()
    
    # 60 second cooldown per message XP
    if user_id in cooldowns and current_time - cooldowns[user_id] < 60:
        return
        
    cooldowns[user_id] = current_time
    
    # Give random XP between 5 and 15
    import random
    xp_gain = random.randint(5, 15)
    
    # Register/Update user
    await db.register_user(user_id, message.from_user.username or message.from_user.first_name)
    await db.add_xp(user_id, xp_gain)
    
    # Check level up
    user_data = await db.get_user_data(user_id)
    if not user_data:
        return
        
    current_xp = user_data.get("xp", 0)
    current_level = user_data.get("level", 1)
    
    # Calculate new level
    # We should iterate or verify logic. 
    # Optimization: Just check if current_xp >= requirement for NEXT level
    req_xp = get_xp_for_level(current_level)
    
    if current_xp >= req_xp:
        new_level = current_level + 1
        await db.update_level(user_id, new_level)
        await message.reply_text(
            f"🎉 **Level Up!**\n{message.from_user.mention} has reached **Level {new_level}**!"
        )

@Client.on_message(filters.command("rank"))
async def rank_command(client: Client, message: Message):
    user = message.from_user
    if len(message.command) > 1:
        # TODO: Get other user logic
        pass
        
    u_data = await db.get_user_data(user.id)
    if not u_data:
        await message.reply_text("You have no XP yet.")
        return
        
    xp = u_data.get("xp", 0)
    lvl = u_data.get("level", 1)
    req = get_xp_for_level(lvl)
    
    await message.reply_text(
        f"📊 **Rank Info**\n"
        f"👤 **User:** {user.mention}\n"
        f"🌟 **Level:** {lvl}\n"
        f"💠 **XP:** {xp} / {req}"
    )

@Client.on_message(filters.command("top"))
async def leaderboard(client: Client, message: Message):
    top_users = await db.get_top_users(limit=10, sort_by="xp")
    text = "🏆 **Global XP Leaderboard**\n\n"
    
    for i, user in enumerate(top_users, 1):
        username = user.get("username", "Unknown")
        lvl = user.get("level", 1)
        xp = user.get("xp", 0)
        text += f"{i}. **{username}** - Lvl {lvl} ({xp} XP)\n"
        
    await message.reply_text(text)
