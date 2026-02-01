import os
import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from zyrax.utils.errors import error_handler
import yt_dlp

__mod_name__ = "Music"
__help__ = """
**Playback:**
/play <query/url> - Play music
/stop - Stop playback and leave
/pause - Pause playback
/resume - Resume playback
/skip - Skip to next track

**Queue:**
/queue - Show current queue
/nowplaying - Show currently playing track
/remove <number> - Remove track from queue
/clear - Clear the queue

**Radio Streams:**
/radio <station> - Play radio station
/stations - List available stations
/stopradio - Stop radio playback

**Info:**
/lyrics <song> - Search for lyrics
"""

# Queue: {chat_id: [{"title": ..., "file": ..., "duration": ...}]}
QUEUES = {}
NOW_PLAYING = {}  # {chat_id: {"title": ..., "started": timestamp}}

def get_audio_url(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'outtmpl': 'zyrax/downloads/%(id)s.%(ext)s',
    }
    
    # Ensure downloads directory exists
    os.makedirs('zyrax/downloads', exist_ok=True)
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{query}" if not query.startswith("http") else query, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            return {
                "file": ydl.prepare_filename(info),
                "title": info.get("title", "Unknown"),
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail", ""),
                "channel": info.get("channel", "Unknown")
            }
        except Exception as e:
            return None

def format_duration(seconds):
    if not seconds:
        return "Unknown"
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    if hours:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"

