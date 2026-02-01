from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from zyrax.utils.decorators import require_admin
from zyrax.utils.errors import error_handler
from zyrax.database.mongo import db

__mod_name__ = "Reports"
__help__ = """
/report - Reply to a message to report it to admins.
"""

@Client.on_message(filters.command("report") & filters.group)
@error_handler
async def report_handler(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a message to report it.")
    
    reported_msg = message.reply_to_message
    reporter = message.from_user
    
    # Notify Admins
    chat_id = message.chat.id
    
    # Build report text
    text = (
        f"⚠️ **New Report**\n\n"
        f"**User:** {reported_msg.from_user.mention if reported_msg.from_user else 'Unknown'} (`{reported_msg.from_user.id if reported_msg.from_user else 'Unknown'}`)\n"
        f"**Reporter:** {reporter.mention if reporter else 'Unknown'} (`{reporter.id if reporter else 'Unknown'}`)\n"
        f"**Chat:** {message.chat.title}\n"
        f"**Link:** {reported_msg.link if reported_msg.link else 'No Link'}\n"
    )
    
    # Send to admins
    admins = []
    try:
        async for member in client.get_chat_members(chat_id, filter=ChatMemberStatus.ADMINISTRATOR):
            if member.user and not member.user.is_bot:
                admins.append(member.user.mention)
        
        # Also include owner
        async for member in client.get_chat_members(chat_id, filter=ChatMemberStatus.OWNER):
            if member.user and not member.user.is_bot:
                admins.append(member.user.mention)
    except Exception as e:
        # Fallback if admin fetch fails
        pass
            
    if admins:
        # Deduplicate
        admins = list(set(admins))
        # Split into chunks if too many admins (Telegram limit)
        admin_text = " ".join(admins)
        # Verify length
        if len(text + admin_text) > 4096:
            await message.reply_text(text)
            await message.reply_text(admin_text)
        else:
            await message.reply_text(f"{text}\n{admin_text}")
    else:
        await message.reply_text(f"{text}\n(No admins tagged)")
