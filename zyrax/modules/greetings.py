from pyrogram import Client, filters
from pyrogram.types import Message

__mod_name__ = "Greetings"
__help__ = """
Auto-Greeting system:
- Welcome new members
- Goodbye to leaving members
"""

@Client.on_message(filters.new_chat_members & filters.group)
async def welcome(client: Client, message: Message):
    for member in message.new_chat_members:
        # Check if it's the bot itself
        if member.id == client.me.id:
             await message.reply_text(f"Hello! I am ZyraX. Thanks for adding me to {message.chat.title}!")

@Client.on_message(filters.left_chat_member & filters.group)
async def goodbye(client: Client, message: Message):
    member = message.left_chat_member
    if member.id == client.me.id:
        return 
    await message.reply_text(f"Goodbye {member.mention}! We will miss you.")
