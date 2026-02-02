from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.config import Config
import google.generativeai as genai
import random
import aiohttp
import io

__mod_name__ = "AI"
__help__ = """
/ask <question> - Ask Gemini
/gemini <question> - Alias for ask
/imagine <prompt> - Generate an image (Requires OpenAI Key)
/summarize - Reply to a document/text to summarize it
/tldr - Quick summary of replied message
/explain <topic> - Get a detailed explanation
/translate <lang> <text> - Translate text
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


# ===== DOCUMENT SUMMARIZATION =====
@Client.on_message(filters.command(["summarize", "tldr"]))
async def summarize_content(client: Client, message: Message):
    if not Config.GEMINI_API_KEYS:
        return await message.reply_text("AI is currently disabled (No Gemini API Keys).")
    
    text_to_summarize = None
    
    # Check if replying to a message
    if message.reply_to_message:
        reply = message.reply_to_message
        
        # Check if it's a document
        if reply.document:
            msg = await message.reply_text("Downloading and analyzing document...")
            
            try:
                # Download document
                file_path = await reply.download()
                
                # Read text content (supports txt, py, js, etc.)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text_to_summarize = f.read()
                
                # Cleanup
                import os
                os.remove(file_path)
                
                if len(text_to_summarize) > 30000:
                    text_to_summarize = text_to_summarize[:30000] + "\n\n[Content truncated...]"
                    
            except Exception as e:
                return await msg.edit_text(f"Failed to read document: {e}")
        
        # Check if it's text
        elif reply.text:
            text_to_summarize = reply.text
            msg = await message.reply_text("Analyzing...")
        else:
            return await message.reply_text("Reply to a text message or document to summarize.")
    else:
        # Check for inline text
        if len(message.command) > 1:
            text_to_summarize = " ".join(message.command[1:])
            msg = await message.reply_text("Analyzing...")
        else:
            return await message.reply_text("Reply to a message/document or provide text to summarize.")
    
    if not text_to_summarize:
        return await msg.edit_text("No content to summarize.")
    
    # Generate summary
    is_tldr = message.command[0].lower() == "tldr"
    
    if is_tldr:
        prompt = f"Provide a very brief TL;DR (1-2 sentences max) of the following:\n\n{text_to_summarize}"
    else:
        prompt = f"Provide a comprehensive summary of the following content. Include key points and main ideas:\n\n{text_to_summarize}"
    
    try:
        import asyncio
        from functools import partial
        
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, partial(get_gemini_response, prompt))
        
        if response:
            header = "**TL;DR:**" if is_tldr else "**Summary:**"
            await msg.edit_text(f"{header}\n\n{response}")
        else:
            await msg.edit_text("Failed to generate summary.")
            
    except Exception as e:
        await msg.edit_text(f"Error: {e}")


# ===== EXPLAIN TOPIC =====
@Client.on_message(filters.command("explain"))
async def explain_topic(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /explain <topic>")
    
    if not Config.GEMINI_API_KEYS:
        return await message.reply_text("AI is currently disabled.")
    
    topic = " ".join(message.command[1:])
    msg = await message.reply_text("Researching...")
    
    prompt = f"Explain '{topic}' in detail. Include:\n1. What it is\n2. How it works\n3. Key concepts\n4. Examples if applicable\n\nMake it educational and easy to understand."
    
    try:
        import asyncio
        from functools import partial
        
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, partial(get_gemini_response, prompt))
        
        if response:
            await msg.edit_text(f"**Explanation: {topic}**\n\n{response}")
        else:
            await msg.edit_text("Failed to generate explanation.")
            
    except Exception as e:
        await msg.edit_text(f"Error: {e}")


# ===== TRANSLATE =====
@Client.on_message(filters.command("translate"))
async def translate_text(client: Client, message: Message):
    if len(message.command) < 3 and not message.reply_to_message:
        return await message.reply_text(
            "Usage: /translate <language> <text>\n"
            "Or reply to a message: /translate <language>"
        )
    
    if not Config.GEMINI_API_KEYS:
        return await message.reply_text("AI is currently disabled.")
    
    target_lang = message.command[1] if len(message.command) > 1 else "English"
    
    if message.reply_to_message and message.reply_to_message.text:
        text = message.reply_to_message.text
    elif len(message.command) > 2:
        text = " ".join(message.command[2:])
    else:
        return await message.reply_text("Please provide text to translate.")
    
    msg = await message.reply_text("Translating...")
    
    prompt = f"Translate the following text to {target_lang}. Only provide the translation, nothing else:\n\n{text}"
    
    try:
        import asyncio
        from functools import partial
        
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, partial(get_gemini_response, prompt))
        
        if response:
            await msg.edit_text(f"**Translation ({target_lang}):**\n\n{response}")
        else:
            await msg.edit_text("Failed to translate.")
            
    except Exception as e:
        await msg.edit_text(f"Error: {e}")
