from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.config import Config
import google.generativeai as genai
import random
import aiohttp

__mod_name__ = "AI"
__help__ = """
/ask <question> - Ask Gemini
/gemini <question> - Alias for ask
/imagine <prompt> - Generate an image (Requires OpenAI Key)
"""

def get_gemini_response(question: str):
    if not Config.GEMINI_API_KEYS:
        return None
    
    # Rotate Key
    api_key = random.choice(Config.GEMINI_API_KEYS)
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(question)
    return response.text

@Client.on_message(filters.command(["ask", "gemini", "chatgpt"]) & filters.group)
async def ask_ai(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /ask <question>")
    
    question = " ".join(message.command[1:])
    
    if not Config.GEMINI_API_KEYS:
        return await message.reply_text("AI is currently disabled (No Gemini API Keys).")
    
    msg = await message.reply_text("Thinking...")
    
    try:
        # Run synchronous Gemini call in executor or direct if library supports async (it doesn't natively, but it's fast)
        # Better to wrap in thread to not block event loop
        import asyncio
        from functools import partial
        
        loop = asyncio.get_running_loop()
        response_text = await loop.run_in_executor(None, partial(get_gemini_response, question))
        
        if response_text:
            await msg.edit_text(response_text)
        else:
            await msg.edit_text("Failed to get response.")
            
    except Exception as e:
        await msg.edit_text(f"AI Error: {e}")

@Client.on_message(filters.command("imagine") & filters.group)
async def imagine(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /imagine <prompt>")
    
    prompt = " ".join(message.command[1:])
    
    if not Config.OPENAI_API_KEY:
        return await message.reply_text("Image generation is disabled (No OpenAI API Key).")
    
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
                    await msg.edit_text(f"AI Error: Failed to generate image. ({resp.status})")
    except Exception as e:
        await msg.edit_text(f"Error: {str(e)}")
