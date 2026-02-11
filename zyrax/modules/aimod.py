from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.enums import ChatMemberStatus
from zyrax.utils.decorators import require_admin
from zyrax.utils.errors import error_handler
from zyrax.database.mongo import db
from zyrax.config import Config
from google import genai
import random
import asyncio
from functools import partial

__mod_name__ = "AI Moderation"
__help__ = """
**AI Moderation Commands:**
/aimod on - Enable AI content moderation
/aimod off - Disable AI content moderation
/aimod sensitivity <low/medium/high> - Set moderation sensitivity
/aimod status - Check AI moderation status

**Features:**
- Automatic detection of toxic, offensive, and NSFW content
- Sentiment analysis for flagged messages
- Smart spam detection

**Note:** Requires Gemini API key to be configured.
"""

SENSITIVITY_PROMPTS = {
    "low": "Only flag extremely offensive content like hate speech, explicit threats, or severe harassment.",
    "medium": "Flag offensive content including insults, harassment, and inappropriate language.",
    "high": "Flag any potentially offensive content including mild insults, passive-aggressive language, and borderline inappropriate content."
}

def analyze_content_sync(text: str, sensitivity: str = "medium"):
    """Synchronous Gemini analysis - run in executor"""
    if not Config.GEMINI_API_KEYS:
        return None
    
    try:
        api_key = random.choice(Config.GEMINI_API_KEYS)
        client = genai.Client(api_key=api_key)
        # Using genai client
        
        sensitivity_desc = SENSITIVITY_PROMPTS.get(sensitivity, SENSITIVITY_PROMPTS["medium"])
        
        prompt = f"""Analyze the following message for moderation purposes. {sensitivity_desc}

Message: "{text}"

Respond in EXACTLY this JSON format (no markdown, just raw JSON):
{{"is_toxic": true/false, "category": "spam/harassment/hate/nsfw/threat/none", "confidence": 0.0-1.0, "reason": "brief explanation"}}

Only respond with the JSON, nothing else."""

        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        result_text = response.text.strip()
        
        # Parse JSON response
        import json
        # Clean up common issues
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        
        return json.loads(result_text)
    except Exception as e:
        return None


async def analyze_content(text: str, sensitivity: str = "medium"):
    """Async wrapper for content analysis"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(analyze_content_sync, text, sensitivity))


@Client.on_message(filters.command("aimod") & filters.group)
@require_admin()
@error_handler
async def aimod_settings(client: Client, message: Message):
    args = message.command[1:] if len(message.command) > 1 else []
    chat_id = message.chat.id
    
    if not args:
        return await message.reply_text("Usage: /aimod <on/off/sensitivity/status>")
    
    action = args[0].lower()
    
    if action == "on":
        if not Config.GEMINI_API_KEYS:
            return await message.reply_text("AI Moderation requires Gemini API keys to be configured.")
        
        await db.set_aimod(chat_id, True)
        await message.reply_text(
            "**AI Moderation Enabled!**\n\n"
            "Messages will be automatically analyzed for toxic content.\n"
            "Use /aimod sensitivity to adjust strictness."
        )
        
    elif action == "off":
        await db.set_aimod(chat_id, False)
        await message.reply_text("AI Moderation disabled.")
        
    elif action == "sensitivity":
        if len(args) < 2:
            return await message.reply_text("Usage: /aimod sensitivity <low/medium/high>")
        
        level = args[1].lower()
        if level not in ["low", "medium", "high"]:
            return await message.reply_text("Invalid level. Use: low, medium, or high")
        
        await db.set_aimod_sensitivity(chat_id, level)
        await message.reply_text(f"AI Moderation sensitivity set to: **{level}**")
        
    elif action == "status":
        settings = await db.get_aimod_settings(chat_id)
        enabled = settings.get("enabled", False)
        sensitivity = settings.get("sensitivity", "medium")
        
        status_text = "ON" if enabled else "OFF"
        await message.reply_text(
            f"**AI Moderation Status:**\n\n"
            f"Status: {status_text}\n"
            f"Sensitivity: {sensitivity}\n"
            f"API Keys: {len(Config.GEMINI_API_KEYS)} configured"
        )
    else:
        await message.reply_text("Unknown action. Use: on, off, sensitivity, status")


@Client.on_message(filters.text & filters.group, group=10)
async def aimod_watcher(client: Client, message: Message):
    """Watch messages for AI moderation"""
    if not message.text or message.text.startswith("/"):
        return
    
    # Skip short messages
    if len(message.text) < 10:
        return
    
    # Check if AI mod is enabled for this chat
    settings = await db.get_aimod_settings(message.chat.id)
    if not settings.get("enabled", False):
        return
    
    # Skip admins
    try:
        member = await message.chat.get_member(message.from_user.id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return
    except Exception:
        pass
    
    # Analyze content
    sensitivity = settings.get("sensitivity", "medium")
    analysis = await analyze_content(message.text, sensitivity)
    
    if not analysis:
        return
    
    if analysis.get("is_toxic") and analysis.get("confidence", 0) >= 0.7:
        category = analysis.get("category", "unknown")
        reason = analysis.get("reason", "Content flagged by AI")
        
        # Log the action
        await db.log_admin_action(
            "ai_flag",
            0,  # Bot
            message.chat.id,
            message.from_user.id,
            f"Category: {category}, Reason: {reason}"
        )
        
        # Take action based on category
        if category in ["threat", "hate"]:
            # Severe - mute user
            try:
                await message.delete()
                await client.restrict_chat_member(
                    message.chat.id,
                    message.from_user.id,
                    ChatPermissions(can_send_messages=False)
                )
                await message.reply_text(
                    f"**AI Moderation**\n\n"
                    f"{message.from_user.mention} has been muted.\n"
                    f"Reason: {reason}",
                    quote=False
                )
            except Exception:
                pass
                
        elif category in ["harassment", "nsfw"]:
            # Moderate - warn
            try:
                await message.delete()
                count = await db.add_warn(
                    message.chat.id,
                    message.from_user.id,
                    f"[AI] {reason}"
                )
                await message.reply_text(
                    f"**AI Warning**\n\n"
                    f"{message.from_user.mention} warned for inappropriate content.\n"
                    f"Warning count: {count}/3",
                    quote=False
                )
                
                if count >= 3:
                    await client.ban_chat_member(message.chat.id, message.from_user.id)
                    await db.reset_warns(message.chat.id, message.from_user.id)
            except Exception:
                pass
                
        else:
            # Low severity - just delete
            try:
                await message.delete()
                await message.reply_text(
                    f"{message.from_user.mention}, your message was removed by AI moderation.",
                    quote=False
                )
            except Exception:
                pass
