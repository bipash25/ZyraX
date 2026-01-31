import re
from html import escape

class InputValidator:
    @staticmethod
    def sanitize_text(text: str, max_length: int = 4096) -> str:
        if not text:
            return ""
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Limit length
        text = text[:max_length]
        
        # Escape HTML to prevent injection
        text = escape(text)
        
        return text
    
    @staticmethod
    def validate_regex(pattern: str) -> bool:
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False
    
    @staticmethod
    def validate_chat_id(chat_id: str) -> bool:
        # Telegram chat IDs are negative for groups/channels
        try:
            int(chat_id)
            return True
        except ValueError:
            return False
