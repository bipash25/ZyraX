from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from zyrax.utils.decorators import require_admin
from zyrax.database.mongo import db
from zyrax.utils.validators import InputValidator
from zyrax.utils.formatting import format_text, parse_buttons

__mod_name__ = "Notes"
__help__ = """
/save <notename> - Save a note (reply to message)
/privatesave <notename> - Save a note that answers in PM
/get <notename> - Get a note
/clear <notename> - Delete a note
/notes - List all notes
#notename - Retrieve a note
"""

async def extract_content(message):
    data = {}
    if message.reply_to_message:
        media_msg = message.reply_to_message
        if media_msg.text:
            data = {"type": "text", "content": media_msg.text}
        else:
            file_id = None
            media_type = None
            for attr in ["photo", "video", "audio", "voice", "document", "sticker", "animation"]:
                val = getattr(media_msg, attr, None)
                if val:
                    file_id = val.file_id
                    media_type = attr
                    break
            
            if file_id:
                data = {
                    "type": "media",
                    "media_type": media_type,
                    "file_id": file_id,
                    "caption": media_msg.caption or ""
                }
    elif len(message.command) > 2:
        data = {"type": "text", "content": message.text.split(None, 2)[2]}
    
    return data

@Client.on_message(filters.command(["save", "privatesave"]) & filters.group)
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
async def get_note_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /get <notename>")
    
    note_name = InputValidator.sanitize_text(message.command[1].lower())
    await send_note(client, message, note_name)

@Client.on_message(filters.regex(r"^#(\w+)") & filters.group)
async def get_note_hashtag(client: Client, message: Message):
    if not message.matches: return
    note_name = message.matches[0].group(1).lower()
    await send_note(client, message, note_name)

async def send_note(client, message, note_name):
    try:
        note = await db.get_note(message.chat.id, note_name)
        if not note:
            # Debug: Check if note exists with different casing or unescaped?
            # For now just return
            return 
        
        data = note["data"]
        is_private = data.get("is_private", False)
        
        # Target: PM or Group
        target_msg = message
        if is_private:
            # Try to send PM
            try:
                target_chat_id = message.from_user.id
                # Send notification in group
                await message.reply_text(f"Sent note `{note_name}` to your PM!", quote=True)
            except Exception:
                return await message.reply_text("I can't PM you! Start me first.")
        else:
            target_chat_id = message.chat.id

        # Formatting and Buttons
        content = data.get("content", "") or data.get("caption", "")
        
        # Format text variables
        formatted_content = await format_text(content, message.from_user, message.chat)
        
        # Parse buttons
        text_final, markup = parse_buttons(formatted_content)
        
        try:
            if data["type"] == "text":
                await client.send_message(target_chat_id, text_final, reply_markup=markup)
                
            elif data["type"] == "media":
                # Media types
                media_type = data["media_type"]
                file_id = data["file_id"]
                
                if media_type == "photo":
                    await client.send_photo(target_chat_id, file_id, caption=text_final, reply_markup=markup)
                elif media_type == "video":
                    await client.send_video(target_chat_id, file_id, caption=text_final, reply_markup=markup)
                elif media_type == "document":
                    await client.send_document(target_chat_id, file_id, caption=text_final, reply_markup=markup)
                elif media_type == "sticker":
                    await client.send_sticker(target_chat_id, file_id, reply_markup=markup)
                elif media_type == "audio":
                    await client.send_audio(target_chat_id, file_id, caption=text_final, reply_markup=markup)
                elif media_type == "voice":
                    await client.send_voice(target_chat_id, file_id, caption=text_final, reply_markup=markup)
                elif media_type == "animation":
                    await client.send_animation(target_chat_id, file_id, caption=text_final, reply_markup=markup)
                    
        except Exception as e:
            # Fallback if PM fails (e.g. user blocked bot)
            if is_private:
                 await message.reply_text(f"Failed to send PM: {e}")
            else:
                 await message.reply_text(f"Error sending note: {e}")
                 
    except Exception as e:
        await message.reply_text(f"Error in send_note: {e}")

@Client.on_message(filters.command("clear") & filters.group)
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
async def list_notes(client: Client, message: Message):
    notes = await db.get_all_notes(message.chat.id)
    if not notes:
        return await message.reply_text("No notes in this chat.")
    
    await message.reply_text(f"**Notes:**\n" + "\n".join([f"- `{n}`" for n in notes]))
