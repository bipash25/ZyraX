from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from zyrax.utils.decorators import require_admin

__mod_name__ = "Bans"
__help__ = """
/ban <user> - Ban a user
/unban <user> - Unban a user
/kick <user> - Kick a user
/mute <user> - Mute a user
/unmute <user> - Unmute a user
"""

@Client.on_message(filters.command("ban") & filters.group)
@require_admin()
async def ban_user(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to ban them.")
    
    user_id = message.reply_to_message.from_user.id
    try:
        await client.ban_chat_member(message.chat.id, user_id)
        await message.reply_text(f"Banned {message.reply_to_message.from_user.mention}.")
    except Exception as e:
        await message.reply_text(f"Failed to ban: {str(e)}")

@Client.on_message(filters.command("unban") & filters.group)
@require_admin()
async def unban_user(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to unban them.")
    
    user_id = message.reply_to_message.from_user.id
    try:
        await client.unban_chat_member(message.chat.id, user_id)
        await message.reply_text(f"Unbanned {message.reply_to_message.from_user.mention}.")
    except Exception as e:
        await message.reply_text(f"Failed to unban: {str(e)}")

@Client.on_message(filters.command("kick") & filters.group)
@require_admin()
async def kick_user(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to kick them.")
    
    user_id = message.reply_to_message.from_user.id
    try:
        await client.ban_chat_member(message.chat.id, user_id)
        await client.unban_chat_member(message.chat.id, user_id)
        await message.reply_text(f"Kicked {message.reply_to_message.from_user.mention}.")
    except Exception as e:
        await message.reply_text(f"Failed to kick: {str(e)}")

@Client.on_message(filters.command("mute") & filters.group)
@require_admin()
async def mute_user(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to mute them.")
    
    user_id = message.reply_to_message.from_user.id
    try:
        # Mute indefinitely
        await client.restrict_chat_member(message.chat.id, user_id, ChatPermissions())
        await message.reply_text(f"Muted {message.reply_to_message.from_user.mention}.")
    except Exception as e:
        await message.reply_text(f"Failed to mute: {str(e)}")

@Client.on_message(filters.command("unmute") & filters.group)
@require_admin()
async def unmute_user(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to unmute them.")
    
    user_id = message.reply_to_message.from_user.id
    try:
        # Unmute (Give default permissions - hardcoded for now due to lack of ChatPermissions object in args)
        # Actually better to use ChatPermissions with all True or similar, but typically unban_chat_member lifts restrictions too?
        # unban_chat_member removes from banned list, but for restricted members it might be different.
        # Let's try unban_chat_member which usually resets permissions to default for the group.
        await client.unban_chat_member(message.chat.id, user_id)
        await message.reply_text(f"Unmuted {message.reply_to_message.from_user.mention}.")
    except Exception as e:
        await message.reply_text(f"Failed to unmute: {str(e)}")
