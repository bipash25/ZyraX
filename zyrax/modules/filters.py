from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.utils.decorators import require_admin
from zyrax.database.mongo import db
from zyrax.utils.validators import InputValidator

__mod_name__ = "Filters"
__help__ = """
/filter <keyword> - Save a filter (auto-reply)
/stop <keyword> - Stop a filter
"""

@Client.on_message(filters.command("filter") & filters.group)
@require_admin()
async def save_filter(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /filter <keyword> (reply to message or provide text)")
    
    keyword = InputValidator.sanitize_text(message.command[1].lower())
    
    # Check if reply or text (Reusing logic from notes, should refactor eventually)
    if message.reply_to_message:
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
         data = {"type": "text", "content": InputValidator.sanitize_text(message.text.split(None, 2)[2])}
    else:
        return await message.reply_text("You need to provide content or reply to a message.")

    await db.save_filter(message.chat.id, keyword, data)
    await message.reply_text(f"Saved filter `{keyword}`.")

@Client.on_message(filters.command("stop") & filters.group)
@require_admin()
async def stop_filter(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /stop <keyword>")
    
    keyword = InputValidator.sanitize_text(message.command[1].lower())
    deleted = await db.delete_filter(message.chat.id, keyword)
    if deleted:
        await message.reply_text(f"Stopped filter `{keyword}`.")
    else:
        await message.reply_text("Filter not found.")

@Client.on_message(filters.group & filters.text & ~filters.command([]), group=1)
async def filter_watcher(client: Client, message: Message):
    # This comes after commands, but checks every text message
    # Optimization: Cache filters per chat
    chat_filters = await db.get_chat_filters(message.chat.id)
    if not chat_filters:
        return

    text = message.text.lower()
    for keyword, data in chat_filters.items():
        if keyword in text.split(): # Simple exact match on word basis
            if data["type"] == "text":
                await message.reply_text(data["content"])
            elif data["type"] == "media":
                await send_cached_media(message, data)

async def send_cached_media(message, data):
     # Same helper as notes (duplicate code, Todo: Move to utils)
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
