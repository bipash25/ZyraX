import uuid
from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.utils.decorators import require_admin
from zyrax.database.mongo import db

__mod_name__ = "Federations"
__help__ = """
/newfed <name> - Create a new federation
/joinfed <fed_id> - Join a federation
/leavefed - Leave current federation
/chatfed - Check current federation
/fban <user> <reason> - Fed Ban a user
/unfban <user> - Un-Fed Ban a user
"""

@Client.on_message(filters.command("newfed"))
async def new_fed(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /newfed <name>")
    
    name = message.command[1]
    fed_id = str(uuid.uuid4())
    
    success = await db.create_fed(message.from_user.id, name, fed_id)
    if success:
        # Auto-join creator's chat to the new fed
        await db.join_fed(fed_id, message.chat.id)
        await message.reply_text(f"Created federation '{name}' with ID: `{fed_id}`\nThis chat has joined the federation.")
    else:
        await message.reply_text("Federation name already exists.")

@Client.on_message(filters.command("joinfed") & filters.group)
@require_admin()
async def join_fed(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /joinfed <fed_id>")
    
    fed_id = message.command[1]
    fed = await db.get_fed(fed_id)
    if not fed:
        return await message.reply_text("Federation not found.")
    
    success = await db.join_fed(fed_id, message.chat.id)
    if success:
        await message.reply_text(f"This chat has joined federation '{fed['name']}'.")
    else:
        await message.reply_text("Failed to join federation.")

@Client.on_message(filters.command("leavefed") & filters.group)
@require_admin()
async def leave_fed(client: Client, message: Message):
    success = await db.leave_fed(message.chat.id)
    if success:
        await message.reply_text("Left the federation.")
    else:
        await message.reply_text("This chat is not in any federation.")

@Client.on_message(filters.command("fban"))
async def fban_user(client: Client, message: Message):
    # Only fed owner can fban for now, or promoted fed admins (todo)
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("Reply to user or provide ID to Fed Ban.")
    
    # Determine user
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        reason = " ".join(message.command[1:])
    else:
        try:
            user_id = int(message.command[1])
            reason = " ".join(message.command[2:])
        except:
             return await message.reply_text("Invalid user ID.")
             
    if not reason:
        reason = "No reason provided."

    # For MVP, assume user can only fban in their OWN fed
    # We need to find which fed the user owns
    # This logic is a bit flawed for generic admins, usually you specify which fed if you own multiple or default to chat's fed
    # Let's say: If run in a group, use that group's fed, and check if user is owner.
    
    chat_fed_id = await db.get_chat_fed_id(message.chat.id)
    if not chat_fed_id:
        return await message.reply_text("This chat is not in a federation.")
        
    fed = await db.get_fed(chat_fed_id)
    if fed["owner_id"] != message.from_user.id:
        # TODO: Add Fed Admin check
        return await message.reply_text("You must be the federation owner to FBan.")
    
    await db.fed_ban(chat_fed_id, user_id, reason)
    await message.reply_text(f"FedBanned user {user_id} in {fed['name']}. Reason: {reason}")

@Client.on_message(filters.command("unfban"))
async def unfban_user(client: Client, message: Message):
    # Similar logic to fban
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("Reply to user or provide ID to Un-Fed Ban.")
        
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        try:
            user_id = int(message.command[1])
        except:
             return await message.reply_text("Invalid user ID.")
    
    chat_fed_id = await db.get_chat_fed_id(message.chat.id)
    if not chat_fed_id:
        return await message.reply_text("This chat is not in a federation.")
        
    fed = await db.get_fed(chat_fed_id)
    if fed["owner_id"] != message.from_user.id:
        return await message.reply_text("You must be the federation owner to Un-FBan.")
        
    deleted = await db.fed_unban(chat_fed_id, user_id)
    if deleted:
        await message.reply_text(f"Un-FedBanned user {user_id}.")
    else:
        await message.reply_text("User was not fedbanned.")

@Client.on_message(filters.command("chatfed") & filters.group)
async def chat_fed(client: Client, message: Message):
    fed_id = await db.get_chat_fed_id(message.chat.id)
    if fed_id:
        fed = await db.get_fed(fed_id)
        await message.reply_text(f"This chat is part of federation: **{fed['name']}** (`{fed_id}`)")
    else:
        await message.reply_text("This chat is not in any federation.")

# Fed Ban Enforcer
@Client.on_message(filters.group & filters.new_chat_members)
async def fed_ban_check(client: Client, message: Message):
    chat_fed_id = await db.get_chat_fed_id(message.chat.id)
    if not chat_fed_id:
        return
        
    for member in message.new_chat_members:
        ban_info = await db.is_user_fedor_banned(chat_fed_id, member.id)
        if ban_info:
            try:
                await client.ban_chat_member(message.chat.id, member.id)
                await message.reply_text(f"Removed {member.mention} because they are FedBanned in current fed.\nReason: {ban_info.get('reason')}")
            except Exception:
                pass 
