from pyrogram import Client, filters
from pyrogram.types import Message
import subprocess
import shutil
from zyrax.config import Config

__mod_name__ = "System"
__help__ = """
/gpu - Check GPU Status (Owner Only)
/sysinfo - Basic System Info (Owner Only)
"""

OWNER_ID = Config.OWNER_ID

@Client.on_message(filters.command("gpu") & filters.user(OWNER_ID))
async def gpu_check(client: Client, message: Message):
    if not shutil.which("nvidia-smi"):
        await message.reply_text("❌ **No NVIDIA GPU detected.**\n`nvidia-smi` command not found.")
        return

    msg = await message.reply_text("🔍 Checking GPU...")
    try:
        output = subprocess.check_output("nvidia-smi", shell=True, stderr=subprocess.STDOUT)
        text = output.decode("utf-8")
        if len(text) > 4000:
            text = text[:4000] + "\n..."
        await msg.edit_text(f"✅ **GPU Detected!**\n```\n{text}\n```")
    except Exception as e:
        await msg.edit_text(f"❌ **Error Checking GPU:**\n`{str(e)}`")

@Client.on_message(filters.command("sysinfo") & filters.user(OWNER_ID))
async def sysinfo(client: Client, message: Message):
    import platform
    import psutil
    
    uname = platform.uname()
    mem = psutil.virtual_memory()
    
    text = f"🖥 **System Info**\n"
    text += f"**OS:** {uname.system} {uname.release} ({uname.version})\n"
    text += f"**Machine:** {uname.machine}\n"
    text += f"**Processor:** {uname.processor}\n"
    text += f"**RAM:** {getattr(mem, 'percent', 'N/A')}%\n"
    
    await message.reply_text(text)
