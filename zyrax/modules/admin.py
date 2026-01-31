from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.utils.decorators import require_admin
from zyrax.utils.errors import error_handler

__mod_name__ = "Admin"
__help__ = """
/promote <user> - Promote a user to admin
/demote <user> - Demote an admin
/adminlist - List all admins in the chat
"""

@Client.on_message(filters.command("promote") & filters.group)
@error_handler
@require_admin()
async def promote(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to promote them.")
    
    user_id = message.reply_to_message.from_user.id
    try:
        await client.promote_chat_member(
            message.chat.id,
            user_id,
            can_change_info=True,
            can_delete_messages=True,
            can_restrict_members=True,
            can_invite_users=True,
            can_pin_messages=True
        )
        await message.reply_text(f"Promoted {message.reply_to_message.from_user.mention}.")
    except Exception as e:
        await message.reply_text(f"Failed to promote: {str(e)}")

@Client.on_message(filters.command("demote") & filters.group)
@error_handler
@require_admin()
async def demote(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to demote them.")
    
    user_id = message.reply_to_message.from_user.id
    try:
        await client.promote_chat_member(
            message.chat.id,
            user_id,
            can_change_info=False,
            can_delete_messages=False,
            can_restrict_members=False,
            can_invite_users=False,
            can_pin_messages=False
        )
        await message.reply_text(f"Demoted {message.reply_to_message.from_user.mention}.")
    except Exception as e:
        await message.reply_text(f"Failed to demote: {str(e)}")

@Client.on_message(filters.command("adminlist") & filters.group)
async def adminlist(client: Client, message: Message):
    chat_id = message.chat.id
    admins = []
    async for member in client.get_chat_members(chat_id, filter="administrators"):
        admins.append(member.user.mention)
    
    await message.reply_text(f"Admins in {message.chat.title}:\n" + "\n".join(admins))
