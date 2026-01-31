from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.database.mongo import db

__mod_name__ = "Stats Tracker"
__help__ = "Internal module for tracking usage stats."

@Client.on_message(filters.group, group=-1)
async def track_chat(client: Client, message: Message):
    # Track Chat
    await db.register_chat(message.chat.id, message.chat.title)
    
    # Track User
    if message.from_user:
        await db.register_user(message.from_user.id, message.from_user.username)
        
    # Track Command Usage
    if message.text and message.text.startswith("/"):
        await db.track_command_usage()

@Client.on_message(filters.private, group=-1)
async def track_private(client: Client, message: Message):
    if message.from_user:
        await db.register_user(message.from_user.id, message.from_user.username)
