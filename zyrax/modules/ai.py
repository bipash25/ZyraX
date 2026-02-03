"""
ZyraX AI Module

AI-powered commands using Gemini and OpenAI APIs.
"""

import asyncio
import os
import random
from functools import partial
from typing import Optional

import aiohttp
import google.generativeai as genai
from pyrogram import Client, filters
from pyrogram.types import Message

from zyrax.config import Config
from zyrax.utils.errors import error_handler
from zyrax.utils.ratelimit import ai_rate_limit


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


# =============================================================================
# CONSTANTS
# =============================================================================

MAX_DOCUMENT_CHARS = 30000
DEFAULT_IMAGE_SIZE = "1024x1024"
GEMINI_MODEL = "gemini-pro"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _call_gemini(question: str) -> Optional[str]:
    """
    Call Gemini API synchronously.
    
    This is meant to be run in an executor since the Gemini SDK is synchronous.
    """
    if not Config.GEMINI_API_KEYS:
        return None
    
    api_key = random.choice(Config.GEMINI_API_KEYS)
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(question)
    return response.text


async def gemini_query(prompt: str) -> Optional[str]:
    """
    Query Gemini API asynchronously.
    
    Runs the synchronous SDK call in an executor to avoid blocking.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(_call_gemini, prompt))


def check_ai_enabled() -> bool:
    """Check if AI features are enabled (Gemini keys configured)."""
    return bool(Config.GEMINI_API_KEYS)


def check_image_enabled() -> bool:
    """Check if image generation is enabled (OpenAI key configured)."""
    return bool(Config.OPENAI_API_KEY)


# =============================================================================
# COMMAND HANDLERS
# =============================================================================

@Client.on_message(filters.command(["ask", "gemini", "chatgpt"]) & filters.group)
@ai_rate_limit()
@error_handler
async def ask_ai(client: Client, message: Message):
    """Answer questions using Gemini AI."""
    if len(message.command) < 2:
        return await message.reply_text("Usage: /ask <question>")
    
    if not check_ai_enabled():
        return await message.reply_text("AI is currently disabled (No Gemini API Keys).")
    
    question = " ".join(message.command[1:])
    msg = await message.reply_text("Thinking...")
    
    try:
        response = await gemini_query(question)
        
        if response:
            await msg.edit_text(response)
        else:
            await msg.edit_text("Failed to get response.")
            
    except Exception as e:
        await msg.edit_text(f"AI Error: {e}")


@Client.on_message(filters.command("imagine") & filters.group)
@ai_rate_limit()
@error_handler
async def imagine(client: Client, message: Message):
    """Generate images using OpenAI DALL-E."""
    if len(message.command) < 2:
        return await message.reply_text("Usage: /imagine <prompt>")
    
    if not check_image_enabled():
        return await message.reply_text("Image generation is disabled (No OpenAI API Key).")
    
    prompt = " ".join(message.command[1:])
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
                "size": DEFAULT_IMAGE_SIZE
            }
            
            async with session.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=data
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    image_url = result["data"][0]["url"]
                    await message.reply_photo(image_url, caption=f"Prompt: {prompt}")
                    await msg.delete()
                else:
                    error_text = await resp.text()
                    await msg.edit_text(f"AI Error: Failed to generate image. ({resp.status})")
                    
    except Exception as e:
        await msg.edit_text(f"Error: {e}")


@Client.on_message(filters.command(["summarize", "tldr"]))
@ai_rate_limit()
@error_handler
async def summarize_content(client: Client, message: Message):
    """Summarize text or documents."""
    if not check_ai_enabled():
        return await message.reply_text("AI is currently disabled (No Gemini API Keys).")
    
    text_to_summarize = None
    msg = None
    
    if message.reply_to_message:
        reply = message.reply_to_message
        
        if reply.document:
            msg = await message.reply_text("Downloading and analyzing document...")
            
            try:
                file_path = await reply.download()
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text_to_summarize = f.read()
                
                os.remove(file_path)
                
                if len(text_to_summarize) > MAX_DOCUMENT_CHARS:
                    text_to_summarize = text_to_summarize[:MAX_DOCUMENT_CHARS] + "\n\n[Content truncated...]"
                    
            except Exception as e:
                return await msg.edit_text(f"Failed to read document: {e}")
        
        elif reply.text:
            text_to_summarize = reply.text
            msg = await message.reply_text("Analyzing...")
        else:
            return await message.reply_text("Reply to a text message or document to summarize.")
    
    elif len(message.command) > 1:
        text_to_summarize = " ".join(message.command[1:])
        msg = await message.reply_text("Analyzing...")
    else:
        return await message.reply_text("Reply to a message/document or provide text to summarize.")
    
    if not text_to_summarize:
        return await msg.edit_text("No content to summarize.")
    
    is_tldr = message.command[0].lower() == "tldr"
    
    if is_tldr:
        prompt = f"Provide a very brief TL;DR (1-2 sentences max) of the following:\n\n{text_to_summarize}"
    else:
        prompt = f"Provide a comprehensive summary of the following content. Include key points and main ideas:\n\n{text_to_summarize}"
    
    try:
        response = await gemini_query(prompt)
        
        if response:
            header = "**TL;DR:**" if is_tldr else "**Summary:**"
            await msg.edit_text(f"{header}\n\n{response}")
        else:
            await msg.edit_text("Failed to generate summary.")
            
    except Exception as e:
        await msg.edit_text(f"Error: {e}")


@Client.on_message(filters.command("explain"))
@ai_rate_limit()
@error_handler
async def explain_topic(client: Client, message: Message):
    """Explain a topic in detail."""
    if len(message.command) < 2:
        return await message.reply_text("Usage: /explain <topic>")
    
    if not check_ai_enabled():
        return await message.reply_text("AI is currently disabled.")
    
    topic = " ".join(message.command[1:])
    msg = await message.reply_text("Researching...")
    
    prompt = f"""Explain '{topic}' in detail. Include:
1. What it is
2. How it works
3. Key concepts
4. Examples if applicable

Make it educational and easy to understand."""
    
    try:
        response = await gemini_query(prompt)
        
        if response:
            await msg.edit_text(f"**Explanation: {topic}**\n\n{response}")
        else:
            await msg.edit_text("Failed to generate explanation.")
            
    except Exception as e:
        await msg.edit_text(f"Error: {e}")


@Client.on_message(filters.command("translate"))
@ai_rate_limit()
@error_handler
async def translate_text(client: Client, message: Message):
    """Translate text to another language."""
    if len(message.command) < 3 and not message.reply_to_message:
        return await message.reply_text(
            "Usage: /translate <language> <text>\n"
            "Or reply to a message: /translate <language>"
        )
    
    if not check_ai_enabled():
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
        response = await gemini_query(prompt)
        
        if response:
            await msg.edit_text(f"**Translation ({target_lang}):**\n\n{response}")
        else:
            await msg.edit_text("Failed to translate.")
            
    except Exception as e:
        await msg.edit_text(f"Error: {e}")
