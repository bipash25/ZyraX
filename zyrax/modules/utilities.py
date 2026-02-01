import aiohttp
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.utils.errors import error_handler
from zyrax.config import Config
import google.generativeai as genai
import random
import asyncio
from functools import partial

__mod_name__ = "Utilities"
__help__ = """
/ping - Check bot latency
/weather <city> - Get weather info
/ip <ip/domain> - Get IP/DNS info
/bin <bin> - Get BIN info
/time <timezone> - Get current time in a timezone
/tr <lang> <text> - Translate text (e.g. /tr es Hello)
"""

async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            try:
                return await resp.json()
            except:
                return None

@Client.on_message(filters.command("ping"))
async def ping(client: Client, message: Message):
    start = time.time()
    msg = await message.reply_text("Pong!")
    end = time.time()
    await msg.edit_text(f"Pong! `{round((end - start) * 1000)}ms`")

@Client.on_message(filters.command("weather") & filters.group)
@error_handler
async def weather(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /weather <city>")
    
    city = message.text.split(None, 1)[1]
    url = f"https://wttr.in/{city}?format=4"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                text = await resp.text()
                await message.reply_text(f"🌦 **Weather:**\n{text}")
            else:
                await message.reply_text("City not found.")

@Client.on_message(filters.command("ip") & filters.group)
@error_handler
async def ip_lookup(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /ip <ip/domain>")
    
    target = message.command[1]
    data = await fetch_json(f"http://ip-api.com/json/{target}")
    
    if data and data["status"] == "success":
        text = (
            f"🌐 **IP Info:** `{data['query']}`\n"
            f"**ISP:** {data['isp']}\n"
            f"**Country:** {data['country']} ({data['countryCode']})\n"
            f"**Region:** {data['regionName']}\n"
            f"**City:** {data['city']}\n"
            f"**Timezone:** {data['timezone']}"
        )
        await message.reply_text(text)
    else:
        await message.reply_text("Invalid IP/Domain.")

@Client.on_message(filters.command("bin") & filters.group)
@error_handler
async def bin_lookup(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /bin <bin>")
    
    bin_code = message.command[1][:6]
    if not bin_code.isdigit():
        return await message.reply_text("Invalid BIN.")
        
    data = await fetch_json(f"https://lookup.binlist.net/{bin_code}")
    
    if data:
        scheme = data.get("scheme", "?")
        type_ = data.get("type", "?")
        brand = data.get("brand", "?")
        bank = data.get("bank", {}).get("name", "?")
        country = data.get("country", {}).get("name", "?")
        emoji = data.get("country", {}).get("emoji", "")
        
        text = (
            f"💳 **BIN Info:** `{bin_code}`\n"
            f"**Scheme:** {scheme}\n"
            f"**Type:** {type_}\n"
            f"**Brand:** {brand}\n"
            f"**Bank:** {bank}\n"
            f"**Country:** {country} {emoji}"
        )
        await message.reply_text(text)
    else:
        await message.reply_text("BIN not found.")

@Client.on_message(filters.command("time") & filters.group)
async def world_time(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /time <timezone/city> (e.g. UTC, Asia/Kolkata)")
    
    query = message.command[1]
    # Simple fallback using worldtimeapi directly
    data = await fetch_json(f"http://worldtimeapi.org/api/timezone/{query}")
    if data and "datetime" in data:
         dt = data["datetime"].split(".")[0].replace("T", " ")
         await message.reply_text(f"🕒 **Time in {query}:**\n`{dt}`")
    else:
         await message.reply_text("Timezone not found. Try format: Area/City (e.g. Europe/London)")

def translate_gemini(text: str, target_lang: str):
    if not Config.GEMINI_API_KEYS:
        return "No Gemini API Keys configured."
        
    try:
        api_key = random.choice(Config.GEMINI_API_KEYS)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"Translate the following text to {target_lang}. Only provide the translation, no extra text. Text: \"{text}\""
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Translation Error: {e}"

@Client.on_message(filters.command(["tr", "translate"]) & filters.group)
async def translate(client: Client, message: Message):
    if len(message.command) < 3 and not message.reply_to_message:
        return await message.reply_text("Usage: /tr <lang> <text> or reply with /tr <lang>")
        
    target_lang = message.command[1]
    
    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption
        if not text:
            return await message.reply_text("No text to translate.")
    else:
        text = " ".join(message.command[2:])
        
    msg = await message.reply_text("Translating...")
    
    # Run in executor
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, partial(translate_gemini, text, target_lang))
    
    await msg.edit_text(f"**Translated ({target_lang}):**\n\n{result}")