@Client.on_message(filters.command("play") & filters.group)
@error_handler
async def play(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /play <query/url>")
    
    query = " ".join(message.command[1:])
    m = await message.reply_text("Searching...")
    
    loop = asyncio.get_running_loop()
    track_info = await loop.run_in_executor(None, get_audio_url, query)
    
    if not track_info:
        return await m.edit_text("No results found or download failed.")
        
    chat_id = message.chat.id
    track_info["requester"] = message.from_user.first_name
    
    if chat_id not in QUEUES:
        QUEUES[chat_id] = []
    
    QUEUES[chat_id].append(track_info)
    
    call_client: PyTgCalls = client.call_client
    
    if len(QUEUES[chat_id]) == 1:
        await start_playback(client, chat_id, track_info, m)
    else:
        pos = len(QUEUES[chat_id])
        await m.edit_text(
            f"**Added to Queue** (#{pos})\n\n"
            f"**Title:** {track_info['title']}\n"
            f"**Duration:** {format_duration(track_info['duration'])}\n"
            f"**Requested by:** {track_info['requester']}"
        )

async def start_playback(client, chat_id, track, message_obj=None):
    import time
    call_client: PyTgCalls = client.call_client
    
    try:
        await call_client.play(
            chat_id,
            MediaStream(track["file"])
        )
        
        NOW_PLAYING[chat_id] = {
            "title": track["title"],
            "duration": track["duration"],
            "started": time.time(),
            "requester": track.get("requester", "Unknown")
        }
        
        text = (
            f"**Now Playing**\n\n"
            f"**Title:** {track['title']}\n"
            f"**Duration:** {format_duration(track['duration'])}\n"
            f"**Requested by:** {track.get('requester', 'Unknown')}"
        )
        
        if message_obj:
            await message_obj.edit_text(text)
        else:
            await client.send_message(chat_id, text)
            
    except Exception as e:
        if message_obj:
            await message_obj.edit_text(f"Error playing: {e}")
        if chat_id in QUEUES and QUEUES[chat_id]:
            QUEUES[chat_id].pop(0)

@Client.on_message(filters.command("stop") & filters.group)
async def stop(client: Client, message: Message):
    chat_id = message.chat.id
    call_client: PyTgCalls = client.call_client
    
    try:
        await call_client.leave_call(chat_id)
        if chat_id in QUEUES:
            for track in QUEUES[chat_id]:
                if os.path.exists(track["file"]):
                    try: os.remove(track["file"])
                    except: pass
            del QUEUES[chat_id]
        
        if chat_id in NOW_PLAYING:
            del NOW_PLAYING[chat_id]
            
        await message.reply_text("Stopped playback.")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@Client.on_message(filters.command("pause") & filters.group)
async def pause(client: Client, message: Message):
    call_client: PyTgCalls = client.call_client
    try:
        await call_client.pause_stream(message.chat.id)
        await message.reply_text("Paused.")
    except:
        await message.reply_text("Nothing playing.")

@Client.on_message(filters.command("resume") & filters.group)
async def resume(client: Client, message: Message):
    call_client: PyTgCalls = client.call_client
    try:
        await call_client.resume_stream(message.chat.id)
        await message.reply_text("Resumed.")
    except:
        await message.reply_text("Nothing paused.")

@Client.on_message(filters.command("skip") & filters.group)
async def skip(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in QUEUES or not QUEUES[chat_id]:
        return await message.reply_text("Queue is empty.")
    
    old_track = QUEUES[chat_id].pop(0)
    if os.path.exists(old_track["file"]):
        try: os.remove(old_track["file"])
        except: pass
        
    if not QUEUES[chat_id]:
        await client.call_client.leave_call(chat_id)
        if chat_id in NOW_PLAYING:
            del NOW_PLAYING[chat_id]
        return await message.reply_text("Skipped. Queue is empty.")
        
    next_track = QUEUES[chat_id][0]
    await message.reply_text(f"Skipped. Next: **{next_track['title']}**")
    await start_playback(client, chat_id, next_track)


@Client.on_message(filters.command("queue") & filters.group)
async def show_queue(client: Client, message: Message):
    chat_id = message.chat.id
    
    if chat_id not in QUEUES or not QUEUES[chat_id]:
        return await message.reply_text("Queue is empty.")
    
    queue = QUEUES[chat_id]
    text = "**Queue:**\n\n"
    
    for i, track in enumerate(queue, 1):
        status = "Now" if i == 1 else str(i)
        text += f"**{status}.** {track['title']} ({format_duration(track['duration'])})\n"
        if i >= 10:
            remaining = len(queue) - 10
            if remaining > 0:
                text += f"\n... and {remaining} more"
            break
    
    await message.reply_text(text)


@Client.on_message(filters.command("nowplaying") & filters.group)
async def now_playing(client: Client, message: Message):
    chat_id = message.chat.id
    
    if chat_id not in NOW_PLAYING:
        return await message.reply_text("Nothing is currently playing.")
    
    import time
    info = NOW_PLAYING[chat_id]
    elapsed = int(time.time() - info["started"])
    
    text = (
        f"**Now Playing**\n\n"
        f"**Title:** {info['title']}\n"
        f"**Duration:** {format_duration(elapsed)} / {format_duration(info['duration'])}\n"
        f"**Requested by:** {info['requester']}"
    )
    
    await message.reply_text(text)


@Client.on_message(filters.command("remove") & filters.group)
async def remove_from_queue(client: Client, message: Message):
    chat_id = message.chat.id
    
    if len(message.command) < 2:
        return await message.reply_text("Usage: /remove <position>")
    
    try:
        pos = int(message.command[1])
    except ValueError:
        return await message.reply_text("Invalid position.")
    
    if chat_id not in QUEUES or pos < 2 or pos > len(QUEUES[chat_id]):
        return await message.reply_text("Invalid position. Cannot remove currently playing track.")
    
    removed = QUEUES[chat_id].pop(pos - 1)
    if os.path.exists(removed["file"]):
        try: os.remove(removed["file"])
        except: pass
    
    await message.reply_text(f"Removed: **{removed['title']}**")


@Client.on_message(filters.command("clear") & filters.group)
async def clear_queue(client: Client, message: Message):
    chat_id = message.chat.id
    
    if chat_id not in QUEUES or len(QUEUES[chat_id]) <= 1:
        return await message.reply_text("Queue is already empty.")
    
    # Keep only the current track
    current = QUEUES[chat_id][0] if QUEUES[chat_id] else None
    
    for track in QUEUES[chat_id][1:]:
        if os.path.exists(track["file"]):
            try: os.remove(track["file"])
            except: pass
    
    QUEUES[chat_id] = [current] if current else []
    await message.reply_text("Queue cleared.")


@Client.on_message(filters.command("lyrics"))
@error_handler
async def lyrics_search(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /lyrics <song name>")
    
    query = " ".join(message.command[1:])
    m = await message.reply_text("Searching for lyrics...")
    
    # Use lyrics.ovh API (free, no auth)
    try:
        # First try to parse "Artist - Song" format
        if " - " in query:
            artist, song = query.split(" - ", 1)
        else:
            # Use the query as song name with empty artist
            artist = ""
            song = query
        
        async with aiohttp.ClientSession() as session:
            url = f"https://api.lyrics.ovh/v1/{artist}/{song}"
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    lyrics = data.get("lyrics", "")
                    
                    if lyrics:
                        # Truncate if too long
                        if len(lyrics) > 4000:
                            lyrics = lyrics[:4000] + "\n\n... (truncated)"
                        
                        await m.edit_text(f"**Lyrics for:** {query}\n\n{lyrics}")
                    else:
                        await m.edit_text("No lyrics found.")
                else:
                    await m.edit_text("Lyrics not found. Try: /lyrics Artist - Song")
    except Exception as e:
        await m.edit_text(f"Error searching lyrics: {e}")


# ===== RADIO STREAMS =====
RADIO_STATIONS = {
    "lofi": {
        "name": "Lofi Hip Hop",
        "url": "https://streams.ilovemusic.de/iloveradio17.mp3",
        "genre": "Chill"
    },
    "jazz": {
        "name": "Smooth Jazz",
        "url": "https://strw3.openstream.co/654?aw_0_1st.collession=default",
        "genre": "Jazz"
    },
    "classical": {
        "name": "Classical Radio",
        "url": "https://live.musopen.org:8085/streamvbr0",
        "genre": "Classical"
    },
    "pop": {
        "name": "Pop Hits",
        "url": "https://streams.ilovemusic.de/iloveradio1.mp3",
        "genre": "Pop"
    },
    "rock": {
        "name": "Rock Radio",
        "url": "https://streams.ilovemusic.de/iloveradio16.mp3",
        "genre": "Rock"
    },
    "electronic": {
        "name": "Electronic Beats",
        "url": "https://streams.ilovemusic.de/iloveradio2.mp3",
        "genre": "Electronic"
    },
    "hiphop": {
        "name": "Hip Hop Hits",
        "url": "https://streams.ilovemusic.de/iloveradio3.mp3",
        "genre": "Hip Hop"
    },
    "ambient": {
        "name": "Ambient Chill",
        "url": "https://ice2.somafm.com/dronezone-128-mp3",
        "genre": "Ambient"
    }
}

RADIO_PLAYING = {}  # {chat_id: station_key}


@Client.on_message(filters.command("stations") & filters.group)
async def list_stations(client: Client, message: Message):
    text = "**Available Radio Stations:**\n\n"
    
    for key, station in RADIO_STATIONS.items():
        text += f"**{station['name']}** (`{key}`)\n"
        text += f"  Genre: {station['genre']}\n\n"
    
    text += "\nUse: /radio <station_code>"
    await message.reply_text(text)


@Client.on_message(filters.command("radio") & filters.group)
@error_handler
async def radio_play(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "Usage: /radio <station>\n"
            "Use /stations to see available stations."
        )
    
    station_key = message.command[1].lower()
    
    if station_key not in RADIO_STATIONS:
        return await message.reply_text(
            f"Station `{station_key}` not found.\n"
            "Use /stations to see available stations."
        )
    
    station = RADIO_STATIONS[station_key]
    chat_id = message.chat.id
    
    m = await message.reply_text(f"Connecting to **{station['name']}**...")
    
    call_client: PyTgCalls = client.call_client
    
    try:
        # Stop any current playback
        if chat_id in QUEUES:
            for track in QUEUES[chat_id]:
                if os.path.exists(track.get("file", "")):
                    try:
                        os.remove(track["file"])
                    except:
                        pass
            del QUEUES[chat_id]
        
        if chat_id in NOW_PLAYING:
            del NOW_PLAYING[chat_id]
        
        # Start radio stream
        await call_client.play(
            chat_id,
            MediaStream(station["url"])
        )
        
        RADIO_PLAYING[chat_id] = station_key
        
        await m.edit_text(
            f"**Now Playing Radio**\n\n"
            f"Station: **{station['name']}**\n"
            f"Genre: {station['genre']}\n\n"
            f"Use /stopradio to stop."
        )
        
    except Exception as e:
        await m.edit_text(f"Error starting radio: {e}")


@Client.on_message(filters.command("stopradio") & filters.group)
async def stop_radio(client: Client, message: Message):
    chat_id = message.chat.id
    
    if chat_id not in RADIO_PLAYING:
        return await message.reply_text("No radio is currently playing.")
    
    call_client: PyTgCalls = client.call_client
    
    try:
        await call_client.leave_call(chat_id)
        del RADIO_PLAYING[chat_id]
        await message.reply_text("Radio stopped.")
    except Exception as e:
        await message.reply_text(f"Error stopping radio: {e}")
