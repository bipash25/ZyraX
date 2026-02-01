from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.utils.decorators import require_admin
from zyrax.database.mongo import db
from zyrax.utils.errors import error_handler
from zyrax.utils.users import extract_user

__mod_name__ = "Warnings"
__help__ = """
/warn <user> <reason> - Warn a user
/unwarn <user> - Remove a warn from a user
/rmwarn <user> - Alias for /unwarn
/resetwarns <user> - Reset all warns for a user
"""

@Client.on_message(filters.command("warn") & filters.group)
@require_admin()
async def warn_user(client: Client, message: Message):
    user = await extract_user(client, message)
    if not user:
        return await message.reply_text("Reply to a user or mention them to warn.")
    
    # Reason logic: if reply, args start at 1. If mention, args start at 2 (command + mention + reason)
    reason = "No reason"
    if message.reply_to_message:
        if len(message.command) > 1:
            reason = " ".join(message.command[1:])
    elif len(message.command) > 2:
        reason = " ".join(message.command[2:])
        
    user_id = user.id if hasattr(user, "id") else user
    user_mention = user.mention if hasattr(user, "mention") else str(user_id)
    
    count = await db.add_warn(message.chat.id, user_id, reason)
    
    await message.reply_text(f"Warned {user_mention}. Count: {count}")
    await db.log_admin_action("warn", client.me.id, message.chat.id, user_id, f"Reason: {reason}, Count: {count}")
    
    # Check for max warns (hardcoded to 3 for now, make configurable later)
    if count >= 3:
        try:
            await client.ban_chat_member(message.chat.id, user_id)
            await message.reply_text(f"{user_mention} has lived their life! (3/3 warns => Banned)")
            await db.reset_warns(message.chat.id, user_id)
            await db.log_admin_action("ban", client.me.id, message.chat.id, user_id, "Max Warnings Reached")
        except Exception as e:
            await message.reply_text(f"Failed to ban: {e}")


@Client.on_message(filters.command(["unwarn", "rmwarn"]) & filters.group)
@require_admin()
async def remove_warn(client: Client, message: Message):
    user = await extract_user(client, message)
    if not user:
        return await message.reply_text("Reply to a user or mention them to remove warn.")
    
    user_id = user.id if hasattr(user, "id") else user
    user_mention = user.mention if hasattr(user, "mention") else str(user_id)

    count = await db.remove_warn(message.chat.id, user_id)
    
    await message.reply_text(f"Removed warn for {user_mention}. Current count: {count}")
    await db.log_admin_action("unwarn", client.me.id, message.chat.id, user_id)

@Client.on_message(filters.command("resetwarns") & filters.group)
@require_admin()
async def reset_warns(client: Client, message: Message):
    user = await extract_user(client, message)
    if not user:
        return await message.reply_text("Reply to a user or mention them to reset warns.")
    
    user_id = user.id if hasattr(user, "id") else user
    user_mention = user.mention if hasattr(user, "mention") else str(user_id)

    await db.reset_warns(message.chat.id, user_id)
    await message.reply_text(f"Reset all warns for {user_mention}.")
    await db.log_admin_action("resetwarns", client.me.id, message.chat.id, user_id)
