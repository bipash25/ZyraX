import asyncio
import random
import string
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from zyrax.config import Config
from zyrax.database.mongo import db

__mod_name__ = "Owner"
__help__ = """
**Owner Commands (2FA Protected):**
/broadcast <message> - Broadcast to all chats
/gban <user> - Global ban user
/ungban <user> - Remove global ban
/restart - Restart the bot
/stats - Bot statistics
/shell <cmd> - Execute shell command
/eval <code> - Evaluate Python code
/leave <chat_id> - Leave a chat

**Settings:**
/set2fa on/off - Enable/disable 2FA for sensitive commands
/setpanic <code> - Set panic button code (emergency shutdown)
"""

# 2FA confirmation storage: {user_id: {"code": "ABC123", "expires": timestamp, "action": "broadcast", "data": {...}}}
PENDING_2FA = {}

# Panic mode
PANIC_MODE = False

def is_owner(user_id: int) -> bool:
    return user_id == Config.OWNER_ID

def generate_2fa_code() -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

async def require_2fa(user_id: int, action: str, data: dict = None) -> tuple:
    """
    Returns (needs_2fa, code) - If needs_2fa is True, the caller should prompt for confirmation
    """
    settings = await db.get_user_data(user_id)
    if not settings or not settings.get("2fa_enabled", False):
        return False, None
    
    code = generate_2fa_code()
    PENDING_2FA[user_id] = {
        "code": code,
        "expires": time.time() + 120,  # 2 minutes
        "action": action,
        "data": data or {}
    }
    return True, code

def verify_2fa(user_id: int, code: str) -> bool:
    if user_id not in PENDING_2FA:
        return False
    
    pending = PENDING_2FA[user_id]
    if time.time() > pending["expires"]:
        del PENDING_2FA[user_id]
        return False
    
    if pending["code"] == code.upper():
        return True
    return False

def get_pending_action(user_id: int) -> dict:
    if user_id not in PENDING_2FA:
        return None
    pending = PENDING_2FA[user_id]
    del PENDING_2FA[user_id]
    return pending


