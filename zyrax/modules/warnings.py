"""
Warnings Module

User warning system with configurable max warns and auto-ban.
"""

from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.utils.decorators import require_admin
from zyrax.utils.ratelimit import rate_limit
from zyrax.database.mongo import db
from zyrax.utils.errors import error_handler
from zyrax.utils.users import extract_user
from zyrax.utils.validators import InputValidator
from zyrax.constants import Limits


__mod_name__ = "Warnings"
__help__ = """
/warn <user> <reason> - Warn a user
/warns <user> - Check a user's warnings
/unwarn <user> - Remove a warn from a user
/rmwarn <user> - Alias for /unwarn
/resetwarns <user> - Reset all warns for a user
"""


@Client.on_message(filters.command("warn") & filters.group)
@rate_limit(max_attempts=10, window=60)
@error_handler
@require_admin()
async def warn_user(client: Client, message: Message):
    """Warn a user."""
    user = await extract_user(client, message)
    if not user:
        return await message.reply_text(
            "Reply to a user or mention them to warn."
        )
    
    # Get user info
    user_id = user.id if hasattr(user, "id") else user
    user_mention = user.mention if hasattr(user, "mention") else f"User {user_id}"
    
    # Check if user is admin (can't warn admins)
    try:
        member = await client.get_chat_member(message.chat.id, user_id)
        if member.status in ("administrator", "creator"):
            return await message.reply_text("Cannot warn an admin!")
    except Exception:
        pass
    
    # Extract reason
    if message.reply_to_message:
        reason = " ".join(message.command[1:]) if len(message.command) > 1 else None
    else:
        reason = " ".join(message.command[2:]) if len(message.command) > 2 else None
    
    # Validate and sanitize reason
    is_valid, reason = InputValidator.validate_warn_reason(reason)
    
    # Add warning
    count = await db.add_warn(message.chat.id, user_id, reason)
    max_warns = Limits.MAX_WARNS
    
    await message.reply_text(
        f"**Warned** {user_mention}\n"
        f"**Reason:** {reason}\n"
        f"**Warnings:** {count}/{max_warns}"
    )
    
    await db.log_admin_action(
        "warn",
        message.from_user.id,
        message.chat.id,
        user_id,
        f"Reason: {reason}, Count: {count}/{max_warns}"
    )
    
    # Check for max warns - auto ban
    if count >= max_warns:
        try:
            await client.ban_chat_member(message.chat.id, user_id)
            await message.reply_text(
                f"{user_mention} has been **banned**!\n"
                f"Reached maximum warnings ({max_warns}/{max_warns})"
            )
            await db.reset_warns(message.chat.id, user_id)
            await db.log_admin_action(
                "ban",
                client.me.id,
                message.chat.id,
                user_id,
                "Max warnings reached"
            )
        except Exception as e:
            await message.reply_text(f"Failed to ban user: {e}")


@Client.on_message(filters.command("warns") & filters.group)
@rate_limit(max_attempts=10, window=60)
@error_handler
async def check_warns(client: Client, message: Message):
    """Check a user's warnings."""
    user = await extract_user(client, message)
    if not user:
        # Check own warns
        user = message.from_user
    
    user_id = user.id if hasattr(user, "id") else user
    user_name = user.first_name if hasattr(user, "first_name") else f"User {user_id}"
    
    warns = await db.get_warns(message.chat.id, user_id)
    count = len(warns) if warns else 0
    
    if count == 0:
        return await message.reply_text(f"{user_name} has no warnings.")
    
    text = f"**Warnings for {user_name}:** {count}/{Limits.MAX_WARNS}\n\n"
    
    for i, warn in enumerate(warns[-5:], 1):  # Show last 5 warns
        reason = warn.get("reason", "No reason")
        text += f"{i}. {reason}\n"
    
    if count > 5:
        text += f"\n_...and {count - 5} more_"
    
    await message.reply_text(text)


@Client.on_message(filters.command(["unwarn", "rmwarn"]) & filters.group)
@rate_limit(max_attempts=10, window=60)
@error_handler
@require_admin()
async def remove_warn(client: Client, message: Message):
    """Remove a warning from a user."""
    user = await extract_user(client, message)
    if not user:
        return await message.reply_text(
            "Reply to a user or mention them to remove a warning."
        )
    
    user_id = user.id if hasattr(user, "id") else user
    user_mention = user.mention if hasattr(user, "mention") else f"User {user_id}"
    
    count = await db.remove_warn(message.chat.id, user_id)
    
    await message.reply_text(
        f"Removed 1 warning from {user_mention}.\n"
        f"**Current warnings:** {count}/{Limits.MAX_WARNS}"
    )
    
    await db.log_admin_action(
        "unwarn",
        message.from_user.id,
        message.chat.id,
        user_id
    )


@Client.on_message(filters.command("resetwarns") & filters.group)
@rate_limit(max_attempts=10, window=60)
@error_handler
@require_admin()
async def reset_warns(client: Client, message: Message):
    """Reset all warnings for a user."""
    user = await extract_user(client, message)
    if not user:
        return await message.reply_text(
            "Reply to a user or mention them to reset warnings."
        )
    
    user_id = user.id if hasattr(user, "id") else user
    user_mention = user.mention if hasattr(user, "mention") else f"User {user_id}"
    
    await db.reset_warns(message.chat.id, user_id)
    
    await message.reply_text(f"Reset all warnings for {user_mention}.")
    
    await db.log_admin_action(
        "resetwarns",
        message.from_user.id,
        message.chat.id,
        user_id
    )
