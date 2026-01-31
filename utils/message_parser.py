"""
Message parser for custom formatting
Supports markdown, buttons, and variable filling
"""
import re
import html
from typing import Dict, List, Tuple, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def parse_filling_variables(text: str, context: Dict[str, str]) -> str:
    """
    Replace filling variables in text with actual values
    
    Supported variables:
    - {first} - User's first name
    - {last} - User's last name
    - {fullname} - User's full name
    - {username} - User's username (with @)
    - {mention} - Mention user by first name
    - {id} - User's ID
    - {chatname} - Chat name
    - {count} - Member count
    
    Args:
        text: Text with variables
        context: Dictionary with variable values
        
    Returns:
        Text with variables replaced
    """
    if not text:
        return text
    
    # Define variable patterns and their replacements
    variables = {
        '{first}': context.get('first_name', ''),
        '{last}': context.get('last_name', ''),
        '{fullname}': context.get('fullname', ''),
        '{username}': context.get('username', ''),
        '{mention}': context.get('mention', ''),
        '{id}': str(context.get('user_id', '')),
        '{chatname}': context.get('chat_name', ''),
        '{count}': str(context.get('member_count', ''))
    }
    
    # Replace all variables
    result = text
    for var, value in variables.items():
        result = result.replace(var, value)
    
    return result


def parse_buttons(text: str) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Parse inline buttons from text
    
    Button format:
    [Button Text](buttonurl://example.com)
    [Button Text](buttonurl://example.com:same)  # Same row
    
    Args:
        text: Text with button markup
        
    Returns:
        Tuple of (text_without_buttons, keyboard_markup)
    """
    # Pattern for button: [Text](buttonurl://URL) or [Text](buttonurl://URL:same)
    button_pattern = r'\[([^\]]+)\]\(buttonurl://([^\)]+)\)'
    
    buttons = []
    current_row = []
    
    # Find all buttons
    for match in re.finditer(button_pattern, text):
        button_text = match.group(1)
        button_data = match.group(2)
        
        # Check if button should be on same row
        same_row = False
        if ':same' in button_data:
            button_data = button_data.replace(':same', '')
            same_row = True
        
        # Create button
        button = InlineKeyboardButton(text=button_text, url=button_data)
        
        if same_row and current_row:
            # Add to current row
            current_row.append(button)
        else:
            # Start new row
            if current_row:
                buttons.append(current_row)
            current_row = [button]
    
    # Add last row if exists
    if current_row:
        buttons.append(current_row)
    
    # Remove button markup from text
    clean_text = re.sub(button_pattern, '', text).strip()
    
    # Create keyboard if buttons exist
    keyboard = InlineKeyboardMarkup(buttons) if buttons else None
    
    return clean_text, keyboard


def parse_markdown_v2(text: str) -> str:
    """
    Convert simple markdown to Telegram MarkdownV2
    
    Supported:
    - *bold* -> **bold**
    - _italic_ -> __italic__
    - `code` -> `code`
    - ```code block``` -> ```code block```
    - [link](url) -> [link](url)
    
    Args:
        text: Text with simple markdown
        
    Returns:
        Text with MarkdownV2 formatting
    """
    if not text:
        return text
    
    # Escape special characters for MarkdownV2 except those in code blocks
    # This is a simplified version - proper implementation would be more complex
    
    # For now, return as-is and let Telegram handle it
    return text


def escape_markdown_v2(text: str) -> str:
    """
    Escape special characters for MarkdownV2
    
    Args:
        text: Plain text
        
    Returns:
        Escaped text safe for MarkdownV2
    """
    # Characters that need escaping in MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    result = text
    for char in escape_chars:
        result = result.replace(char, f'\\{char}')
    
    return result


def parse_html(text: str) -> str:
    """
    Parse HTML tags to Telegram HTML
    
    Supported:
    - <b>bold</b>
    - <i>italic</i>
    - <u>underline</u>
    - <s>strikethrough</s>
    - <code>code</code>
    - <pre>code block</pre>
    - <a href="url">link</a>
    
    Args:
        text: Text with HTML tags
        
    Returns:
        Text with proper HTML formatting
    """
    if not text:
        return text
    
    # Escape special HTML characters except tags
    # This is already handled by telegram's HTML parser
    return text


def format_welcome_message(
    template: str,
    user_first: str,
    user_last: str = "",
    user_username: str = "",
    user_id: int = 0,
    chat_name: str = "",
    member_count: int = 0
) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Format a welcome/goodbye message with variables and buttons
    
    Args:
        template: Message template with variables and buttons
        user_first: User's first name
        user_last: User's last name
        user_username: User's username
        user_id: User's ID
        chat_name: Chat name
        member_count: Member count
        
    Returns:
        Tuple of (formatted_message, keyboard_markup)
    """
    # Build context for variable replacement
    fullname = f"{user_first} {user_last}".strip() if user_last else user_first
    username_formatted = f"@{user_username}" if user_username else fullname
    mention = f'<a href="tg://user?id={user_id}">{html.escape(user_first)}</a>'
    
    context = {
        'first_name': html.escape(user_first),
        'last_name': html.escape(user_last) if user_last else '',
        'fullname': html.escape(fullname),
        'username': username_formatted,
        'mention': mention,
        'user_id': user_id,
        'chat_name': html.escape(chat_name),
        'member_count': member_count
    }
    
    # Parse buttons first
    text_without_buttons, keyboard = parse_buttons(template)
    
    # Replace variables
    formatted_text = parse_filling_variables(text_without_buttons, context)
    
    return formatted_text, keyboard


def extract_filter_content(message) -> Dict:
    """
    Extract content from a message for saving as filter response
    
    Args:
        message: Telegram message object
        
    Returns:
        Dictionary with content type, text, and file_id
    """
    content = {
        'type': 'text',
        'text': None,
        'file_id': None,
        'file_type': None
    }
    
    # Check for different content types
    if message.text:
        content['text'] = message.text
    elif message.caption:
        content['text'] = message.caption
    
    # Check for media
    if message.photo:
        content['type'] = 'photo'
        content['file_id'] = message.photo[-1].file_id
        content['file_type'] = 'photo'
    elif message.video:
        content['type'] = 'video'
        content['file_id'] = message.video.file_id
        content['file_type'] = 'video'
    elif message.document:
        content['type'] = 'document'
        content['file_id'] = message.document.file_id
        content['file_type'] = 'document'
    elif message.audio:
        content['type'] = 'audio'
        content['file_id'] = message.audio.file_id
        content['file_type'] = 'audio'
    elif message.voice:
        content['type'] = 'voice'
        content['file_id'] = message.voice.file_id
        content['file_type'] = 'voice'
    elif message.video_note:
        content['type'] = 'video_note'
        content['file_id'] = message.video_note.file_id
        content['file_type'] = 'video_note'
    elif message.sticker:
        content['type'] = 'sticker'
        content['file_id'] = message.sticker.file_id
        content['file_type'] = 'sticker'
    elif message.animation:
        content['type'] = 'animation'
        content['file_id'] = message.animation.file_id
        content['file_type'] = 'animation'
    
    return content