from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.utils.decorators import require_admin
from zyrax.utils.errors import error_handler
from zyrax.database.mongo import db
from zyrax.utils.validators import InputValidator
from zyrax.utils.formatting import format_text, parse_buttons, extract_content, reply_media
import re
from datetime import datetime

__mod_name__ = "Filters"
__help__ = """
**Filter Commands:**
/filter <keyword> - Save a filter (reply to message or provide text)
/filter regex <pattern> - Save a regex filter
/stop <keyword> - Stop a filter
/filters - List all filters
/filterstats - Show filter hit statistics

**Button Syntax in filters:**
Use [Button Text](buttonurl://example.com) to add buttons

**Variables:**
{first} - User's first name
{last} - User's last name
{mention} - User mention
{username} - Username
{chatname} - Chat name
"""

@Client.on_message(filters.command("filter") & filters.group)
@error_handler
@require_admin()
async def save_filter(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /filter <keyword> (reply to message or provide text)")
    
    keyword = message.command[1]
    is_regex = False
    
    if keyword.lower() == "regex":
        if len(message.command) < 3:
            return await message.reply_text("Usage: /filter regex <pattern> <reply>")
        keyword = message.command[2]
        is_regex = True
        
        try:
            re.compile(keyword)
        except re.error:
            return await message.reply_text("Invalid regex pattern.")
            
        if message.reply_to_message:
            data = await extract_content(message)
        elif len(message.command) > 3:
             data = {"type": "text", "content": message.text.split(None, 3)[3]}
        else:
            return await message.reply_text("Provide content.")
            
    else:
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
@error_handler
@require_admin()
async def stop_filter(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /stop <keyword>")
    
    keyword = message.command[1]
    deleted = await db.delete_filter(message.chat.id, keyword)
    if not deleted:
        deleted = await db.delete_filter(message.chat.id, keyword.lower())
        
    if deleted:
        await message.reply_text(f"Stopped filter `{keyword}`.")
    else:
        await message.reply_text("Filter not found.")

@Client.on_message(filters.command("filters") & filters.group)
@error_handler
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


@Client.on_message(filters.command("filterstats") & filters.group)
@error_handler
@require_admin()
async def filter_stats(client: Client, message: Message):
    """Show filter hit statistics"""
    stats = await db.get_filter_stats(message.chat.id)
    
    if not stats:
        return await message.reply_text("No filter stats available yet.")
    
    text = "**Filter Statistics:**\n\n"
    for stat in stats[:15]:  # Top 15
        last_hit = datetime.fromtimestamp(stat.get("last_hit", 0)).strftime("%m/%d %H:%M")
        text += f"- `{stat['filter']}`: {stat['hits']} hits (last: {last_hit})\n"
    
    await message.reply_text(text)


@Client.on_message(filters.group & filters.text & ~filters.command([]), group=1)
async def filter_watcher(client: Client, message: Message):
    """Watch for filter triggers in messages."""
    chat_filters = await db.get_chat_filters(message.chat.id)
    if not chat_filters:
        return

    text = message.text
    text_lower = text.lower()
    
    matched_keyword = None
    match_data = None
    
    for keyword, data in chat_filters.items():
        if data.get("is_regex"):
            try:
                if re.search(keyword, text):
                    matched_keyword = keyword
                    match_data = data
                    break
            except re.error:
                continue
        else:
            if keyword in text_lower.split():
                matched_keyword = keyword
                match_data = data
                break
    
    if match_data and matched_keyword:
        # Track filter stats
        await db.increment_filter_stats(message.chat.id, matched_keyword)
        
        # Format content with variables
        content = match_data.get("content", "") or match_data.get("caption", "")
        formatted_content = await format_text(content, message.from_user, message.chat)
        text_final, markup = parse_buttons(formatted_content)
        
        if match_data["type"] == "text":
            await message.reply_text(text_final, reply_markup=markup)
        elif match_data["type"] == "media":
            await reply_media(message, match_data, text_final, markup)
