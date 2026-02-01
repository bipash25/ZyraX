from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from zyrax.utils.decorators import require_admin
from zyrax.utils.errors import error_handler
from zyrax.database.mongo import db
import random
import asyncio
import time

__mod_name__ = "Captcha"
__help__ = """
/captcha [on/off] - Enable or disable captcha for the group.
/captchamode [button/math] - Set captcha mode.
"""

# In-memory storage for pending captchas: {user_id_chat_id: {"answer": ..., "timestamp": ...}}
PENDING_CAPTCHAS = {}
# Keep references to tasks to avoid GC
BACKGROUND_TASKS = set()

@Client.on_message(filters.command("captcha") & filters.group)
@require_admin()
@error_handler
async def set_captcha(client: Client, message: Message):
    if len(message.command) < 2:
        # Get current status
        settings = await db.get_captcha_settings(message.chat.id)
        status = "ON" if settings and settings.get("enabled") else "OFF"
        mode = settings.get("mode", "button")
        return await message.reply_text(f"Captcha is currently: **{status}** (Mode: {mode})")
        
    arg = message.command[1].lower()
    if arg == "on":
        await db.set_captcha(message.chat.id, enabled=True)
        await message.reply_text("Captcha enabled. New users will be muted until they verify.")
    elif arg == "off":
        await db.set_captcha(message.chat.id, enabled=False)
        await message.reply_text("Captcha disabled.")
    else:
        await message.reply_text("Usage: /captcha [on/off]")

@Client.on_message(filters.command("captchamode") & filters.group)
@require_admin()
@error_handler
async def set_captcha_mode(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /captchamode [button/math]")
    
    mode = message.command[1].lower()
    if mode not in ["button", "math"]:
        return await message.reply_text("Invalid mode. Use 'button' or 'math'.")
    
    await db.set_captcha(message.chat.id, mode=mode)
    await message.reply_text(f"Captcha mode set to: **{mode}**")

@Client.on_message(filters.new_chat_members & filters.group, group=1) 
async def captcha_handler(client: Client, message: Message):
    chat_id = message.chat.id
    settings = await db.get_captcha_settings(chat_id)
    
    if not settings or not settings.get("enabled"):
        return

    mode = settings.get("mode", "button")
    
    # Slight delay to allow welcome message to be sent first (from group 0)
    await asyncio.sleep(0.5)
    
    for member in message.new_chat_members:
        if member.is_bot or member.is_self:
            continue
            
        # Mute user
        try:
            await client.restrict_chat_member(chat_id, member.id, ChatPermissions())
        except Exception:
            # Bot might not have permissions
            return

        # Prepare Captcha
        question = "Click to verify you are human."
        answer = "verified"
        buttons = []

        if mode == "math":
            a = random.randint(1, 10)
            b = random.randint(1, 10)
            question = f"Solve: {a} + {b} = ?"
            answer = str(a + b)
            
            # Generate buttons (1 correct, 3 wrong)
            options = [answer]
            while len(options) < 4:
                wrong = str(random.randint(2, 20))
                if wrong not in options:
                    options.append(wrong)
            random.shuffle(options)
            
            row1 = [InlineKeyboardButton(opt, callback_data=f"captcha_{opt}_{member.id}") for opt in options[:2]]
            row2 = [InlineKeyboardButton(opt, callback_data=f"captcha_{opt}_{member.id}") for opt in options[2:]]
            buttons = [row1, row2]
            
        else: # Button mode
            buttons = [[InlineKeyboardButton("I am Human", callback_data=f"captcha_verified_{member.id}")]]

        msg = await message.reply_text(
            f"Hello {member.mention}, please verify yourself.\n{question}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
        # Store pending verification
        PENDING_CAPTCHAS[f"{member.id}_{chat_id}"] = {
            "msg_id": msg.id,
            "answer": answer,
            "timestamp": time.time()
        }
        
        # Auto kick task (60 seconds)
        task = asyncio.create_task(timeout_captcha(client, chat_id, member.id, msg.id))
        BACKGROUND_TASKS.add(task)
        task.add_done_callback(BACKGROUND_TASKS.discard)

async def timeout_captcha(client, chat_id, user_id, msg_id):
    await asyncio.sleep(60) # 60 seconds timeout
    key = f"{user_id}_{chat_id}"
    if key in PENDING_CAPTCHAS:
        # Not verified yet
        try:
            await client.ban_chat_member(chat_id, user_id)
            await client.unban_chat_member(chat_id, user_id) # Kick (Ban+Unban)
            await client.delete_messages(chat_id, msg_id)
            del PENDING_CAPTCHAS[key]
            await client.send_message(chat_id, f"User <a href='tg://user?id={user_id}'>{user_id}</a> failed captcha and was kicked.")
        except Exception:
            pass

@Client.on_callback_query(filters.regex(r"^captcha_"))
async def captcha_callback(client: Client, callback_query):
    data = callback_query.data.split("_")
    # data format: captcha_ANSWER_USERID
    ans_provided = data[1]
    user_id = int(data[2])
    
    if callback_query.from_user.id != user_id:
        return await callback_query.answer("This captcha is not for you!", show_alert=True)
    
    chat_id = callback_query.message.chat.id
    key = f"{user_id}_{chat_id}"
    
    if key not in PENDING_CAPTCHAS:
        return await callback_query.answer("Captcha expired or invalid.")
    
    correct_ans = PENDING_CAPTCHAS[key]["answer"]
    
    if ans_provided == correct_ans:
        # Success
        del PENDING_CAPTCHAS[key]
        try:
            # Unmute
            await client.restrict_chat_member(
                chat_id,
                user_id,
                ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_send_polls=True,
                    can_change_info=False,
                    can_invite_users=True,
                    can_pin_messages=False
                )
            )
            await callback_query.message.delete()
            await callback_query.answer("Verified! Welcome.")
        except Exception as e:
            await callback_query.answer(f"Error: {e}", show_alert=True)
            
    else:
        # Wrong answer
        await callback_query.answer("Wrong answer! Try again.", show_alert=True)
