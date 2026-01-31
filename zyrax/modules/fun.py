import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

__mod_name__ = "Fun"
__help__ = """
/meme - Get a random meme
/joke - Get a random joke
/quote - Get a random quote
/ud <term> - Search Urban Dictionary
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

@Client.on_message(filters.command("quote") & filters.group)
async def quote(client: Client, message: Message):
    url = "https://api.quotable.io/random"
    data = await fetch_json(url)
    if data:
        await message.reply_text(f"“{data['content']}”\n\n— *{data['author']}*")
    else:
        await message.reply_text("Failed to fetch quote.")

@Client.on_message(filters.command("ud") & filters.group)
async def urban_dictionary(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /ud <term>")
    
    term = message.text.split(None, 1)[1]
    url = f"https://api.urbandictionary.com/v0/define?term={term}"
    data = await fetch_json(url)
    
    if data and "list" in data and len(data["list"]) > 0:
        entry = data["list"][0]
        definition = entry["definition"].replace("[", "").replace("]", "")
        example = entry["example"].replace("[", "").replace("]", "")
        
        text = (
            f"**Word:** {entry['word']}\n\n"
            f"**Definition:**\n{definition[:1000]}...\n\n"
            f"**Example:**\n{example[:500]}..."
        )
        await message.reply_text(text)
    else:
        await message.reply_text("No definition found.")
