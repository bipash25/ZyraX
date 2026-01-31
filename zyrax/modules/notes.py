from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.utils.decorators import require_admin
from zyrax.database.mongo import db

__mod_name__ = "Notes"
__help__ = """
/save <notename> - Save a note (reply to message)
/get <notename> - Get a note
/clear <notename> - Delete a note
/notes - List all notes
"""

@Client.on_message(filters.command("save") & filters.group)
@require_admin()
async def save_note(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /save <notename> (reply to message or provide text)")
    
    note_name = message.command[1].lower()
    
    # Check if reply or text
    if message.reply_to_message:
        # Saving a message (media or text)
        # For simplicity, we'll store the message ID and rely on Pyrogram to copy it later
        # OR better, store file_id and content.
        # Simplest approach for "copy" is just storing the message ID if it's not going to be deleted.
        # But if we want permanence, we should store content.
        # Pyrogram's `copy_message` is easiest if we assume the message stays.
        if message.reply_to_message.media:
            # It's media
            # This is complex to store fully generically in DB without just pickling or extensive JSONification
            # Strategy: Store message_id and link it to the chat? No, message might be deleted.
            # Strategy: Save file_id and caption.
            data = {
                "type": "media",
                "file_id": message.reply_to_message.sticker.file_id if message.reply_to_message.sticker else \
                           message.reply_to_message.photo.file_id if message.reply_to_message.photo else \
                           message.reply_to_message.video.file_id if message.reply_to_message.video else \
                           message.reply_to_message.document.file_id if message.reply_to_message.document else \
                           message.reply_to_message.voice.file_id if message.reply_to_message.voice else \
                           message.reply_to_message.audio.file_id if message.reply_to_message.audio else None,
                "caption": message.reply_to_message.caption or "",
                 # Store what kind of media it is
                "media_type": message.reply_to_message.media.value # simple string representation
            }
            # Refined strategy: Just use copy_message if possible, but for DB storage of "content", 
            # let's just support TEXT for now to keep it simple, or simple media.
            # Best way for robust bots: Use the message.reply_to_message_id and chat_id to copy. 
            # But if original message is deleted, the note breaks.
            # For this MVP, let's implement Text + basic File ID.
            pass # Improving below
        
        # Simplified storage logic:
        # We will iterate attributes to find file_id
        media_msg = message.reply_to_message
        file_id = None
        media_type = None
        
        if media_msg.text:
            data = {"type": "text", "content": media_msg.text}
        else:
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
            else:
                return await message.reply_text("Unsupported media type.")

    elif len(message.command) > 2:
        # /save name text content
        data = {"type": "text", "content": message.text.split(None, 2)[2]}
    else:
        return await message.reply_text("You need to provide content or reply to a message.")

    await db.save_note(message.chat.id, note_name, data)
    await message.reply_text(f"Saved note `{note_name}`.")

@Client.on_message(filters.command("get") & filters.group)
async def get_note_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /get <notename>")
    
    note_name = message.command[1].lower()
    await send_note(client, message, note_name)

@Client.on_message(filters.regex(r"^#(\w+)") & filters.group)
async def get_note_hashtag(client: Client, message: Message):
    note_name = message.matches[0].group(1).lower()
    await send_note(client, message, note_name)

async def send_note(client, message, note_name):
    note = await db.get_note(message.chat.id, note_name)
    if not note:
        return await message.reply_text("Note not found.")
    
    data = note["data"]
    if data["type"] == "text":
        await message.reply_text(data["content"])
    elif data["type"] == "media":
        # Send cached media
        if data["media_type"] == "photo":
            await message.reply_photo(data["file_id"], caption=data["caption"])
        elif data["media_type"] == "video":
            await message.reply_video(data["file_id"], caption=data["caption"])
        elif data["media_type"] == "document":
            await message.reply_document(data["file_id"], caption=data["caption"])
        elif data["media_type"] == "sticker":
            await message.reply_sticker(data["file_id"])
        elif data["media_type"] == "audio":
            await message.reply_audio(data["file_id"], caption=data["caption"])
        elif data["media_type"] == "voice":
            await message.reply_voice(data["file_id"], caption=data["caption"])
        elif data["media_type"] == "animation":
            await message.reply_animation(data["file_id"], caption=data["caption"])
        else:
            await message.reply_text("Unsupported media type in DB.")

@Client.on_message(filters.command("clear") & filters.group)
@require_admin()
async def clear_note(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /clear <notename>")
    
    note_name = message.command[1].lower()
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
