import re
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def format_text(text: str, user, chat):
    if not text:
        return ""
    
    return text.format(
        first=user.first_name,
        last=user.last_name or "",
        username=f"@{user.username}" if user.username else user.mention,
        mention=user.mention,
        id=user.id,
        chatname=chat.title,
        chatid=chat.id
    )

def parse_buttons(text: str):
    """
    Parses markdown-style buttons from text.
    Format:
    Some text here...
    
    [Button 1](https://google.com) [Button 2](https://yahoo.com)
    [Button 3](https://bing.com)
    
    Returns: (cleaned_text, InlineKeyboardMarkup)
    """
    buttons = []
    lines = text.split('\n')
    new_lines = []
    
    # Simple parser: If a line consists ONLY of buttons, it's a button line.
    # Button regex: \[([^\]]+)\]\(([^)]+)\)
    button_regex = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    
    for line in lines:
        matches = list(button_regex.finditer(line))
        if not matches:
            new_lines.append(line)
            continue
            
        # Check if the line is ONLY buttons (ignoring spaces)
        # We construct what the line would look like if we removed all matches
        remainder = button_regex.sub('', line).strip()
        if remainder:
            # Contains other text, so not a button line (or buttons inline in text)
            # For simplicity, we only parse buttons if they are on their own lines?
            # Or we strip them from text?
            # Standard bot behavior: Buttons defined at end or mixed? 
            # Let's assume buttons are defined at the end usually, or anywhere.
            # If we extract them, we should remove them from text.
            new_lines.append(line) # Keep text as is for now if mixed
            continue
            
        # It's a button line
        row = []
        for match in matches:
            name = match.group(1)
            url = match.group(2)
            # Check for special schemes like 'note://' or 'btn://' later
            row.append(InlineKeyboardButton(name, url=url))
        buttons.append(row)
        
    return "\n".join(new_lines).strip(), InlineKeyboardMarkup(buttons) if buttons else None
