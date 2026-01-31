from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.config import Config
import aiohttp

__mod_name__ = "AI"
__help__ = """
/ask <question> - Ask ChatGPT
/chatgpt <question> - Alias for ask
/imagine <prompt> - Generate an image using AI
"""

@Client.on_message(filters.command("ask") & filters.group)
async def ask_ai(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /ask <question>")
    
    question = " ".join(message.command[1:])
    
    if not Config.OPENAI_API_KEY:
        return await message.reply_text(f"AI is currently disabled (No API Key). You asked: {question}")
    
    # OpenAI implementation placeholder
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": question}],
                "max_tokens": 150
            }
            async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    answer = result["choices"][0]["message"]["content"]
                    await message.reply_text(answer)
                else:
                    await message.reply_text("AI Error: Failed to contact OpenAI.")
    except Exception as e:
        await message.reply_text(f"AI Error: {e}")

@Client.on_message(filters.command("chatgpt"))
async def chatgpt_alias(client: Client, message: Message):
    await ask_ai(client, message)

@Client.on_message(filters.command("imagine") & filters.group)
async def imagine(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /imagine <prompt>")
    
    prompt = " ".join(message.command[1:])
    
    if not Config.OPENAI_API_KEY:
        return await message.reply_text("AI is currently disabled (No API Key).")
    
    msg = await message.reply_text("Generating image... Please wait.")
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024"
            }
            async with session.post("https://api.openai.com/v1/images/generations", headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    image_url = result["data"][0]["url"]
                    await message.reply_photo(image_url, caption=f"Prompt: {prompt}")
                    await msg.delete()
                else:
                    error_text = await resp.text()
                    await msg.edit_text(f"AI Error: Failed to generate image. ({resp.status})")
    except Exception as e:
        await msg.edit_text(f"Error: {str(e)}")
