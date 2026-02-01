import aiohttp
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.utils.errors import error_handler

__mod_name__ = "Fun"
__help__ = """
/quote - Get a random quote
/joke - Get a random joke
/meme - Get a random meme
/ud <term> - Search Urban Dictionary
/cat - Get a random cat picture
/dog - Get a random dog picture
/coin - Flip a coin
/choice <options> - Choose from options (comma separated)
"""

async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            try:
                return await resp.json()
            except:
                return None

@Client.on_message(filters.command("quote") & filters.group)
@error_handler
async def quote(client: Client, message: Message):
    data = await fetch_json("https://api.quotable.io/random")
    if data:
        await message.reply_text(f"“{data['content']}”\n— __{data['author']}__")
    else:
        await message.reply_text("Failed to fetch quote.")

@Client.on_message(filters.command("joke") & filters.group)
@error_handler
async def joke(client: Client, message: Message):
    data = await fetch_json("https://official-joke-api.appspot.com/random_joke")
    if data:
        await message.reply_text(f"{data['setup']}\n\n||{data['punchline']}||")
    else:
        await message.reply_text("Failed to fetch joke.")

@Client.on_message(filters.command("meme") & filters.group)
@error_handler
async def meme(client: Client, message: Message):
    data = await fetch_json("https://meme-api.com/gimme")
    if data and "url" in data:
        await message.reply_photo(data["url"], caption=data["title"])
    else:
        await message.reply_text("Failed to fetch meme.")

@Client.on_message(filters.command("ud") & filters.group)
@error_handler
async def urban_dictionary(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /ud <term>")
    
    term = message.text.split(None, 1)[1]
    data = await fetch_json(f"https://api.urbandictionary.com/v0/define?term={term}")
    
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

@Client.on_message(filters.command("cat") & filters.group)
@error_handler
async def cat(client: Client, message: Message):
    data = await fetch_json("https://api.thecatapi.com/v1/images/search")
    if data:
        await message.reply_photo(data[0]['url'], caption="Meow! 🐱")
    else:
        await message.reply_text("Failed to fetch cat.")

@Client.on_message(filters.command("dog") & filters.group)
@error_handler
async def dog(client: Client, message: Message):
    data = await fetch_json("https://dog.ceo/api/breeds/image/random")
    if data:
        await message.reply_photo(data['message'], caption="Woof! 🐶")
    else:
        await message.reply_text("Failed to fetch dog.")

@Client.on_message(filters.command("coin") & filters.group)
async def coin(client: Client, message: Message):
    result = random.choice(["Heads", "Tails"])
    await message.reply_text(f"🪙 **{result}**")

@Client.on_message(filters.command(["choice", "choose"]) & filters.group)
async def choose(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /choice option1, option2, ...")
    
    # Split by comma first, if no comma, split by space
    text = message.text.split(None, 1)[1]
    if "," in text:
        options = [o.strip() for o in text.split(",")]
    else:
        options = text.split()
        
    choice = random.choice(options)
    await message.reply_text(f"I choose: **{choice}**")
