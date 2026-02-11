from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from zyrax.database.mongo import db
from zyrax.utils.errors import error_handler
from datetime import datetime

__mod_name__ = "UserInfo"
__help__ = """
/info [user] - Get detailed info about a user
/id - Get current chat ID and your user ID
"""

@Client.on_message(filters.command("info"))
@error_handler
async def get_user_info(client: Client, message: Message):
    user = None
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            # Try by username or ID
            user_input = message.command[1]
            if user_input.isdigit():
                user = await client.get_users(int(user_input))
            else:
                user = await client.get_users(user_input)
        except Exception:
            return await message.reply_text("User not found.")
    else:
        user = message.from_user

    if not user:
        return await message.reply_text("Could not determine user.")

    # Fetch extra data from DB if available (e.g. warnings, XP)
    warns = await db.get_warns(message.chat.id, user.id)
    warn_count = warns["count"] if warns else 0
    
    # Get member status in current chat
    try:
        member = await message.chat.get_member(user.id)
        status = member.status.name.title()
        joined_date = member.joined_date.strftime("%Y-%m-%d %H:%M:%S") if member.joined_date else "Unknown"
    except Exception:
        status = "Member (Left/Kicked)"
        joined_date = "Unknown"

    text = (
        f"**User Info for {user.mention}:**\n"
        f"🆔 **ID:** `{user.id}`\n"
        f"👤 **First Name:** {user.first_name}\n"
    )
    
    if user.last_name:
        text += f"👤 **Last Name:** {user.last_name}\n"
    if user.username:
        text += f"🔗 **Username:** @{user.username}\n"
    
    text += (
        f"🛡 **Status:** {status}\n"
        f"📅 **Joined Chat:** {joined_date}\n"
        f"⚠️ **Warnings:** {warn_count}/3\n"
        f"🤖 **Bot:** {'Yes' if user.is_bot else 'No'}\n"
        f"🏢 **DC ID:** {user.dc_id if user.dc_id else 'Unknown'}\n"
    )
    
    # Check for premium if user object has it (Pyrogram raw types might have it, high level maybe not fully)
    if getattr(user, "is_premium", False):
         text += f"🌟 **Premium User:** Yes\n"

    await message.reply_text(text)

@Client.on_message(filters.command("id") & filters.group)
@error_handler
async def get_id(client: Client, message: Message):
    text = f"**Chat ID:** `{message.chat.id}`\n"
    if message.reply_to_message:
        text += f"**User ID:** `{message.reply_to_message.from_user.id}`"
    else:
        text += f"**Your ID:** `{message.from_user.id}`"
    await message.reply_text(text)
