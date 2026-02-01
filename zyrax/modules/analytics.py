from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.database.mongo import db
from zyrax.utils.decorators import require_admin
from zyrax.utils.errors import error_handler
import json
import io

__mod_name__ = "Analytics"
__help__ = """
**Analytics Commands:**
/stats - View chat statistics
/userstats [@user] - View user stats
/topactive - Top 10 most active users
/activitystats - Activity summary

**Export:**
/exportstats - Export analytics as JSON file
/exportlogs - Export audit logs as JSON file

**Admin:**
/gamestats - Game leaderboards
"""

@Client.on_message(filters.group, group=0)
async def analytics_tracker(client: Client, message: Message):
    if not message.from_user:
        return
        
    try:
        await db.track_activity(message.from_user.id, message.chat.id)
    except:
        pass


@Client.on_message(filters.command("stats") & filters.group)
@error_handler
async def chat_stats(client: Client, message: Message):
    """Show chat statistics"""
    chat_id = message.chat.id
    
    # Get chat data
    chats = await db.get_collection("chats")
    chat_data = await chats.find_one({"chat_id": chat_id})
    
    msg_count = chat_data.get("msg_count", 0) if chat_data else 0
    
    # Get member count
    try:
        chat_info = await client.get_chat(chat_id)
        members = chat_info.members_count or 0
    except:
        members = "N/A"
    
    # Get today's stats
    activity = await db.get_activity_stats()
    today_msgs = 0
    if activity.get("daily"):
        import time
        today = time.strftime("%Y-%m-%d")
        for d in activity["daily"]:
            if d["key"] == today:
                today_msgs = d["count"]
                break
    
    text = (
        f"**Chat Statistics**\n\n"
        f"**Members:** {members}\n"
        f"**Total Messages:** {msg_count}\n"
        f"**Messages Today:** {today_msgs}\n"
    )
    
    await message.reply_text(text)


@Client.on_message(filters.command("userstats"))
@error_handler
async def user_stats(client: Client, message: Message):
    """Show user statistics"""
    from zyrax.utils.users import extract_user
    
    user = await extract_user(client, message)
    if not user:
        user = message.from_user
    
    user_id = user.id if hasattr(user, "id") else user
    name = user.first_name if hasattr(user, "first_name") else str(user_id)
    
    user_data = await db.get_user_data(user_id)
    
    if not user_data:
        return await message.reply_text("No data found for this user.")
    
    msg_count = user_data.get("msg_count", 0)
    xp = user_data.get("xp", 0)
    level = user_data.get("level", 1)
    balance = user_data.get("balance", 0)
    karma = user_data.get("karma", 0)
    
    # Game stats
    games = user_data.get("games", {})
    game_text = ""
    if games:
        for game, stats in games.items():
            played = stats.get("played", 0)
            won = stats.get("won", 0)
            if played > 0:
                win_rate = (won / played) * 100
                game_text += f"  - {game.title()}: {won}/{played} ({win_rate:.0f}%)\n"
    
    text = (
        f"**Stats for {name}**\n\n"
        f"**Messages:** {msg_count}\n"
        f"**Level:** {level} ({xp} XP)\n"
        f"**Balance:** {balance} coins\n"
        f"**Karma:** {karma}\n"
    )
    
    if game_text:
        text += f"\n**Games:**\n{game_text}"
    
    await message.reply_text(text)


@Client.on_message(filters.command("topactive") & filters.group)
@error_handler
async def top_active(client: Client, message: Message):
    """Show top 10 most active users"""
    users = await db.get_collection("users")
    cursor = users.find({"msg_count": {"$exists": True}}).sort("msg_count", -1).limit(10)
    
    text = "**Top 10 Most Active Users:**\n\n"
    rank = 1
    async for user in cursor:
        name = user.get("username") or str(user["user_id"])
        count = user.get("msg_count", 0)
        text += f"{rank}. {name} - {count} messages\n"
        rank += 1
    
    await message.reply_text(text)


@Client.on_message(filters.command("activitystats") & filters.group)
@error_handler  
async def activity_stats(client: Client, message: Message):
    """Show activity summary"""
    activity = await db.get_activity_stats()
    
    text = "**Activity Summary (Last 7 Days):**\n\n"
    
    # Daily stats
    if activity.get("daily"):
        for day in activity["daily"][-7:]:
            text += f"- {day['key']}: {day['count']} messages\n"
    
    # Peak hours (from hourly data)
    hourly = activity.get("hourly", [])
    if hourly:
        # Group by hour (last part of key)
        hour_totals = {}
        for h in hourly:
            hour = h["key"].split("-")[-1]
            hour_totals[hour] = hour_totals.get(hour, 0) + h["count"]
        
        if hour_totals:
            peak_hour = max(hour_totals, key=hour_totals.get)
            text += f"\n**Peak Hour:** {peak_hour}:00"
    
    await message.reply_text(text)


@Client.on_message(filters.command("exportstats") & filters.group)
@require_admin()
@error_handler
async def export_stats(client: Client, message: Message):
    """Export analytics as JSON"""
    data = await db.export_chat_analytics(message.chat.id)
    
    # Convert to JSON
    json_str = json.dumps(data, indent=2, default=str)
    
    # Create file
    file = io.BytesIO(json_str.encode())
    file.name = f"analytics_{message.chat.id}.json"
    
    await message.reply_document(file, caption="Chat Analytics Export")


@Client.on_message(filters.command("exportlogs") & filters.group)
@require_admin()
@error_handler
async def export_logs(client: Client, message: Message):
    """Export audit logs as JSON"""
    logs = await db.get_audit_logs(limit=500)
    
    # Filter for this chat
    chat_logs = [l for l in logs if l.get("chat_id") == message.chat.id]
    
    # Clean for JSON
    clean_logs = []
    for log in chat_logs:
        clean_logs.append({
            "action": log["action"],
            "user_id": log.get("user_id"),
            "target_id": log.get("target_id"),
            "details": log.get("details"),
            "timestamp": log["timestamp"]
        })
    
    json_str = json.dumps(clean_logs, indent=2, default=str)
    
    file = io.BytesIO(json_str.encode())
    file.name = f"audit_logs_{message.chat.id}.json"
    
    await message.reply_document(file, caption="Audit Logs Export")


@Client.on_message(filters.command("gamestats"))
@error_handler
async def game_stats(client: Client, message: Message):
    """Show game leaderboards"""
    games = ["trivia", "guess", "hangman", "scramble", "ttt"]
    
    text = "**Game Leaderboards:**\n"
    
    for game in games:
        leaders = await db.get_game_leaderboard(game, limit=3)
        if leaders:
            text += f"\n**{game.upper()}:**\n"
            for i, user in enumerate(leaders, 1):
                name = user.get("username") or str(user["user_id"])
                wins = user.get("games", {}).get(game, {}).get("won", 0)
                text += f"  {i}. {name} - {wins} wins\n"
    
    await message.reply_text(text)
