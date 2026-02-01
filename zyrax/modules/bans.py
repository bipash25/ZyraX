from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from zyrax.utils.decorators import require_admin
from zyrax.utils.errors import error_handler
from zyrax.utils.ratelimit import rate_limit
from zyrax.utils.time_parser import parse_duration
from zyrax.utils.users import extract_user
from zyrax.utils.i18n import get_text
from zyrax.database.mongo import db
import time
from datetime import datetime, timedelta

__mod_name__ = "Bans"
__help__ = """
/ban <user> - Ban a user
/unban <user> - Unban a user
/kick <user> - Kick a user
/mute <user> - Mute a user
/unmute <user> - Unmute a user
/tban <time> <user> - Temporarily ban a user
/tmute <time> <user> - Temporarily mute a user
/sban <user> - Soft ban (ban and immediate unban to delete messages)
"""

@Client.on_message(filters.command("ban") & filters.group)
@rate_limit(max_attempts=5, window=60)
@error_handler
@require_admin()
async def ban_user(client: Client, message: Message):
    lang = await db.get_chat_language(message.chat.id)
    user = await extract_user(client, message)
    if not user:
        return await message.reply_text(get_text("user_not_found", lang))
    
    user_id = user.id if hasattr(user, "id") else user
    user_mention = user.mention if hasattr(user, "mention") else str(user_id)

    try:
        await client.ban_chat_member(message.chat.id, user_id)
        await message.reply_text(get_text("banned", lang, mention=user_mention))
        await db.log_admin_action("ban", client.me.id, message.chat.id, user_id)
    except Exception as e:
        await message.reply_text(get_text("error", lang, error=str(e)))

@Client.on_message(filters.command("unban") & filters.group)
@error_handler
@require_admin()
async def unban_user(client: Client, message: Message):
    lang = await db.get_chat_language(message.chat.id)
    user = await extract_user(client, message)
    if not user:
        return await message.reply_text(get_text("user_not_found", lang))
    
    user_id = user.id if hasattr(user, "id") else user
    user_mention = user.mention if hasattr(user, "mention") else str(user_id)

    try:
        await client.unban_chat_member(message.chat.id, user_id)
        await message.reply_text(get_text("unbanned", lang, mention=user_mention))
        await db.log_admin_action("unban", client.me.id, message.chat.id, user_id)
    except Exception as e:
        await message.reply_text(get_text("error", lang, error=str(e)))

@Client.on_message(filters.command("kick") & filters.group)
@rate_limit(max_attempts=10, window=60)
@error_handler
@require_admin()
async def kick_user(client: Client, message: Message):
    lang = await db.get_chat_language(message.chat.id)
    user = await extract_user(client, message)
    if not user:
        return await message.reply_text(get_text("user_not_found", lang))
    
    user_id = user.id if hasattr(user, "id") else user
    user_mention = user.mention if hasattr(user, "mention") else str(user_id)

    try:
        await client.ban_chat_member(message.chat.id, user_id)
        await client.unban_chat_member(message.chat.id, user_id)
        await message.reply_text(get_text("kicked", lang, mention=user_mention))
        await db.log_admin_action("kick", client.me.id, message.chat.id, user_id)
    except Exception as e:
        await message.reply_text(get_text("error", lang, error=str(e)))

@Client.on_message(filters.command("mute") & filters.group)
@error_handler
@require_admin()
async def mute_user(client: Client, message: Message):
    lang = await db.get_chat_language(message.chat.id)
    user = await extract_user(client, message)
    if not user:
        return await message.reply_text(get_text("user_not_found", lang))
    
    user_id = user.id if hasattr(user, "id") else user
    user_mention = user.mention if hasattr(user, "mention") else str(user_id)

    try:
        # Mute indefinitely
        await client.restrict_chat_member(message.chat.id, user_id, ChatPermissions())
        await message.reply_text(get_text("muted", lang, mention=user_mention))
        await db.log_admin_action("mute", client.me.id, message.chat.id, user_id)
    except Exception as e:
        await message.reply_text(get_text("error", lang, error=str(e)))

