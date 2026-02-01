from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.database.mongo import db

__mod_name__ = "Analytics"
__help__ = """
Passive module. Tracks message statistics.
"""

@Client.on_message(filters.group, group=0)
async def analytics_tracker(client: Client, message: Message):
    if not message.from_user:
        return
        
    # Async track (fire and forget)
    try:
        await db.track_activity(message.from_user.id, message.chat.id)
    except:
        pass
