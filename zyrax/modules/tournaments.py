from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.utils.decorators import require_admin
from zyrax.database.mongo import db

__mod_name__ = "Tournaments"
__help__ = """
/tourney <name> <size> - Create a tournament (2, 4, 8, 16, 32)
/join - Join the current tournament
/starttourney - Start the tournament (Close registration)
/bracket - View current bracket
"""

@Client.on_message(filters.command("tourney") & filters.group)
@require_admin()
async def create_tourney(client: Client, message: Message):
    if len(message.command) < 3:
        return await message.reply_text("Usage: /tourney <name> <size> (e.g., /tourney PubG 8)")
    
    name = message.command[1]
    try:
        size = int(message.command[2])
        if size not in [2, 4, 8, 16, 32]:
            return await message.reply_text("Size must be power of 2 (2, 4, 8, 16, 32).")
    except ValueError:
        return await message.reply_text("Size must be an integer.")
        
    success = await db.create_tournament(message.chat.id, name, size)
    if success:
        await message.reply_text(f"Tournament '{name}' created for {size} players! Type /join to register.")
    else:
        await message.reply_text("An active tournament already exists in this chat.")

@Client.on_message(filters.command("join") & filters.group)
async def join_tourney(client: Client, message: Message):
    user = message.from_user
    result = await db.join_tournament(message.chat.id, user.id, user.first_name)
    
    if result == "joined":
        await message.reply_text(f"{user.mention} joined the tournament!")
    elif result == "full":
        await message.reply_text("Tournament is full!")
    elif result == "already_joined":
        await message.reply_text("You already joined!")
    elif result == "no_tournament":
        await message.reply_text("No tournament open for registration.")

@Client.on_message(filters.command("starttourney") & filters.group)
@require_admin()
async def start_tourney(client: Client, message: Message):
    success = await db.start_tournament(message.chat.id)
    if success:
        await message.reply_text("Tournament started! Check /bracket for matches.")
    else:
        await message.reply_text("Could not start tournament (Check if enough players or if one exists).")

@Client.on_message(filters.command("bracket") & filters.group)
async def view_bracket(client: Client, message: Message):
    tourney = await db.get_active_tournament(message.chat.id)
    if not tourney:
        return await message.reply_text("No active tournament.")
        
    if tourney["status"] == "registration":
        participants = tourney["participants"]
        text = f"**{tourney['name']} (Registration)**\n"
        text += f"Players: {len(participants)}/{tourney['size']}\n"
        for p in participants:
            text += f"- {p['name']}\n"
        await message.reply_text(text)
    elif tourney["status"] == "active":
        text = f"**{tourney['name']} (Round {tourney['round']})**\n"
        for i, match in enumerate(tourney["matches"]):
            p1 = match["p1"]["name"]
            p2 = match["p2"]["name"] if match["p2"] else "Bye"
            text += f"Match {i+1}: {p1} vs {p2}\n"
        await message.reply_text(text)
