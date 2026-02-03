"""
ZyraX Music Module

Voice chat music playback with queue management and radio streams.
"""

import os
import asyncio
import time
from typing import Dict, List, Optional, Any

import aiohttp
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

from zyrax.utils.errors import error_handler
from zyrax.utils.ratelimit import rate_limit
from zyrax.constants import Limits, RADIO_STATIONS


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


# =============================================================================
# CONSTANTS
# =============================================================================

DOWNLOADS_DIR = "zyrax/downloads"
MAX_LYRICS_LENGTH = 4000
QUEUE_DISPLAY_LIMIT = 10


# =============================================================================
# STATE
# =============================================================================

# Queue: {chat_id: [{"title": ..., "file": ..., "duration": ...}]}
QUEUES: Dict[int, List[Dict[str, Any]]] = {}

# Now playing: {chat_id: {"title": ..., "started": timestamp}}
NOW_PLAYING: Dict[int, Dict[str, Any]] = {}

# Radio playing: {chat_id: station_key}
RADIO_PLAYING: Dict[int, str] = {}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_audio_url(query: str) -> Optional[Dict[str, Any]]:
    """Download audio from YouTube and return track info."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'outtmpl': f'{DOWNLOADS_DIR}/%(id)s.%(ext)s',
    }
    
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            search_query = query if query.startswith("http") else f"ytsearch:{query}"
            info = ydl.extract_info(search_query, download=True)
            
            if 'entries' in info:
                info = info['entries'][0]
                
            return {
                "file": ydl.prepare_filename(info),
                "title": info.get("title", "Unknown"),
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail", ""),
                "channel": info.get("channel", "Unknown")
            }
        except Exception:
            return None


def format_duration(seconds: Optional[int]) -> str:
    """Format seconds as MM:SS or HH:MM:SS."""
    if not seconds:
        return "Unknown"
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    if hours:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


def cleanup_track_file(track: Dict[str, Any]) -> None:
    """Remove downloaded file for a track."""
    file_path = track.get("file", "")
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass


def cleanup_queue(chat_id: int) -> None:
    """Clean up all tracks in a queue."""
    if chat_id in QUEUES:
        for track in QUEUES[chat_id]:
            cleanup_track_file(track)
        del QUEUES[chat_id]
    
    if chat_id in NOW_PLAYING:
        del NOW_PLAYING[chat_id]


# =============================================================================
# PLAYBACK COMMANDS
# =============================================================================

@Client.on_message(filters.command("play") & filters.group)
@rate_limit(max_attempts=5, window=60)
@error_handler
async def play(client: Client, message: Message):
    """Play a song from YouTube."""
    if len(message.command) < 2:
        return await message.reply_text("Usage: /play <query/url>")
    
    chat_id = message.chat.id
    
    # Check queue size limit
    if chat_id in QUEUES and len(QUEUES[chat_id]) >= Limits.MAX_QUEUE_SIZE:
        return await message.reply_text(
            f"Queue is full ({Limits.MAX_QUEUE_SIZE} tracks max). "
            "Remove some tracks or clear the queue."
        )
    
    query = " ".join(message.command[1:])
    msg = await message.reply_text("Searching...")
    
    loop = asyncio.get_running_loop()
    track_info = await loop.run_in_executor(None, get_audio_url, query)
    
    if not track_info:
        return await msg.edit_text("No results found or download failed.")
    
    track_info["requester"] = message.from_user.first_name
    
    if chat_id not in QUEUES:
        QUEUES[chat_id] = []
    
    QUEUES[chat_id].append(track_info)
    
    if len(QUEUES[chat_id]) == 1:
        await start_playback(client, chat_id, track_info, msg)
    else:
        pos = len(QUEUES[chat_id])
        await msg.edit_text(
            f"**Added to Queue** (#{pos})\n\n"
            f"**Title:** {track_info['title']}\n"
            f"**Duration:** {format_duration(track_info['duration'])}\n"
            f"**Requested by:** {track_info['requester']}"
        )


async def start_playback(
    client: Client,
    chat_id: int,
    track: Dict[str, Any],
    message_obj: Optional[Message] = None
) -> None:
    """Start playing a track in voice chat."""
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
        # Remove failed track from queue
        if chat_id in QUEUES and QUEUES[chat_id]:
            QUEUES[chat_id].pop(0)


@Client.on_message(filters.command("stop") & filters.group)
@error_handler
async def stop(client: Client, message: Message):
    """Stop playback and leave voice chat."""
    chat_id = message.chat.id
    call_client: PyTgCalls = client.call_client
    
    try:
        await call_client.leave_call(chat_id)
        cleanup_queue(chat_id)
        await message.reply_text("Stopped playback.")
    except Exception as e:
        await message.reply_text(f"Error: {e}")


@Client.on_message(filters.command("pause") & filters.group)
@error_handler
async def pause(client: Client, message: Message):
    """Pause current playback."""
    call_client: PyTgCalls = client.call_client
    try:
        await call_client.pause_stream(message.chat.id)
        await message.reply_text("Paused.")
    except Exception:
        await message.reply_text("Nothing playing.")


@Client.on_message(filters.command("resume") & filters.group)
@error_handler
async def resume(client: Client, message: Message):
    """Resume paused playback."""
    call_client: PyTgCalls = client.call_client
    try:
        await call_client.resume_stream(message.chat.id)
        await message.reply_text("Resumed.")
    except Exception:
        await message.reply_text("Nothing paused.")


@Client.on_message(filters.command("skip") & filters.group)
@error_handler
async def skip(client: Client, message: Message):
    """Skip to the next track in queue."""
    chat_id = message.chat.id
    
    if chat_id not in QUEUES or not QUEUES[chat_id]:
        return await message.reply_text("Queue is empty.")
    
    old_track = QUEUES[chat_id].pop(0)
    cleanup_track_file(old_track)
    
    if not QUEUES[chat_id]:
        await client.call_client.leave_call(chat_id)
        if chat_id in NOW_PLAYING:
            del NOW_PLAYING[chat_id]
        return await message.reply_text("Skipped. Queue is empty.")
    
    next_track = QUEUES[chat_id][0]
    await message.reply_text(f"Skipped. Next: **{next_track['title']}**")
    await start_playback(client, chat_id, next_track)


# =============================================================================
# QUEUE COMMANDS
# =============================================================================

@Client.on_message(filters.command("queue") & filters.group)
@error_handler
async def show_queue(client: Client, message: Message):
    """Show the current queue."""
    chat_id = message.chat.id
    
    if chat_id not in QUEUES or not QUEUES[chat_id]:
        return await message.reply_text("Queue is empty.")
    
    queue = QUEUES[chat_id]
    text = "**Queue:**\n\n"
    
    for i, track in enumerate(queue[:QUEUE_DISPLAY_LIMIT], 1):
        status = "Now" if i == 1 else str(i)
        text += f"**{status}.** {track['title']} ({format_duration(track['duration'])})\n"
    
    remaining = len(queue) - QUEUE_DISPLAY_LIMIT
    if remaining > 0:
        text += f"\n... and {remaining} more"
    
    await message.reply_text(text)


@Client.on_message(filters.command("nowplaying") & filters.group)
@error_handler
async def now_playing(client: Client, message: Message):
    """Show currently playing track."""
    chat_id = message.chat.id
    
    if chat_id not in NOW_PLAYING:
        return await message.reply_text("Nothing is currently playing.")
    
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
@error_handler
async def remove_from_queue(client: Client, message: Message):
    """Remove a track from the queue by position."""
    chat_id = message.chat.id
    
    if len(message.command) < 2:
        return await message.reply_text("Usage: /remove <position>")
    
    try:
        pos = int(message.command[1])
    except ValueError:
        return await message.reply_text("Invalid position.")
    
    if chat_id not in QUEUES or pos < 2 or pos > len(QUEUES[chat_id]):
        return await message.reply_text(
            "Invalid position. Cannot remove currently playing track."
        )
    
    removed = QUEUES[chat_id].pop(pos - 1)
    cleanup_track_file(removed)
    
    await message.reply_text(f"Removed: **{removed['title']}**")


@Client.on_message(filters.command("clearqueue") & filters.group)
@error_handler
async def clear_queue(client: Client, message: Message):
    """Clear the queue (keep current track)."""
    chat_id = message.chat.id
    
    if chat_id not in QUEUES or len(QUEUES[chat_id]) <= 1:
        return await message.reply_text("Queue is already empty.")
    
    # Keep only the current track
    current = QUEUES[chat_id][0] if QUEUES[chat_id] else None
    
    for track in QUEUES[chat_id][1:]:
        cleanup_track_file(track)
    
    QUEUES[chat_id] = [current] if current else []
    await message.reply_text("Queue cleared.")


# =============================================================================
# LYRICS
# =============================================================================

@Client.on_message(filters.command("lyrics"))
@rate_limit(max_attempts=5, window=60)
@error_handler
async def lyrics_search(client: Client, message: Message):
    """Search for song lyrics."""
    if len(message.command) < 2:
        return await message.reply_text("Usage: /lyrics <song name>")
    
    query = " ".join(message.command[1:])
    msg = await message.reply_text("Searching for lyrics...")
    
    try:
        # Parse "Artist - Song" format
        if " - " in query:
            artist, song = query.split(" - ", 1)
        else:
            artist = ""
            song = query
        
        async with aiohttp.ClientSession() as session:
            url = f"https://api.lyrics.ovh/v1/{artist}/{song}"
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    lyrics = data.get("lyrics", "")
                    
                    if lyrics:
                        if len(lyrics) > MAX_LYRICS_LENGTH:
                            lyrics = lyrics[:MAX_LYRICS_LENGTH] + "\n\n... (truncated)"
                        
                        await msg.edit_text(f"**Lyrics for:** {query}\n\n{lyrics}")
                    else:
                        await msg.edit_text("No lyrics found.")
                else:
                    await msg.edit_text("Lyrics not found. Try: /lyrics Artist - Song")
                    
    except Exception as e:
        await msg.edit_text(f"Error searching lyrics: {e}")


# =============================================================================
# RADIO STREAMS
# =============================================================================

@Client.on_message(filters.command("stations") & filters.group)
@error_handler
async def list_stations(client: Client, message: Message):
    """List available radio stations."""
    text = "**Available Radio Stations:**\n\n"
    
    for key, station in RADIO_STATIONS.items():
        text += f"**{station['name']}** (`{key}`)\n"
        text += f"  Genre: {station['genre']}\n\n"
    
    text += "\nUse: /radio <station_code>"
    await message.reply_text(text)


@Client.on_message(filters.command("radio") & filters.group)
@error_handler
async def radio_play(client: Client, message: Message):
    """Play a radio station."""
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
    
    msg = await message.reply_text(f"Connecting to **{station['name']}**...")
    
    call_client: PyTgCalls = client.call_client
    
    try:
        # Clean up any existing playback
        cleanup_queue(chat_id)
        
        # Start radio stream
        await call_client.play(
            chat_id,
            MediaStream(station["url"])
        )
        
        RADIO_PLAYING[chat_id] = station_key
        
        await msg.edit_text(
            f"**Now Playing Radio**\n\n"
            f"Station: **{station['name']}**\n"
            f"Genre: {station['genre']}\n\n"
            f"Use /stopradio to stop."
        )
        
    except Exception as e:
        await msg.edit_text(f"Error starting radio: {e}")


@Client.on_message(filters.command("stopradio") & filters.group)
@error_handler
async def stop_radio(client: Client, message: Message):
    """Stop radio playback."""
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
