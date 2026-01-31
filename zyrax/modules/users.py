from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

__mod_name__ = "Users"
__help__ = """
/info [user] - Get info about a user
"""

@Client.on_message(filters.command("info") & filters.group)
async def get_user_info(client: Client, message: Message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            user = await client.get_users(message.command[1])
        except Exception:
            return await message.reply_text("User not found.")
    else:
        user = message.from_user

    text = (
        f"**User Info:**\n"
        f"ID: `{user.id}`\n"
        f"First Name: {user.first_name}\n"
    )
    if user.last_name:
        text += f"Last Name: {user.last_name}\n"
    if user.username:
        text += f"Username: @{user.username}\n"
    if user.dc_id:
        text += f"DC ID: {user.dc_id}\n"
        
    await message.reply_text(text)
