"""
Help command - Show available commands dynamically with pagination
"""
import logging
import math
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from core.decorators import log_command

logger = logging.getLogger(__name__)

# Command metadata
COMMAND_INFO = {
    "name": "help",
    "aliases": ["commands"],
    "description": "Show available commands and their usage",
    "usage": "/help [command_name]",
    "category": "misc",
    "scope": ["private", "group", "supergroup"]
}

# Pagination settings
CATEGORIES_PER_PAGE = 8


def get_category_emoji(category: str) -> str:
    """Get emoji for command category"""
    emojis = {
        "admin": "👮",
        "moderation": "🔨",
        "warnings": "⚠️",
        "misc": "ℹ️",
        "info": "📊",
        "fun": "🎮",
        "antiflood": "🌊",
        "antiraid": "🛡️",
        "approval": "✅",
        "backup": "💾",
        "blocklists": "🚫",
        "captcha": "🔐",
        "economy": "💰",
        "federation": "🌐",
        "filters": "🔍",
        "leveling": "⭐",
        "notes": "📝",
        "greetings": "👋",
        "locks": "🔒",
        "pins": "📌",
        "profile": "👤",
        "reports": "🚨",
        "rules": "📜",
        "clean": "🧹",
        "logs": "📋",
        "owner": "👑"
    }
    return emojis.get(category.lower(), "•")


