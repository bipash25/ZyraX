import time
from pyrogram import Client, filters
from pyrogram.types import Message

__mod_name__ = "Utilities"
__help__ = """
/ping - Check bot latency
"""

@Client.on_message(filters.command("ping"))
async def ping(client: Client, message: Message):
    start = time.time()
    msg = await message.reply_text("Pong!")
    end = time.time()
    await msg.edit_text(f"Pong! {round((end - start) * 1000)}ms")