@Client.on_message(filters.command("unmute") & filters.group)
@error_handler
@require_admin()
async def unmute_user(client: Client, message: Message):
    lang = await db.get_chat_language(message.chat.id)
    user = await extract_user(client, message)
    if not user:
        return await message.reply_text(get_text("user_not_found", lang))
    
    user_id = user.id if hasattr(user, "id") else user
    user_mention = user.mention if hasattr(user, "mention") else str(user_id)

    try:
        # Unmute by giving sending permissions
        await client.restrict_chat_member(
            message.chat.id,
            user_id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_send_polls=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False
            )
        )
        await message.reply_text(get_text("unmuted", lang, mention=user_mention))
        await db.log_admin_action("unmute", client.me.id, message.chat.id, user_id)
    except Exception as e:
        await message.reply_text(get_text("error", lang, error=str(e)))

@Client.on_message(filters.command("tban") & filters.group)
@error_handler
@require_admin()
async def tban_user(client: Client, message: Message):
    # Args: /tban time user OR /tban user time OR reply /tban time
    if len(message.command) < 2:
        return await message.reply_text("Usage: /tban <time> [user]")

    # Check first arg for time
    duration = parse_duration(message.command[1])
    target_arg_idx = 2
    if not duration:
        # Maybe user provided user first? /tban user time (uncommon but possible)
        # Or maybe replied?
        # Let's assume syntax /tban time [user]
        return await message.reply_text("Invalid time format. Use 10m, 2h, 1d.")

    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 2:
        # Try to get user from 2nd arg
        # We need to construct a temp message object or modify logic of extract_user to take arg
        # But extract_user uses message.command[1]. We need to temporarily shift args or query manually
        try:
            user = await client.get_users(message.command[2])
        except:
            user = None
    else:
        return await message.reply_text("Reply to a user or mention them.")

    if not user:
        return await message.reply_text("User not found.")

    user_id = user.id
    until_date = datetime.now() + timedelta(seconds=duration)
    
    try:
        await client.ban_chat_member(message.chat.id, user_id, until_date=until_date)
        await message.reply_text(f"Banned {user.mention} for {message.command[1]}.")
        await db.log_admin_action("tban", client.me.id, message.chat.id, user_id, f"Duration: {message.command[1]}")
    except Exception as e:
        await message.reply_text(f"Failed to ban: {str(e)}")

@Client.on_message(filters.command("tmute") & filters.group)
@error_handler
@require_admin()
async def tmute_user(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /tmute <time> [user]")

    duration = parse_duration(message.command[1])
    if not duration:
        return await message.reply_text("Invalid time format.")

    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 2:
        try:
            user = await client.get_users(message.command[2])
        except:
            user = None
    else:
        return await message.reply_text("Reply to a user or mention them.")

    if not user:
        return await message.reply_text("User not found.")
    
    until_date = datetime.now() + timedelta(seconds=duration)
    
    try:
        await client.restrict_chat_member(
            message.chat.id, 
            user.id, 
            ChatPermissions(),
            until_date=until_date
        )
        await message.reply_text(f"Muted {user.mention} for {message.command[1]}.")
        await db.log_admin_action("tmute", client.me.id, message.chat.id, user.id, f"Duration: {message.command[1]}")
    except Exception as e:
        await message.reply_text(f"Failed to mute: {str(e)}")

@Client.on_message(filters.command("sban") & filters.group)
@error_handler
@require_admin()
async def sban_user(client: Client, message: Message):
    user = await extract_user(client, message)
    if not user:
        return await message.reply_text("Reply to a user or mention them to soft ban.")
    
    user_id = user.id if hasattr(user, "id") else user
    user_mention = user.mention if hasattr(user, "mention") else str(user_id)

    try:
        await client.ban_chat_member(message.chat.id, user_id)
        await client.unban_chat_member(message.chat.id, user_id)
        await message.reply_text(f"Soft banned {user_mention} (messages deleted).")
        await db.log_admin_action("sban", client.me.id, message.chat.id, user_id)
    except Exception as e:
        await message.reply_text(f"Failed to soft ban: {str(e)}")
