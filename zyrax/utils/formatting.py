"""
ZyraX Formatting Utilities

Text formatting, button parsing, and content extraction utilities.
"""

import re
from typing import Dict, Any, Optional, Tuple, List
from pyrogram import Client
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    User, Chat
)


# =============================================================================
# MEDIA TYPE CONSTANTS
# =============================================================================

MEDIA_TYPES: List[str] = [
    "photo", "video", "audio", "voice", 
    "document", "sticker", "animation", "video_note"
]


# =============================================================================
# TEXT FORMATTING
# =============================================================================

async def format_text(text: str, user: User, chat: Chat) -> str:
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

def parse_buttons(text: str) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Parses markdown-style buttons from text.
    
    Format:
        Some text here...
        
        [Button 1](https://google.com) [Button 2](https://yahoo.com)
        [Button 3](https://bing.com)
    
    Returns:
        Tuple of (cleaned_text, InlineKeyboardMarkup or None)
    """
    buttons: List[List[InlineKeyboardButton]] = []
    lines = text.split('\n')
    new_lines: List[str] = []
    
    button_regex = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    
    for line in lines:
        matches = list(button_regex.finditer(line))
        if not matches:
            new_lines.append(line)
            continue
            
        # Check if line is ONLY buttons (no other text)
        remainder = button_regex.sub('', line).strip()
        if remainder:
            # Contains other text, keep as-is
            new_lines.append(line)
            continue
            
        # Extract buttons from this line
        row: List[InlineKeyboardButton] = []
        for match in matches:
            name = match.group(1)
            url = match.group(2)
            row.append(InlineKeyboardButton(name, url=url))
        buttons.append(row)
        
    cleaned_text = "\n".join(new_lines).strip()
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    return cleaned_text, markup


# =============================================================================
# CONTENT EXTRACTION
# =============================================================================

async def extract_content(message: Message) -> Dict[str, Any]:
    """
    Extract content from a message for saving as note/filter.
    
    Handles:
        - Reply to text message
        - Reply to media (photo, video, audio, etc.)
        - Inline text after command
    
    Args:
        message: The command message
        
    Returns:
        Dict with content data or empty dict if no content found
    """
    data: Dict[str, Any] = {}
    
    if message.reply_to_message:
        media_msg = message.reply_to_message
        
        if media_msg.text:
            data = {"type": "text", "content": media_msg.text}
        else:
            # Check for media types
            for media_type in MEDIA_TYPES:
                media = getattr(media_msg, media_type, None)
                if media:
                    file_id = media.file_id
                    data = {
                        "type": "media",
                        "media_type": media_type,
                        "file_id": file_id,
                        "caption": media_msg.caption or ""
                    }
                    break
                    
    elif len(message.command) > 2:
        # Text provided inline: /command arg1 <content>
        data = {"type": "text", "content": message.text.split(None, 2)[2]}
    
    return data


async def send_media(
    client: Client,
    chat_id: int,
    data: Dict[str, Any],
    caption: str = "",
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    reply_to_message_id: Optional[int] = None
) -> Optional[Message]:
    """
    Send cached media to a chat.
    
    Args:
        client: Pyrogram client
        chat_id: Target chat ID
        data: Media data dict with media_type and file_id
        caption: Caption text
        reply_markup: Optional inline keyboard
        reply_to_message_id: Optional message to reply to
        
    Returns:
        Sent message or None on failure
    """
    media_type = data.get("media_type")
    file_id = data.get("file_id")
    
    if not media_type or not file_id:
        return None
        
    send_methods = {
        "photo": client.send_photo,
        "video": client.send_video,
        "audio": client.send_audio,
        "voice": client.send_voice,
        "document": client.send_document,
        "animation": client.send_animation,
        "video_note": client.send_video_note,
    }
    
    method = send_methods.get(media_type)
    
    if not method:
        # Sticker is special - no caption
        if media_type == "sticker":
            return await client.send_sticker(
                chat_id, file_id,
                reply_markup=reply_markup,
                reply_to_message_id=reply_to_message_id
            )
        return None
    
    # For video_note, no caption allowed
    if media_type == "video_note":
        return await method(
            chat_id, file_id,
            reply_markup=reply_markup,
            reply_to_message_id=reply_to_message_id
        )
    
    return await method(
        chat_id, file_id,
        caption=caption,
        reply_markup=reply_markup,
        reply_to_message_id=reply_to_message_id
    )


async def reply_media(
    message: Message,
    data: Dict[str, Any],
    caption: str = "",
    reply_markup: Optional[InlineKeyboardMarkup] = None
) -> Optional[Message]:
    """
    Reply with cached media.
    
    Args:
        message: Message to reply to
        data: Media data dict with media_type and file_id
        caption: Caption text
        reply_markup: Optional inline keyboard
        
    Returns:
        Sent message or None on failure
    """
    media_type = data.get("media_type")
    file_id = data.get("file_id")
    
    if not media_type or not file_id:
        return None
        
    reply_methods = {
        "photo": message.reply_photo,
        "video": message.reply_video,
        "audio": message.reply_audio,
        "voice": message.reply_voice,
        "document": message.reply_document,
        "animation": message.reply_animation,
    }
    
    method = reply_methods.get(media_type)
    
    if not method:
        if media_type == "sticker":
            return await message.reply_sticker(file_id, reply_markup=reply_markup)
        return None
    
    return await method(file_id, caption=caption, reply_markup=reply_markup)
