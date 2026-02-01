from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.config import Config
from zyrax.database.mongo import db
import aiohttp
import time
import google.generativeai as genai
import random
import asyncio
from functools import partial

__mod_name__ = "Automation"
__help__ = """
/schedule <time> <message> - Schedule a message (e.g. 10m Hello)
/rss add <url> - Add RSS feed
/rss list - List RSS feeds
/rss remove <url> - Remove RSS feed
"""

@Client.on_message(filters.command("schedule") & filters.group)
async def schedule_message(client: Client, message: Message):
    # This requires a persistent scheduler (APScheduler or custom loop)
    # For now, we'll store in DB and have a background task check every minute
    pass

@Client.on_message(filters.command("rss") & filters.group)
async def rss_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /rss <add/list/remove> [url]")
        
    subcmd = message.command[1].lower()
    if subcmd == "add":
        url = message.command[2]
        # Validate URL
        if not url.startswith("http"):
            return await message.reply_text("Invalid URL.")
            
        await db.add_rss(message.chat.id, url)
        await message.reply_text(f"Added RSS feed: {url}")
        
    elif subcmd == "list":
        feeds = await db.get_chat_rss(message.chat.id)
        if not feeds:
            return await message.reply_text("No RSS feeds.")
        await message.reply_text("**RSS Feeds:**\n" + "\n".join(feeds))
        
    elif subcmd == "remove":
        url = message.command[2]
        await db.remove_rss(message.chat.id, url)
        await message.reply_text("Removed RSS feed.")

def _check_toxicity_gemini(text: str):
    if not Config.GEMINI_API_KEYS:
        return False
    
    try:
        api_key = random.choice(Config.GEMINI_API_KEYS)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Prompt for moderation
        prompt = f"Analyze the following text for toxicity, hate speech, or explicit content. Reply with 'YES' if it violates safety standards, or 'NO' if it is safe. Text: \"{text}\""
        
        response = model.generate_content(prompt)
        answer = response.text.strip().upper().replace(".", "")
        return "YES" in answer
    except:
        return False

# Auto-Moderation (AI)
@Client.on_message(filters.text & filters.group, group=10)
async def ai_moderation(client: Client, message: Message):
    # Check if AI mod enabled for this chat
    settings = await db.get_chat_settings(message.chat.id)
    if not settings.get("ai_mod_enabled"):
        return

    text = message.text
    if len(text) < 5: 
        return

    # Use Gemini if keys available
    if Config.GEMINI_API_KEYS:
        loop = asyncio.get_running_loop()
        is_toxic = await loop.run_in_executor(None, partial(_check_toxicity_gemini, text))
        
        if is_toxic:
            try:
                await message.delete()
                # Optional: Send a temp message
                # m = await message.reply_text(f"{message.from_user.mention}, your message was removed (AI Detection).")
                # await asyncio.sleep(5)
                # await m.delete()
            except:
                pass
        return

    # Fallback to OpenAI Moderation API (Legacy/Alternative)
    if Config.OPENAI_API_KEY:
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {Config.OPENAI_API_KEY}"}
                async with session.post(
                    "https://api.openai.com/v1/moderations", 
                    headers=headers, 
                    json={"input": text}
                ) as resp:
                    result = await resp.json()
                    if result["results"][0]["flagged"]:
                        await message.delete()
        except:
            pass
