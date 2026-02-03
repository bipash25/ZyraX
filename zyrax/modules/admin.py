from pyrogram import Client, filters
from pyrogram.types import Message, ChatPrivileges
from pyrogram.enums import ChatMembersFilter
from zyrax.utils.decorators import require_admin
from zyrax.utils.errors import error_handler
from zyrax.utils.users import extract_user
from zyrax.database.mongo import db
from zyrax.constants import Limits

__mod_name__ = "Admin"
__help__ = """
/promote <user> [title] - Promote a user to admin with optional title
/demote <user> - Demote an admin
/adminlist - List all admins in the chat
"""

@Client.on_message(filters.command("promote") & filters.group)
@error_handler
@require_admin()
async def promote(client: Client, message: Message):
    user = await extract_user(client, message)
    if not user:
        return await message.reply_text("Reply to a user or mention them to promote.")
    
    # Extract Title:
    # If reply: /promote Title (command 0, arg 1..)
    # If mention: /promote @user Title (command 0, arg 1, arg 2..)
    title = "Admin"
    if message.reply_to_message:
        if len(message.command) > 1:
            title = " ".join(message.command[1:])
    elif len(message.command) > 2:
        title = " ".join(message.command[2:])
        
    # Trim title to Telegram's limit
    if len(title) > Limits.MAX_ADMIN_TITLE_LENGTH:
        title = title[:Limits.MAX_ADMIN_TITLE_LENGTH]

    user_id = user.id if hasattr(user, "id") else user
    user_mention = user.mention if hasattr(user, "mention") else str(user_id)

    try:
        await client.promote_chat_member(
            message.chat.id,
            user_id,
            privileges=ChatPrivileges(
                can_change_info=True,
                can_delete_messages=True,
                can_restrict_members=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_manage_video_chats=True,
                can_promote_members=False
            )
        )
        # Set custom title (Requires promote first usually, or separate call)
        # set_administrator_title is separate method
        try:
            await client.set_administrator_title(message.chat.id, user_id, title)
        except Exception as e:
            # Ignore title errors (e.g. not enough rights to set title, or user is bot)
            pass
            
        await message.reply_text(f"Promoted {user_mention} with title **{title}**.")
        await db.log_admin_action("promote", client.me.id, message.chat.id, user_id, f"Title: {title}")
    except Exception as e:
        await message.reply_text(f"Failed to promote: {str(e)}")

@Client.on_message(filters.command("demote") & filters.group)
@error_handler
@require_admin()
async def demote(client: Client, message: Message):
    user = await extract_user(client, message)
    if not user:
        return await message.reply_text("Reply to a user or mention them to demote.")
    
    user_id = user.id if hasattr(user, "id") else user
    user_mention = user.mention if hasattr(user, "mention") else str(user_id)

    try:
        # Demote by setting all privileges to False
        await client.promote_chat_member(
            message.chat.id,
            user_id,
            privileges=ChatPrivileges(
                can_change_info=False,
                can_delete_messages=False,
                can_restrict_members=False,
                can_invite_users=False,
                can_pin_messages=False,
                can_manage_video_chats=False,
                can_promote_members=False,
                is_anonymous=False
            )
        )
        # Try to set title empty?
        try:
            await client.set_administrator_title(message.chat.id, user_id, "")
        except:
            pass
            
        await message.reply_text(f"Demoted {user_mention}.")
        await db.log_admin_action("demote", client.me.id, message.chat.id, user_id)
    except Exception as e:
        await message.reply_text(f"Failed to demote: {str(e)}")

@Client.on_message(filters.command("adminlist") & filters.group)
@error_handler
async def adminlist(client: Client, message: Message):
    chat_id = message.chat.id
    admins = []
    try:
        async for member in client.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS):
            user = member.user
            name = user.first_name if user else "Unknown"
            if user.is_bot:
                 name += " [BOT]"
            admins.append(f"- {user.mention}")
            
    except Exception as e:
        return await message.reply_text(f"Error fetching admins: {e}")

    if not admins:
        await message.reply_text("Could not fetch admins (Empty list).")
    else:
        await message.reply_text(f"**Admins in {message.chat.title}:**\n" + "\n".join(admins))
