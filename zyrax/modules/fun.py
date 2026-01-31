import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

__mod_name__ = "Fun"
__help__ = """
/meme - Get a random meme
/joke - Get a random joke
"""

async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            try:
                return await resp.json()
            except:
                return None

@Client.on_message(filters.command("meme") & filters.group)
async def meme(client: Client, message: Message):
    # Using a public meme API (e.g., meme-api.com)
    url = "https://meme-api.com/gimme"
    data = await fetch_json(url)
    if data and "url" in data:
        await message.reply_photo(data["url"], caption=data["title"])
    else:
        await message.reply_text("Failed to fetch meme.")

@Client.on_message(filters.command("joke") & filters.group)
async def joke(client: Client, message: Message):
    url = "https://official-joke-api.appspot.com/random_joke"
    data = await fetch_json(url)
    if data:
        await message.reply_text(f"{data['setup']}\n\n||{data['punchline']}||")
    else:
        await message.reply_text("Failed to fetch joke.")
