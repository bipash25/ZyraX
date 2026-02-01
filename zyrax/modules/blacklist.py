from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.enums import ChatMemberStatus
from zyrax.utils.decorators import require_admin
from zyrax.utils.errors import error_handler
from zyrax.database.mongo import db

__mod_name__ = "Blacklist"
__help__ = """
/blacklist add <word> [action] - Add a word to blacklist. Actions: delete (default), warn, ban, kick, mute.
/blacklist remove <word> - Remove a word from blacklist.
/blacklist list - List blacklisted words.
"""

ACTIONS = ["delete", "warn", "ban", "kick", "mute"]

@Client.on_message(filters.command("blacklist") & filters.group)
@require_admin()
@error_handler
async def blacklist_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /blacklist <add/remove/list> [args]")
    
    subcmd = message.command[1].lower()
    
    if subcmd == "add":
        if len(message.command) < 3:
            return await message.reply_text("Usage: /blacklist add <word> [action]")
        
        word = message.command[2].lower()
        action = "delete"
        if len(message.command) > 3:
            req_action = message.command[3].lower()
            if req_action in ACTIONS:
                action = req_action
            else:
                return await message.reply_text(f"Invalid action. Available: {', '.join(ACTIONS)}")
        
        await db.add_blacklist(message.chat.id, word, action)
        await message.reply_text(f"Added '{word}' to blacklist with action: {action}")
        
    elif subcmd == "remove":
        if len(message.command) < 3:
            return await message.reply_text("Usage: /blacklist remove <word>")
            
        word = message.command[2].lower()
        await db.remove_blacklist(message.chat.id, word)
        await message.reply_text(f"Removed '{word}' from blacklist.")
        
    elif subcmd == "list":
        blacklist = await db.get_blacklist(message.chat.id)
        if not blacklist:
            return await message.reply_text("Blacklist is empty.")
            
        text = "**Blacklist:**\n"
        for word, action in blacklist.items():
            text += f"- `{word}` ({action})\n"
        await message.reply_text(text)

@Client.on_message(filters.text & filters.group, group=5)
async def check_blacklist(client: Client, message: Message):
    if not message.text:
        return
        
    # Ignore commands
    if message.text.startswith("/"):
        return

    # Check for admins (API Call - optimize later with cache if needed)
    try:
        member = await message.chat.get_member(message.from_user.id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return
    except Exception:
        pass # Failed to check status, proceed with check (safe fail) or return? Safe fail = check blacklist.

    blacklist = await db.get_blacklist(message.chat.id)
    if not blacklist:
        return

    text = message.text.lower()
    for word, action in blacklist.items():
        if word in text.split(): # Exact word match to avoid accidental substring triggers (e.g. 'hell' in 'hello')
            # The user reported 'hello' triggered. If they blacklist 'hello', it should match 'hello'.
            # Substring vs Word: The user likely wants substring if it's a slur, but word if common.
            # Let's stick to word boundary check for safety or raw 'in' if requested.
            # The previous implementation was `if word in text`.
            # User reported: "Hello!" in command triggered it.
            # Ignoring "/" fixes command trigger.
            # Let's use `word in text` for broad matching as requested implies.
            
            if word in text:
                try:
                    if action == "delete":
                        await message.delete()
                    elif action == "warn":
                        await message.delete()
                        count = await db.add_warn(message.chat.id, message.from_user.id, f"Blacklisted word: {word}")
                        await message.reply_text(f"{message.from_user.mention} warned for using blacklisted word '{word}'. ({count}/3)")
                        if count >= 3:
                            await client.ban_chat_member(message.chat.id, message.from_user.id)
                            await db.reset_warns(message.chat.id, message.from_user.id)
                            await message.reply_text(f"{message.from_user.mention} banned for max warnings.")
                            
                    elif action == "ban":
                        await message.delete()
                        await client.ban_chat_member(message.chat.id, message.from_user.id)
                        await message.reply_text(f"{message.from_user.mention} banned for using blacklisted word '{word}'.")
                        
                    elif action == "kick":
                        await message.delete()
                        await client.ban_chat_member(message.chat.id, message.from_user.id)
                        await client.unban_chat_member(message.chat.id, message.from_user.id)
                        await message.reply_text(f"{message.from_user.mention} kicked for using blacklisted word '{word}'.")
                        
                    elif action == "mute":
                        await message.delete()
                        await client.restrict_chat_member(message.chat.id, message.from_user.id, ChatPermissions())
                        await message.reply_text(f"{message.from_user.mention} muted for using blacklisted word '{word}'.")
                        
                    break 
                except Exception:
                    pass