@log_command
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /help command
    
    Shows available commands grouped by category with pagination.
    If command name is provided, shows detailed help for that command.
    
    Args:
        update: Telegram update
        context: PTB context
    """
    # Get all loaded commands from context
    command_registry = context.bot_data.get('command_registry')
    
    if not command_registry:
        await update.message.reply_text(
            "⚠️ Command registry not initialized. Please restart the bot."
        )
        return
    
    # Check if specific command help requested
    if context.args:
        command_name = context.args[0].lower().lstrip('/')
        await show_command_help(update, command_registry, command_name)
        return
    
    # Show general help with categories (page 1)
    await show_general_help(update, context, command_registry, page=1)


async def show_general_help(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    command_registry: dict,
    page: int = 1
):
    """
    Show general help with command categories (with pagination)
    
    Args:
        update: Telegram update
        context: PTB context
        command_registry: Dictionary of loaded commands
        page: Current page number
    """
    chat_type = update.effective_chat.type
    
    # Group commands by category (show all, don't filter by scope)
    categories = {}
    for cmd_name, cmd_info in command_registry.items():
        category = cmd_info.get('category', 'misc')
        
        # Skip owner category in non-private chats (security)
        if category == 'owner' and chat_type != 'private':
            continue
        
        if category not in categories:
            categories[category] = []
        
        categories[category].append({
            'name': cmd_name,
            'description': cmd_info.get('description', 'No description'),
            'aliases': cmd_info.get('aliases', [])
        })
    
    # Sort categories for consistent display
    category_order = [
        'admin', 'moderation', 'warnings', 'antiflood', 'antiraid', 
        'approval', 'captcha', 'locks', 'filters', 'blocklists',
        'notes', 'greetings', 'rules', 'federation', 'pins', 
        'reports', 'clean', 'logs', 'backup', 'leveling', 
        'economy', 'profile', 'fun', 'info', 'misc', 'owner'
    ]
    
    # Filter to only include categories that exist
    available_categories = [cat for cat in category_order if cat in categories]
    
    # Calculate pagination
    total_categories = len(available_categories)
    total_pages = math.ceil(total_categories / CATEGORIES_PER_PAGE)
    page = max(1, min(page, total_pages))  # Clamp page number
    
    start_idx = (page - 1) * CATEGORIES_PER_PAGE
    end_idx = start_idx + CATEGORIES_PER_PAGE
    page_categories = available_categories[start_idx:end_idx]
    
    # Build help message
    message = "<b>📚 ZyraX Bot - Command Categories</b>\n\n"
    message += "🔹 Select a category to view available commands\n"
    message += "🔹 Use <code>/help &lt;command&gt;</code> for detailed usage\n\n"
    message += f"📊 <b>Total Commands:</b> {len(command_registry)}\n"
    message += f"📂 <b>Categories:</b> {total_categories}\n"
    message += f"📄 <b>Page:</b> {page}/{total_pages}"
    
    # Create inline keyboard for categories
    keyboard = []
    row = []
    for i, category in enumerate(page_categories):
        emoji = get_category_emoji(category)
        cmd_count = len(categories[category])
        row.append(InlineKeyboardButton(
            f"{emoji} {category.title()} ({cmd_count})",
            callback_data=f"help_cat:{category}"
        ))
        
        if (i + 1) % 2 == 0:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    # Add pagination buttons
    if total_pages > 1:
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"help_page:{page-1}"))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"help_page:{page+1}"))
        if nav_row:
            keyboard.append(nav_row)
    
    # Add close button
    keyboard.append([InlineKeyboardButton("❌ Close", callback_data="help_close")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_html(message, reply_markup=reply_markup)


async def show_general_help_inline(
    query, 
    context: ContextTypes.DEFAULT_TYPE, 
    command_registry: dict,
    page: int = 1
):
    """
    Show general help for inline editing (with pagination)
    
    Args:
        query: Callback query
        context: PTB context
        command_registry: Dictionary of loaded commands
        page: Current page number
    """
    chat_type = query.message.chat.type
    
    # Group commands by category
    categories = {}
    for cmd_name, cmd_info in command_registry.items():
        category = cmd_info.get('category', 'misc')
        
        # Skip owner category in non-private chats
        if category == 'owner' and chat_type != 'private':
            continue
        
        if category not in categories:
            categories[category] = []
        
        categories[category].append({
            'name': cmd_name,
            'description': cmd_info.get('description', 'No description'),
            'aliases': cmd_info.get('aliases', [])
        })
    
    # Sort categories
    category_order = [
        'admin', 'moderation', 'warnings', 'antiflood', 'antiraid', 
        'approval', 'captcha', 'locks', 'filters', 'blocklists',
        'notes', 'greetings', 'rules', 'federation', 'pins', 
        'reports', 'clean', 'logs', 'backup', 'leveling', 
        'economy', 'profile', 'fun', 'info', 'misc', 'owner'
    ]
    
    available_categories = [cat for cat in category_order if cat in categories]
    
    # Calculate pagination
    total_categories = len(available_categories)
    total_pages = math.ceil(total_categories / CATEGORIES_PER_PAGE)
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * CATEGORIES_PER_PAGE
    end_idx = start_idx + CATEGORIES_PER_PAGE
    page_categories = available_categories[start_idx:end_idx]
    
    # Build message
    message = "<b>📚 ZyraX Bot - Command Categories</b>\n\n"
    message += "🔹 Select a category to view available commands\n"
    message += "🔹 Use <code>/help &lt;command&gt;</code> for detailed usage\n\n"
    message += f"📊 <b>Total Commands:</b> {len(command_registry)}\n"
    message += f"📂 <b>Categories:</b> {total_categories}\n"
    message += f"📄 <b>Page:</b> {page}/{total_pages}"
    
    # Create keyboard
    keyboard = []
    row = []
    for i, category in enumerate(page_categories):
        emoji = get_category_emoji(category)
        cmd_count = len(categories[category])
        row.append(InlineKeyboardButton(
            f"{emoji} {category.title()} ({cmd_count})",
            callback_data=f"help_cat:{category}"
        ))
        
        if (i + 1) % 2 == 0:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    # Pagination
    if total_pages > 1:
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"help_page:{page-1}"))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"help_page:{page+1}"))
        if nav_row:
            keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("❌ Close", callback_data="help_close")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')


async def show_command_help(update: Update, command_registry: dict, command_name: str):
    """
    Show detailed help for a specific command
    
    Args:
        update: Telegram update
        command_registry: Dictionary of loaded commands
        command_name: Name of the command to show help for
    """
    # Find command in registry
    cmd_info = None
    actual_name = None
    
    # Check direct match
    if command_name in command_registry:
        cmd_info = command_registry[command_name]
        actual_name = command_name
    else:
        # Check aliases
        for name, info in command_registry.items():
            if command_name in info.get('aliases', []):
                cmd_info = info
                actual_name = name
                break
    
    if not cmd_info:
        await update.message.reply_html(
            f"❌ Command <code>/{command_name}</code> not found.\n\n"
            f"Use /help to see all available commands."
        )
        return
    
    # Build detailed help message
    category = cmd_info.get('category', 'misc')
    emoji = get_category_emoji(category)
    
    message = f"{emoji} <b>Command: /{actual_name}</b>\n\n"
    message += f"📝 <b>Description:</b>\n{cmd_info.get('description', 'No description')}\n\n"
    
    # Escape HTML in usage string
    import html
    usage_text = cmd_info.get('usage', f'/{actual_name}')
    usage_text = html.escape(usage_text)
    message += f"💡 <b>Usage:</b>\n<code>{usage_text}</code>\n\n"
    
    # Add aliases if any
    aliases = cmd_info.get('aliases', [])
    if aliases:
        alias_list = ", ".join([f"/{a}" for a in aliases])
        message += f"🔄 <b>Aliases:</b> {alias_list}\n\n"
    
    # Add scope info
    scope = cmd_info.get('scope', ['private', 'group', 'supergroup'])
    scope_text = ", ".join([s.title() for s in scope])
    message += f"📍 <b>Available in:</b> {scope_text}\n\n"
    
    # Add category
    message += f"📂 <b>Category:</b> {category.title()}"
    
    # Add back button
    keyboard = [[InlineKeyboardButton("◀️ Back to Help", callback_data="help_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_html(message, reply_markup=reply_markup)


async def handle_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle callback queries from help keyboard
    
    Args:
        update: Telegram update
        context: PTB context
    """
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "help_close":
        await query.message.delete()
        return
    
    if data == "help_main":
        # Edit message to show main help (page 1)
        command_registry = context.bot_data.get('command_registry', {})
        await show_general_help_inline(query, context, command_registry, page=1)
        return
    
    if data.startswith("help_page:"):
        # Show specific page
        page = int(data.split(":", 1)[1])
        command_registry = context.bot_data.get('command_registry', {})
        await show_general_help_inline(query, context, command_registry, page=page)
        return
    
    if data.startswith("help_cat:"):
        category = data.split(":", 1)[1]
        await show_category_help(query, context, category)


async def show_category_help(query, context: ContextTypes.DEFAULT_TYPE, category: str):
    """
    Show commands in a specific category
    
    Args:
        query: Callback query
        context: PTB context
        category: Category name
    """
    command_registry = context.bot_data.get('command_registry', {})
    
    # Filter commands by category
    commands = []
    for cmd_name, cmd_info in command_registry.items():
        if cmd_info.get('category', 'misc') == category:
            commands.append({
                'name': cmd_name,
                'description': cmd_info.get('description', 'No description')
            })
    
    if not commands:
        await query.answer("No commands in this category", show_alert=True)
        return
    
    emoji = get_category_emoji(category)
    message = f"{emoji} <b>{category.upper()} Commands</b>\n\n"
    
    # Show commands in a clean list format
    for cmd in sorted(commands, key=lambda x: x['name']):
        message += f"• <code>/{cmd['name']}</code> - {cmd['description']}\n"
    
    message += "\n💡 Use <code>/help &lt;command&gt;</code> for detailed usage"
    
    # Add back button
    keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="help_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')


# Register callback handler
def get_callback_handler():
    """Get the callback query handler for help buttons"""
    return CallbackQueryHandler(handle_help_callback, pattern="^help_")
