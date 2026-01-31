"""
Execute shell commands - EXTREMELY DANGEROUS
"""
import logging
import subprocess
from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import owner_only, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "shell",
    "aliases": ["sh", "bash"],
    "description": "Execute shell commands (EXTREMELY DANGEROUS)",
    "usage": "/shell <command>",
    "category": "owner",
    "scope": ["private"]
}


@log_command
@owner_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Execute shell command - EXTREMELY DANGEROUS
    """
    if not context.args:
        await update.message.reply_html(
            "⚠️ <b>Shell Command Executor</b>\n\n"
            "<b>Usage:</b> /shell &lt;command&gt;\n\n"
            "<b>WARNING:</b> This is EXTREMELY dangerous!\n"
            "You can break the entire system."
        )
        return
    
    command = " ".join(context.args)
    
    msg = await update.message.reply_text("⏳ Executing shell command...")
    
    try:
        # Execute command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Get output
        output = result.stdout or result.stderr or "No output"
        
        # Limit output size
        if len(output) > 4000:
            output = output[:4000] + "\n\n... (truncated)"
        
        await msg.edit_text(
            f"🖥️ <b>Shell Output:</b>\n\n"
            f"<code>{output}</code>\n\n"
            f"Exit code: {result.returncode}",
            parse_mode='HTML'
        )
        
        logger.warning(f"Owner executed shell command: {command}")
        
    except subprocess.TimeoutExpired:
        await msg.edit_text("❌ Command timed out (30s limit)")
    except Exception as e:
        logger.error(f"Error executing shell command: {e}")
        await msg.edit_text(f"❌ Error: {str(e)}")

