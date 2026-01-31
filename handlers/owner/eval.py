"""
Evaluate Python code - DANGEROUS, owner only
"""
import logging
import io
import sys
import traceback
from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import owner_only, log_command

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "eval",
    "aliases": ["exec", "py"],
    "description": "Execute Python code (DANGEROUS)",
    "usage": "/eval <code>",
    "category": "owner",
    "scope": ["private"]
}


@log_command
@owner_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Execute Python code - EXTREMELY DANGEROUS
    """
    if not context.args:
        await update.message.reply_html(
            "⚠️ <b>Python Evaluator</b>\n\n"
            "<b>Usage:</b> /eval &lt;code&gt;\n\n"
            "<b>WARNING:</b> This is extremely dangerous!\n"
            "Only use if you know what you're doing."
        )
        return
    
    code = " ".join(context.args)
    
    # If code is in reply, use that
    if update.message.reply_to_message and update.message.reply_to_message.text:
        code = update.message.reply_to_message.text
    
    msg = await update.message.reply_text("⏳ Executing...")
    
    try:
        # Capture stdout
        old_stdout = sys.stdout
        redirected_output = sys.stdout = io.StringIO()
        
        # Create execution environment
        exec_env = {
            'update': update,
            'context': context,
            'bot': context.bot,
            'db': context.application.bot_data.get('database'),
            'cache': context.application.bot_data.get('cache'),
            'scheduler': context.application.bot_data.get('scheduler'),
            'logger': logger
        }
        
        # Execute code
        try:
            exec(code, exec_env)
        except Exception as e:
            sys.stdout = old_stdout
            error_trace = traceback.format_exc()
            await msg.edit_text(
                f"❌ <b>Execution Error:</b>\n\n"
                f"<code>{error_trace}</code>",
                parse_mode='HTML'
            )
            return
        
        # Get output
        sys.stdout = old_stdout
        output = redirected_output.getvalue()
        
        if not output:
            output = "✅ Code executed successfully (no output)"
        
        # Limit output size
        if len(output) > 4000:
            output = output[:4000] + "\n\n... (truncated)"
        
        await msg.edit_text(
            f"✅ <b>Execution Result:</b>\n\n"
            f"<code>{output}</code>",
            parse_mode='HTML'
        )
        
        logger.warning(f"Owner executed code: {code[:100]}")
        
    except Exception as e:
        logger.error(f"Error in eval command: {e}")
        await msg.edit_text(f"❌ Error: {str(e)}")

