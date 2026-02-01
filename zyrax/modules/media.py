import aiohttp
import os
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.utils.errors import error_handler
from zyrax.utils.ratelimit import rate_limit

__mod_name__ = "Media"
__help__ = """
/tosticker - Convert image to sticker
/dl <url> - Download media from URL (Youtube/Insta/etc)
"""

@Client.on_message(filters.command("tosticker") & filters.group)
@error_handler
async def tosticker(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply_text("Reply to an image.")
    
    msg = await message.reply_text("Converting...")
    path = await message.reply_to_message.download("sticker.png")
    
    try:
        # Resize using Pillow? Telegram requires specific dimensions.
        # But wait, send_sticker handles pngs. Let's just try sending.
        # Ideally we resize to 512x512.
        from PIL import Image
        img = Image.open(path)
        img.thumbnail((512, 512))
        img.save(path, "PNG")
        
        await message.reply_sticker(path)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"Error: {e}")
    finally:
        if os.path.exists(path):
            os.remove(path)

@Client.on_message(filters.command("dl") & filters.group)
@rate_limit(max_attempts=1, window=60)
@error_handler
async def download_media(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /dl <url>")
    
    url = message.command[1]
    msg = await message.reply_text("Downloading... This may take a while.")
    
    # Use yt-dlp
    import yt_dlp
    
    timestamp = int(time.time())
    output_template = f"downloads/{timestamp}.%(ext)s"
    
    ydl_opts = {
        'outtmpl': output_template,
        'max_filesize': 50 * 1024 * 1024, # 50MB limit for bot
        'format': 'best',
        'noplaylist': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
        await message.reply_video(filename, caption=f"Downloaded: {info.get('title', 'video')}")
        await msg.delete()
        os.remove(filename)
        
    except Exception as e:
        await msg.edit_text(f"Download failed: {str(e)}")