@Client.on_message(filters.command("set2fa") & filters.private)
async def set_2fa(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    if len(message.command) < 2:
        return await message.reply_text("Usage: /set2fa on/off")
    
    mode = message.command[1].lower()
    if mode == "on":
        users = await db.get_collection("users")
        await users.update_one(
            {"user_id": message.from_user.id},
            {"$set": {"2fa_enabled": True}},
            upsert=True
        )
        await message.reply_text("2FA enabled for sensitive commands.")
    elif mode == "off":
        users = await db.get_collection("users")
        await users.update_one(
            {"user_id": message.from_user.id},
            {"$set": {"2fa_enabled": False}}
        )
        await message.reply_text("2FA disabled.")
    else:
        await message.reply_text("Invalid option. Use on/off.")


@Client.on_message(filters.command("confirm") & filters.private)
async def confirm_2fa(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    if len(message.command) < 2:
        return await message.reply_text("Usage: /confirm <code>")
    
    code = message.command[1].upper()
    
    if not verify_2fa(message.from_user.id, code):
        return await message.reply_text("Invalid or expired code.")
    
    pending = get_pending_action(message.from_user.id)
    if not pending:
        return await message.reply_text("No pending action.")
    
    action = pending["action"]
    data = pending["data"]
    
    # Execute the pending action
    if action == "broadcast":
        await execute_broadcast(client, message, data.get("text", ""))
    elif action == "gban":
        await execute_gban(client, message, data.get("user_id"))
    elif action == "restart":
        await execute_restart(client, message)
    elif action == "shell":
        await execute_shell(client, message, data.get("cmd", ""))
    elif action == "eval":
        await execute_eval(client, message, data.get("code", ""))
    elif action == "leave":
        await execute_leave(client, message, data.get("chat_id"))


@Client.on_message(filters.command("broadcast") & filters.private)
async def broadcast_cmd(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text("Usage: /broadcast <message> or reply to a message")
    
    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption
    else:
        text = message.text.split(None, 1)[1]
    
    needs_2fa, code = await require_2fa(message.from_user.id, "broadcast", {"text": text})
    
    if needs_2fa:
        await message.reply_text(
            f"**2FA Required**\n\n"
            f"Action: Broadcast message to all chats\n"
            f"Your code: `{code}`\n\n"
            f"Reply with: /confirm {code}\n"
            f"Expires in 2 minutes."
        )
    else:
        await execute_broadcast(client, message, text)


async def execute_broadcast(client: Client, message: Message, text: str):
    chats = await db.get_collection("chats")
    all_chats = await chats.find({}).to_list(length=None)
    
    success = 0
    failed = 0
    
    m = await message.reply_text(f"Broadcasting to {len(all_chats)} chats...")
    
    for chat in all_chats:
        try:
            await client.send_message(chat["chat_id"], text)
            success += 1
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception:
            failed += 1
    
    await m.edit_text(f"Broadcast complete!\nSuccess: {success}\nFailed: {failed}")


@Client.on_message(filters.command("gban") & filters.private)
async def gban_cmd(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text("Usage: /gban <user_id> or reply to a user")
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        try:
            user_id = int(message.command[1])
        except ValueError:
            try:
                user = await client.get_users(message.command[1])
                user_id = user.id
            except:
                return await message.reply_text("User not found.")
    
    needs_2fa, code = await require_2fa(message.from_user.id, "gban", {"user_id": user_id})
    
    if needs_2fa:
        await message.reply_text(
            f"**2FA Required**\n\n"
            f"Action: Global ban user {user_id}\n"
            f"Your code: `{code}`\n\n"
            f"Reply with: /confirm {code}\n"
            f"Expires in 2 minutes."
        )
    else:
        await execute_gban(client, message, user_id)


async def execute_gban(client: Client, message: Message, user_id: int):
    # Add to global ban list
    gbans = await db.get_collection("gbans")
    await gbans.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, "banned_at": time.time(), "banned_by": message.from_user.id}},
        upsert=True
    )
    
    # Ban from all chats
    chats = await db.get_collection("chats")
    all_chats = await chats.find({}).to_list(length=None)
    
    banned = 0
    for chat in all_chats:
        try:
            await client.ban_chat_member(chat["chat_id"], user_id)
            banned += 1
            await asyncio.sleep(0.05)
        except:
            pass
    
    await message.reply_text(f"Globally banned user {user_id}.\nBanned from {banned} chats.")


@Client.on_message(filters.command("ungban") & filters.private)
async def ungban_cmd(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    if len(message.command) < 2:
        return await message.reply_text("Usage: /ungban <user_id>")
    
    try:
        user_id = int(message.command[1])
    except ValueError:
        try:
            user = await client.get_users(message.command[1])
            user_id = user.id
        except:
            return await message.reply_text("User not found.")
    
    gbans = await db.get_collection("gbans")
    result = await gbans.delete_one({"user_id": user_id})
    
    if result.deleted_count > 0:
        await message.reply_text(f"Removed global ban for user {user_id}.")
    else:
        await message.reply_text("User was not globally banned.")


@Client.on_message(filters.command("stats") & filters.private)
async def bot_stats(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    stats = await db.get_stats()
    
    # Get uptime
    import os
    uptime = "Unknown"
    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.readline().split()[0])
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            uptime = f"{hours}h {minutes}m"
    except:
        pass
    
    # Count gbans
    gbans = await db.get_collection("gbans")
    gban_count = await gbans.count_documents({})
    
    await message.reply_text(
        f"**Bot Statistics**\n\n"
        f"Users: {stats['users']}\n"
        f"Chats: {stats['chats']}\n"
        f"Commands Today: {stats['commands_today']}\n"
        f"Global Bans: {gban_count}\n"
        f"System Uptime: {uptime}"
    )


@Client.on_message(filters.command("shell") & filters.private)
async def shell_cmd(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    if len(message.command) < 2:
        return await message.reply_text("Usage: /shell <command>")
    
    cmd = message.text.split(None, 1)[1]
    
    needs_2fa, code = await require_2fa(message.from_user.id, "shell", {"cmd": cmd})
    
    if needs_2fa:
        await message.reply_text(
            f"**2FA Required**\n\n"
            f"Action: Execute shell command\n"
            f"Command: `{cmd[:100]}...`\n"
            f"Your code: `{code}`\n\n"
            f"Reply with: /confirm {code}"
        )
    else:
        await execute_shell(client, message, cmd)


async def execute_shell(client: Client, message: Message, cmd: str):
    import subprocess
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        output = result.stdout or result.stderr or "No output"
        
        if len(output) > 4000:
            output = output[:4000] + "\n\n... (truncated)"
        
        await message.reply_text(f"**Output:**\n```\n{output}\n```")
    except subprocess.TimeoutExpired:
        await message.reply_text("Command timed out (30s limit).")
    except Exception as e:
        await message.reply_text(f"Error: {e}")


@Client.on_message(filters.command("eval") & filters.private)
async def eval_cmd(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    if len(message.command) < 2:
        return await message.reply_text("Usage: /eval <code>")
    
    code = message.text.split(None, 1)[1]
    
    needs_2fa, code_2fa = await require_2fa(message.from_user.id, "eval", {"code": code})
    
    if needs_2fa:
        await message.reply_text(
            f"**2FA Required**\n\n"
            f"Action: Evaluate Python code\n"
            f"Your code: `{code_2fa}`\n\n"
            f"Reply with: /confirm {code_2fa}"
        )
    else:
        await execute_eval(client, message, code)


async def execute_eval(client: Client, message: Message, code: str):
    try:
        # Create local scope with useful variables
        local_vars = {
            "client": client,
            "message": message,
            "db": db,
            "asyncio": asyncio,
        }
        
        # Handle async code
        if "await" in code:
            exec(
                f"async def __aexec():\n" + 
                "\n".join(f"    {line}" for line in code.split("\n")),
                local_vars
            )
            result = await local_vars["__aexec"]()
        else:
            result = eval(code, local_vars)
        
        output = str(result) if result is not None else "None"
        if len(output) > 4000:
            output = output[:4000] + "\n\n... (truncated)"
        
        await message.reply_text(f"**Result:**\n```\n{output}\n```")
    except Exception as e:
        await message.reply_text(f"**Error:**\n```\n{e}\n```")


@Client.on_message(filters.command("leave") & filters.private)
async def leave_cmd(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    if len(message.command) < 2:
        return await message.reply_text("Usage: /leave <chat_id>")
    
    try:
        chat_id = int(message.command[1])
    except ValueError:
        return await message.reply_text("Invalid chat ID.")
    
    needs_2fa, code = await require_2fa(message.from_user.id, "leave", {"chat_id": chat_id})
    
    if needs_2fa:
        await message.reply_text(
            f"**2FA Required**\n\n"
            f"Action: Leave chat {chat_id}\n"
            f"Your code: `{code}`\n\n"
            f"Reply with: /confirm {code}"
        )
    else:
        await execute_leave(client, message, chat_id)


async def execute_leave(client: Client, message: Message, chat_id: int):
    try:
        await client.leave_chat(chat_id)
        await message.reply_text(f"Left chat {chat_id}.")
    except Exception as e:
        await message.reply_text(f"Failed to leave: {e}")


@Client.on_message(filters.command("restart") & filters.private)
async def restart_cmd(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    needs_2fa, code = await require_2fa(message.from_user.id, "restart", {})
    
    if needs_2fa:
        await message.reply_text(
            f"**2FA Required**\n\n"
            f"Action: Restart bot\n"
            f"Your code: `{code}`\n\n"
            f"Reply with: /confirm {code}"
        )
    else:
        await execute_restart(client, message)


async def execute_restart(client: Client, message: Message):
    await message.reply_text("Restarting...")
    import os
    import sys
    os.execl(sys.executable, sys.executable, *sys.argv)


@Client.on_message(filters.command("setpanic") & filters.private)
async def set_panic(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    if len(message.command) < 2:
        return await message.reply_text("Usage: /setpanic <code>")
    
    code = message.command[1]
    users = await db.get_collection("users")
    await users.update_one(
        {"user_id": message.from_user.id},
        {"$set": {"panic_code": code}},
        upsert=True
    )
    await message.reply_text(f"Panic code set. Use /panic {code} to emergency shutdown.")


@Client.on_message(filters.command("panic") & filters.private)
async def panic_cmd(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return
    
    if len(message.command) < 2:
        return await message.reply_text("Usage: /panic <code>")
    
    code = message.command[1]
    user_data = await db.get_user_data(message.from_user.id)
    
    if not user_data or user_data.get("panic_code") != code:
        return await message.reply_text("Invalid panic code.")
    
    await message.reply_text("PANIC MODE ACTIVATED. Bot shutting down...")
    
    # Leave all chats
    chats = await db.get_collection("chats")
    all_chats = await chats.find({}).to_list(length=None)
    
    for chat in all_chats[:50]:  # Limit to 50 to avoid ban
        try:
            await client.leave_chat(chat["chat_id"])
            await asyncio.sleep(0.1)
        except:
            pass
    
    import sys
    sys.exit(0)


# Check for gbanned users on join
@Client.on_message(filters.new_chat_members & filters.group)
async def check_gban(client: Client, message: Message):
    gbans = await db.get_collection("gbans")
    
    for member in message.new_chat_members:
        if await gbans.find_one({"user_id": member.id}):
            try:
                await client.ban_chat_member(message.chat.id, member.id)
                await message.reply_text(f"Banned {member.mention} (globally banned user).")
            except:
                pass
