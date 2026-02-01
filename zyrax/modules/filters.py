from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.utils.decorators import require_admin
from zyrax.database.mongo import db
from zyrax.utils.validators import InputValidator
from zyrax.utils.formatting import format_text, parse_buttons
import re

__mod_name__ = "Filters"
__help__ = """
/filter <keyword> - Save a filter (auto-reply)
/filter regex <pattern> - Save a regex filter
/stop <keyword> - Stop a filter
/filters - List all filters
"""

async def extract_content(message):
    # Same helper as notes (duplicate code, Todo: Move to utils)
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
    else:
         # For filter regex <pattern> <text>
         # message.text might be "/filter regex pattern text content"
         pass
         
    return data

@Client.on_message(filters.command("filter") & filters.group)
@require_admin()
async def save_filter(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /filter <keyword> (reply to message or provide text)")
    
    keyword = message.command[1] # Don't lower yet if regex
    is_regex = False
    
    if keyword.lower() == "regex":
        if len(message.command) < 3:
            return await message.reply_text("Usage: /filter regex <pattern> <reply>")
        keyword = message.command[2]
        is_regex = True
        
        # Validate regex
        try:
            re.compile(keyword)
        except re.error:
            return await message.reply_text("Invalid regex pattern.")
            
        # Extract content: reply or text
        if message.reply_to_message:
            data = await extract_content(message)
        elif len(message.command) > 3:
             data = {"type": "text", "content": message.text.split(None, 3)[3]}
        else:
            return await message.reply_text("Provide content.")
            
    else:
        # Normal filter
        keyword = InputValidator.sanitize_text(keyword.lower())
        if message.reply_to_message:
            data = await extract_content(message)
        elif len(message.command) > 2:
             data = {"type": "text", "content": message.text.split(None, 2)[2]}
        else:
            return await message.reply_text("Provide content.")

    if not data:
         return await message.reply_text("Provide content.")

    data["is_regex"] = is_regex
    await db.save_filter(message.chat.id, keyword, data)
    await message.reply_text(f"Saved {'regex ' if is_regex else ''}filter `{keyword}`.")

@Client.on_message(filters.command("stop") & filters.group)
@require_admin()
async def stop_filter(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /stop <keyword>")
    
    keyword = message.command[1] # Case sensitive for regex?
    # Try deleting exact match first
    deleted = await db.delete_filter(message.chat.id, keyword)
    if not deleted:
        # Try lower
        deleted = await db.delete_filter(message.chat.id, keyword.lower())
        
    if deleted:
        await message.reply_text(f"Stopped filter `{keyword}`.")
    else:
        await message.reply_text("Filter not found.")

@Client.on_message(filters.command("filters") & filters.group)
async def list_filters(client: Client, message: Message):
    filters_map = await db.get_chat_filters(message.chat.id)
    if not filters_map:
        return await message.reply_text("No filters in this chat.")
    
    text = "**Filters:**\n"
    for keyword, data in filters_map.items():
        if data.get("is_regex"):
             text += f"- `regex:{keyword}`\n"
        else:
             text += f"- `{keyword}`\n"
    await message.reply_text(text)

@Client.on_message(filters.group & filters.text & ~filters.command([]), group=1)
async def filter_watcher(client: Client, message: Message):
    # Optimization: Cache filters per chat (DB layer handles some cache)
    chat_filters = await db.get_chat_filters(message.chat.id)
    if not chat_filters:
        return

    text = message.text # Keep case for regex, lower for normal
    text_lower = text.lower()
    
    match_data = None
    
    for keyword, data in chat_filters.items():
        if data.get("is_regex"):
            try:
                if re.search(keyword, text):
                    match_data = data
                    break
            except:
                continue
        else:
             # Exact match word (simple)
             if keyword in text_lower.split():
                 match_data = data
                 break
    
    if match_data:
        # Formatting
        content = match_data.get("content", "") or match_data.get("caption", "")
        formatted_content = await format_text(content, message.from_user, message.chat)
        text_final, markup = parse_buttons(formatted_content)
        
        if match_data["type"] == "text":
            await message.reply_text(text_final, reply_markup=markup)
        elif match_data["type"] == "media":
            await send_cached_media(message, match_data, text_final, markup)

async def send_cached_media(message, data, caption, markup):
    if data["media_type"] == "photo":
        await message.reply_photo(data["file_id"], caption=caption, reply_markup=markup)
    elif data["media_type"] == "video":
        await message.reply_video(data["file_id"], caption=caption, reply_markup=markup)
    elif data["media_type"] == "document":
        await message.reply_document(data["file_id"], caption=caption, reply_markup=markup)
    elif data["media_type"] == "sticker":
        await message.reply_sticker(data["file_id"], reply_markup=markup)
    elif data["media_type"] == "audio":
        await message.reply_audio(data["file_id"], caption=caption, reply_markup=markup)
    elif data["media_type"] == "voice":
        await message.reply_voice(data["file_id"], caption=caption, reply_markup=markup)
    elif data["media_type"] == "animation":
        await message.reply_animation(data["file_id"], caption=caption, reply_markup=markup)
