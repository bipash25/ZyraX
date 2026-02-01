import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from zyrax.utils.errors import error_handler
import yt_dlp

__mod_name__ = "Music"
__help__ = """
/play <query/url> - Play music
/stop - Stop playback and leave
/pause - Pause playback
/resume - Resume playback
/skip - Skip to next track
"""

# Queue: {chat_id: [{"title": ..., "file": ..., "user": ...}]}
QUEUES = {}

def get_audio_url(query):
    # Search or URL
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'outtmpl': 'downloads/%(id)s.%(ext)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{query}" if not query.startswith("http") else query, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            return {
                "file": ydl.prepare_filename(info),
                "title": info.get("title", "Unknown"),
                "duration": info.get("duration", 0)
            }
        except Exception as e:
            return None

@Client.on_message(filters.command("play") & filters.group)
@error_handler
async def play(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /play <query/url>")
    
    query = " ".join(message.command[1:])
    m = await message.reply_text("🔍 Searching...")
    
    # Run download in thread
    loop = asyncio.get_running_loop()
    track_info = await loop.run_in_executor(None, get_audio_url, query)
    
    if not track_info:
        return await m.edit_text("❌ No results found or download failed.")
        
    chat_id = message.chat.id
    
    # Add to queue
    if chat_id not in QUEUES:
        QUEUES[chat_id] = []
    
    QUEUES[chat_id].append(track_info)
    
    call_client: PyTgCalls = client.call_client
    
    # Check if already playing
    # We can check by seeing if chat_id is in call_client.active_calls? 
    # Or just try to play.
    # Note: active_calls is a list of Call objects or similar in v1.
    
    # Simple logic: If queue was empty (now len 1), start playing.
    if len(QUEUES[chat_id]) == 1:
        await start_playback(client, chat_id, track_info, m)
    else:
        await m.edit_text(f"📝 Added to queue: **{track_info['title']}** (#{len(QUEUES[chat_id])})")

async def start_playback(client, chat_id, track, message_obj=None):
    call_client: PyTgCalls = client.call_client
    
    try:
        await call_client.play(
            chat_id,
            MediaStream(
                track["file"],
            )
        )
        if message_obj:
            await message_obj.edit_text(f"▶️ Now Playing: **{track['title']}**")
        else:
            await client.send_message(chat_id, f"▶️ Now Playing: **{track['title']}**")
            
    except Exception as e:
        if message_obj:
            await message_obj.edit_text(f"Error playing: {e}")
        # Clean up queue if fail
        if chat_id in QUEUES:
            QUEUES[chat_id].pop(0)

@Client.on_message(filters.command("stop") & filters.group)
async def stop(client: Client, message: Message):
    chat_id = message.chat.id
    call_client: PyTgCalls = client.call_client
    
    try:
        await call_client.leave_call(chat_id)
        if chat_id in QUEUES:
            # Clean up files
            for track in QUEUES[chat_id]:
                if os.path.exists(track["file"]):
                    try: os.remove(track["file"])
                    except: pass
            del QUEUES[chat_id]
            
        await message.reply_text("⏹ Stopped playback.")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@Client.on_message(filters.command("pause") & filters.group)
async def pause(client: Client, message: Message):
    call_client: PyTgCalls = client.call_client
    try:
        await call_client.pause_stream(message.chat.id)
        await message.reply_text("⏸ Paused.")
    except:
        await message.reply_text("Nothing playing.")

@Client.on_message(filters.command("resume") & filters.group)
async def resume(client: Client, message: Message):
    call_client: PyTgCalls = client.call_client
    try:
        await call_client.resume_stream(message.chat.id)
        await message.reply_text("▶️ Resumed.")
    except:
        await message.reply_text("Nothing paused.")

@Client.on_message(filters.command("skip") & filters.group)
async def skip(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in QUEUES or not QUEUES[chat_id]:
        return await message.reply_text("Queue is empty.")
    
    # Remove current track
    old_track = QUEUES[chat_id].pop(0)
    # Delete file
    if os.path.exists(old_track["file"]):
        try: os.remove(old_track["file"])
        except: pass
        
    if not QUEUES[chat_id]:
        await client.call_client.leave_call(chat_id)
        return await message.reply_text("Skipped. End of queue.")
        
    next_track = QUEUES[chat_id][0]
    await message.reply_text(f"Skipped. Next: {next_track['title']}")
    await start_playback(client, chat_id, next_track)
