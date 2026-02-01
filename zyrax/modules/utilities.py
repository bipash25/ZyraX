import aiohttp
import time
import math
import io
import qrcode
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from zyrax.utils.errors import error_handler
from zyrax.config import Config
from zyrax.database.mongo import db
import google.generativeai as genai
import random
import asyncio
from functools import partial
from datetime import datetime, timedelta

__mod_name__ = "Utilities"
__help__ = """
**General:**
/ping - Check bot latency
/weather <city> - Get weather info
/ip <ip/domain> - Get IP/DNS info
/bin <bin> - Get BIN info
/time <timezone> - Get current time in a timezone
/tr <lang> <text> - Translate text

**Calculator:**
/calc <expression> - Scientific calculator
/convert <value> <from> <to> - Unit converter

**QR Codes:**
/qr <text> - Generate QR code
/qrread - Reply to QR image to read it

**Reminders:**
/remind <time> <text> - Set a reminder
/reminders - List your reminders

**Todo List:**
/todo add <task> - Add a task
/todo list - List tasks
/todo done <number> - Mark task as done
/todo clear - Clear all tasks

**Polls:**
/poll <question> | <option1> | <option2> | ... - Create a poll
/closepoll - Close active poll (reply to poll)
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
                await message.reply_text(f"**Weather:**\n{text}")
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
            f"**IP Info:** `{data['query']}`\n"
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
            f"**BIN Info:** `{bin_code}`\n"
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
    data = await fetch_json(f"http://worldtimeapi.org/api/timezone/{query}")
    if data and "datetime" in data:
         dt = data["datetime"].split(".")[0].replace("T", " ")
         await message.reply_text(f"**Time in {query}:**\n`{dt}`")
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
    
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, partial(translate_gemini, text, target_lang))
    
    await msg.edit_text(f"**Translated ({target_lang}):**\n\n{result}")


# ===== CALCULATOR =====

@Client.on_message(filters.command("calc"))
@error_handler
async def calculator(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /calc <expression>")
    
    expr = " ".join(message.command[1:])
    
    # Safe evaluation with math functions
    allowed = {
        'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
        'sqrt': math.sqrt, 'log': math.log, 'log10': math.log10,
        'exp': math.exp, 'pow': pow, 'abs': abs,
        'pi': math.pi, 'e': math.e,
        'floor': math.floor, 'ceil': math.ceil,
        'radians': math.radians, 'degrees': math.degrees
    }
    
    try:
        # Remove potentially dangerous characters
        safe_expr = expr.replace('^', '**')
        for char in ['import', 'exec', 'eval', 'open', '__']:
            if char in safe_expr.lower():
                return await message.reply_text("Invalid expression.")
        
        result = eval(safe_expr, {"__builtins__": {}}, allowed)
        await message.reply_text(f"**Result:**\n`{expr} = {result}`")
    except Exception as e:
        await message.reply_text(f"Error: {e}")


@Client.on_message(filters.command("convert"))
@error_handler
async def unit_converter(client: Client, message: Message):
    if len(message.command) < 4:
        return await message.reply_text("Usage: /convert <value> <from> <to>\nExample: /convert 100 km mi")
    
    try:
        value = float(message.command[1])
        from_unit = message.command[2].lower()
        to_unit = message.command[3].lower()
    except ValueError:
        return await message.reply_text("Invalid value.")
    
    # Conversion factors (to base unit)
    conversions = {
        # Length (meters)
        'km': ('length', 1000), 'm': ('length', 1), 'cm': ('length', 0.01),
        'mm': ('length', 0.001), 'mi': ('length', 1609.34), 'ft': ('length', 0.3048),
        'in': ('length', 0.0254), 'yd': ('length', 0.9144),
        # Weight (grams)
        'kg': ('weight', 1000), 'g': ('weight', 1), 'mg': ('weight', 0.001),
        'lb': ('weight', 453.592), 'oz': ('weight', 28.3495),
        # Temperature (special handling)
        'c': ('temp', 'c'), 'f': ('temp', 'f'), 'k': ('temp', 'k'),
        # Time (seconds)
        's': ('time', 1), 'min': ('time', 60), 'h': ('time', 3600),
        'd': ('time', 86400), 'w': ('time', 604800),
    }
    
    if from_unit not in conversions or to_unit not in conversions:
        return await message.reply_text("Unknown unit. Supported: km, m, cm, mm, mi, ft, in, yd, kg, g, mg, lb, oz, c, f, k, s, min, h, d, w")
    
    from_type, from_factor = conversions[from_unit]
    to_type, to_factor = conversions[to_unit]
    
    if from_type != to_type:
        return await message.reply_text("Cannot convert between different unit types.")
    
    # Special handling for temperature
    if from_type == 'temp':
        if from_unit == 'c':
            base = value
        elif from_unit == 'f':
            base = (value - 32) * 5/9
        else:  # kelvin
            base = value - 273.15
        
        if to_unit == 'c':
            result = base
        elif to_unit == 'f':
            result = base * 9/5 + 32
        else:
            result = base + 273.15
    else:
        base = value * from_factor
        result = base / to_factor
    
    await message.reply_text(f"**Conversion:**\n`{value} {from_unit} = {result:.4f} {to_unit}`")


# ===== QR CODES =====

@Client.on_message(filters.command("qr"))
@error_handler
async def generate_qr(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /qr <text>")
    
    text = " ".join(message.command[1:])
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(text)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    buf.name = "qrcode.png"
    
    await message.reply_photo(buf, caption=f"QR Code for: `{text[:100]}`")


# ===== REMINDERS =====

@Client.on_message(filters.command("remind"))
@error_handler
async def set_reminder(client: Client, message: Message):
    if len(message.command) < 3:
        return await message.reply_text("Usage: /remind <time> <text>\nExample: /remind 2h Check the oven")
    
    from zyrax.utils.time_parser import parse_duration
    
    try:
        duration = parse_duration(message.command[1])
    except Exception:
        return await message.reply_text("Invalid time format. Use: 30s, 5m, 2h, 1d")
    
    text = " ".join(message.command[2:])
    remind_at = time.time() + duration
    
    await db.add_reminder(message.from_user.id, message.chat.id, text, remind_at)
    
    remind_time = datetime.fromtimestamp(remind_at).strftime("%Y-%m-%d %H:%M:%S")
    await message.reply_text(f"Reminder set for: `{remind_time}`\n\n{text}")


@Client.on_message(filters.command("reminders"))
@error_handler
async def list_reminders(client: Client, message: Message):
    reminders = await db.get_collection("reminders")
    cursor = reminders.find({"user_id": message.from_user.id})
    user_reminders = [doc async for doc in cursor]
    
    if not user_reminders:
        return await message.reply_text("You have no active reminders.")
    
    text = "**Your Reminders:**\n\n"
    for i, rem in enumerate(user_reminders, 1):
        remind_time = datetime.fromtimestamp(rem["remind_at"]).strftime("%m/%d %H:%M")
        text += f"{i}. `{remind_time}` - {rem['text'][:50]}\n"
    
    await message.reply_text(text)


# ===== TODO LIST =====

@Client.on_message(filters.command("todo"))
@error_handler
async def todo_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /todo <add/list/done/clear> [args]")
    
    action = message.command[1].lower()
    user_id = message.from_user.id
    
    if action == "add":
        if len(message.command) < 3:
            return await message.reply_text("Usage: /todo add <task>")
        task = " ".join(message.command[2:])
        await db.add_todo(user_id, task)
        await message.reply_text(f"Added: {task}")
        
    elif action == "list":
        todos = await db.get_todos(user_id)
        if not todos:
            return await message.reply_text("Your todo list is empty!")
        
        text = "**Your Todo List:**\n\n"
        for i, todo in enumerate(todos, 1):
            text += f"{i}. {todo['task']}\n"
        await message.reply_text(text)
        
    elif action == "done":
        if len(message.command) < 3:
            return await message.reply_text("Usage: /todo done <number>")
        try:
            index = int(message.command[2]) - 1
            success = await db.complete_todo(user_id, index)
            if success:
                await message.reply_text("Task marked as done!")
            else:
                await message.reply_text("Invalid task number.")
        except ValueError:
            await message.reply_text("Please provide a valid number.")
            
    elif action == "clear":
        await db.clear_todos(user_id)
        await message.reply_text("Todo list cleared!")


# ===== POLLS =====

@Client.on_message(filters.command("poll") & filters.group)
@error_handler
async def create_poll(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /poll <question> | <option1> | <option2> | ...")
    
    content = " ".join(message.command[1:])
    parts = [p.strip() for p in content.split("|")]
    
    if len(parts) < 3:
        return await message.reply_text("Please provide a question and at least 2 options, separated by |")
    
    question = parts[0]
    options = parts[1:]
    
    if len(options) > 10:
        return await message.reply_text("Maximum 10 options allowed.")
    
    poll_id = await db.create_poll(message.chat.id, message.from_user.id, question, options)
    
    # Build poll message with buttons
    text = f"**Poll:** {question}\n\n"
    for i, opt in enumerate(options):
        text += f"{i+1}. {opt} - 0 votes\n"
    
    buttons = []
    for i, opt in enumerate(options):
        buttons.append([InlineKeyboardButton(f"{i+1}. {opt}", callback_data=f"poll:{poll_id}:{i}")])
    
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex(r"^poll:"))
async def poll_vote(client: Client, callback: CallbackQuery):
    _, poll_id, option = callback.data.split(":")
    
    from bson import ObjectId
    poll = await db.get_poll(ObjectId(poll_id))
    
    if not poll or not poll.get("active"):
        return await callback.answer("This poll is closed.", show_alert=True)
    
    await db.vote_poll(ObjectId(poll_id), callback.from_user.id, option)
    
    # Refresh poll
    poll = await db.get_poll(ObjectId(poll_id))
    
    text = f"**Poll:** {poll['question']}\n\n"
    buttons = []
    for i, (opt_idx, opt_data) in enumerate(poll["options"].items()):
        vote_count = len(opt_data["votes"])
        text += f"{int(opt_idx)+1}. {opt_data['text']} - {vote_count} votes\n"
        buttons.append([InlineKeyboardButton(f"{int(opt_idx)+1}. {opt_data['text']}", callback_data=f"poll:{poll_id}:{opt_idx}")])
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await callback.answer("Vote recorded!")


@Client.on_message(filters.command("closepoll") & filters.group)
@error_handler
async def close_poll(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a poll message to close it.")
    
    # Extract poll_id from the replied message buttons
    if not message.reply_to_message.reply_markup:
        return await message.reply_text("That doesn't appear to be a poll.")
    
    try:
        callback_data = message.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data
        if not callback_data.startswith("poll:"):
            return await message.reply_text("That doesn't appear to be a poll.")
        
        poll_id = callback_data.split(":")[1]
        from bson import ObjectId
        poll = await db.get_poll(ObjectId(poll_id))
        
        if poll and poll["creator_id"] == message.from_user.id:
            await db.close_poll(ObjectId(poll_id))
            await message.reply_text("Poll closed!")
        else:
            await message.reply_text("Only the poll creator can close it.")
    except Exception as e:
        await message.reply_text(f"Error closing poll: {e}")
