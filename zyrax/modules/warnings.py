from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.utils.decorators import require_admin
from zyrax.database.mongo import db

__mod_name__ = "Warnings"
__help__ = """
/warn <user> <reason> - Warn a user
/rmwarn <user> - Remove a warn from a user
/warns <user> - Check user's warns (To be implemented)
"""

@Client.on_message(filters.command("warn") & filters.group)
@require_admin()
async def warn_user(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to warn them.")
    
    user = message.reply_to_message.from_user
    reason = " ".join(message.command[1:]) if len(message.command) > 1 else "No reason"
    
    count = await db.add_warn(message.chat.id, user.id, reason)
    
    await message.reply_text(f"Warned {user.mention}. Count: {count}")
    
    # Check for max warns (hardcoded to 3 for now, make configurable later)
    if count >= 3:
        try:
            await client.ban_chat_member(message.chat.id, user.id)
            await message.reply_text(f"{user.mention} has lived their life! (3/3 warns => Banned)")
            await db.reset_warns(message.chat.id, user.id)
        except Exception as e:
            await message.reply_text(f"Failed to ban: {e}")


@Client.on_message(filters.command("rmwarn") & filters.group)
@require_admin()
async def remove_warn(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to remove their warn.")
    
    user = message.reply_to_message.from_user
    count = await db.remove_warn(message.chat.id, user.id)
    
    await message.reply_text(f"Removed warn for {user.mention}. Current count: {count}")
