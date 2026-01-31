"""
System information - CPU, RAM, disk usage
"""
import logging
import platform
import psutil
from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import owner_only, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "sysinfo",
    "aliases": ["system", "health"],
    "description": "Get system resource usage",
    "usage": "/sysinfo",
    "category": "owner",
    "scope": ["private"]
}


@log_command
@owner_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Get system information and resource usage
    """
    msg = await update.message.reply_text("⏳ Gathering system info...")
    
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory
        memory = psutil.virtual_memory()
        memory_used = memory.used / (1024 ** 3)  # GB
        memory_total = memory.total / (1024 ** 3)  # GB
        memory_percent = memory.percent
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_used = disk.used / (1024 ** 3)  # GB
        disk_total = disk.total / (1024 ** 3)  # GB
        disk_percent = disk.percent
        
        # Network
        net_io = psutil.net_io_counters()
        sent = net_io.bytes_sent / (1024 ** 2)  # MB
        recv = net_io.bytes_recv / (1024 ** 2)  # MB
        
        # Process info
        process = psutil.Process()
        process_memory = process.memory_info().rss / (1024 ** 2)  # MB
        
        response = (
            "🖥️ <b>System Information</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            
            f"💻 <b>OS:</b> {platform.system()} {platform.release()}\n"
            f"🐍 <b>Python:</b> {platform.python_version()}\n\n"
            
            "📊 <b>Resources:</b>\n"
            f"  • CPU: {cpu_percent}% ({cpu_count} cores)\n"
            f"  • RAM: {memory_used:.1f}/{memory_total:.1f} GB ({memory_percent}%)\n"
            f"  • Disk: {disk_used:.1f}/{disk_total:.1f} GB ({disk_percent}%)\n\n"
            
            "🌐 <b>Network:</b>\n"
            f"  • Sent: {sent:.1f} MB\n"
            f"  • Received: {recv:.1f} MB\n\n"
            
            "🤖 <b>Bot Process:</b>\n"
            f"  • Memory: {process_memory:.1f} MB\n"
            f"  • Threads: {process.num_threads()}\n"
        )
        
        await msg.edit_text(response, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error gathering system info: {e}")
        await msg.edit_text(f"❌ Error: {str(e)}")

