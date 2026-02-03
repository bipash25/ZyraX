from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.utils.decorators import require_admin
from zyrax.utils.errors import error_handler
from zyrax.database.mongo import db
from zyrax.utils.validators import InputValidator
from zyrax.utils.formatting import format_text, parse_buttons, extract_content, send_media

__mod_name__ = "Notes"
__help__ = """
/save <notename> - Save a note (reply to message)
/privatesave <notename> - Save a note that answers in PM
/get <notename> - Get a note
/clear <notename> - Delete a note
/notes - List all notes
#notename - Retrieve a note
"""

@Client.on_message(filters.command(["save", "privatesave"]) & filters.group)
@error_handler
@require_admin()
async def save_note(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /save <notename> (reply to message or provide text)")
    
    note_name = InputValidator.sanitize_text(message.command[1].lower())
    data = await extract_content(message)
    
    if not data:
        return await message.reply_text("You need to provide content or reply to a message.")
    
    # Check for private save
    if message.command[0] == "privatesave":
        data["is_private"] = True

    await db.save_note(message.chat.id, note_name, data)
    await message.reply_text(f"Saved note `{note_name}`.")

@Client.on_message(filters.command("get") & filters.group)
@error_handler
async def get_note_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /get <notename>")
    
    note_name = InputValidator.sanitize_text(message.command[1].lower())
    await send_note(client, message, note_name)

@Client.on_message(filters.regex(r"^#(\w+)") & filters.group)
@error_handler
async def get_note_hashtag(client: Client, message: Message):
    if not message.matches: return
    note_name = message.matches[0].group(1).lower()
    await send_note(client, message, note_name)

async def send_note(client: Client, message: Message, note_name: str):
    """Send a saved note to the chat or PM."""
    note = await db.get_note(message.chat.id, note_name)
    if not note:
        return
    
    data = note["data"]
    is_private = data.get("is_private", False)
    
    # Determine target chat
    if is_private:
        target_chat_id = message.from_user.id
        await message.reply_text(f"Sent note `{note_name}` to your PM!", quote=True)
    else:
        target_chat_id = message.chat.id

    # Format content with variables
    content = data.get("content", "") or data.get("caption", "")
    formatted_content = await format_text(content, message.from_user, message.chat)
    text_final, markup = parse_buttons(formatted_content)
    
    try:
        if data["type"] == "text":
            await client.send_message(target_chat_id, text_final, reply_markup=markup)
        elif data["type"] == "media":
            await send_media(client, target_chat_id, data, text_final, markup)
    except Exception as e:
        error_msg = "Failed to send PM" if is_private else "Error sending note"
        await message.reply_text(f"{error_msg}: {e}")

@Client.on_message(filters.command("clear") & filters.group)
@error_handler
@require_admin()
async def clear_note(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /clear <notename>")
    
    note_name = InputValidator.sanitize_text(message.command[1].lower())
    deleted = await db.delete_note(message.chat.id, note_name)
    if deleted:
        await message.reply_text(f"Deleted note `{note_name}`.")
    else:
        await message.reply_text("Note not found.")

@Client.on_message(filters.command("notes") & filters.group)
@error_handler
async def list_notes(client: Client, message: Message):
    notes = await db.get_all_notes(message.chat.id)
    if not notes:
        return await message.reply_text("No notes in this chat.")
    
    await message.reply_text(f"**Notes:**\n" + "\n".join([f"- `{n}`" for n in notes]))
