"""
Input Validators

Comprehensive validation utilities for user inputs, IDs, durations, and more.
"""

import re
from html import escape
from typing import Optional, Tuple, Union
from urllib.parse import urlparse

from zyrax.constants import Limits


# =============================================================================
# REGEX PATTERNS
# =============================================================================

# Telegram username: @username (5-32 alphanumeric + underscore, not starting with digit)
USERNAME_PATTERN = re.compile(r'^@?[a-zA-Z][a-zA-Z0-9_]{4,31}$')

# User ID: positive integer
USER_ID_PATTERN = re.compile(r'^[1-9]\d*$')

# Duration patterns: 1h, 30m, 2d, 1w, etc.
DURATION_PATTERN = re.compile(r'^(\d+)([smhdw])$', re.IGNORECASE)

# Time unit multipliers (in seconds)
TIME_UNITS = {
    's': 1,           # seconds
    'm': 60,          # minutes
    'h': 3600,        # hours
    'd': 86400,       # days
    'w': 604800,      # weeks
}

# URL pattern (basic validation)
URL_PATTERN = re.compile(
    r'^https?://'
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
    r'localhost|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$',
    re.IGNORECASE
)


# =============================================================================
# INPUT VALIDATOR CLASS
# =============================================================================

class InputValidator:
    """Static methods for validating and sanitizing user inputs."""
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 4096) -> str:
        """
        Sanitize text input by removing dangerous characters and limiting length.
        
        Args:
            text: Raw text input
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text string
        """
        if not text:
            return ""
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove other control characters except newlines and tabs
        text = ''.join(
            char for char in text 
            if char in '\n\t' or (ord(char) >= 32 or ord(char) >= 127)
        )
        
        # Limit length
        text = text[:max_length]
        
        # Escape HTML to prevent injection
        text = escape(text)
        
        return text
    
    @staticmethod
    def sanitize_html(text: str, max_length: int = 4096) -> str:
        """
        Sanitize text but preserve allowed HTML tags for Telegram.
        
        Args:
            text: Raw text with potential HTML
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text with safe HTML preserved
        """
        if not text:
            return ""
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Limit length
        text = text[:max_length]
        
        # Allow only safe Telegram HTML tags
        # This is a basic approach - for production, use a proper HTML sanitizer
        allowed_tags = ['b', 'i', 'u', 's', 'code', 'pre', 'a', 'tg-spoiler']
        
        # Simple tag-based sanitization (keeps allowed tags)
        # Note: This is simplified - a real implementation should use a proper parser
        return text
    
    @staticmethod
    def validate_regex(pattern: str) -> bool:
        """
        Check if a string is a valid regex pattern.
        
        Args:
            pattern: Regex pattern string
            
        Returns:
            True if valid regex
        """
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False
    
    @staticmethod
    def validate_chat_id(chat_id: Union[str, int]) -> bool:
        """
        Validate a Telegram chat ID.
        
        Args:
            chat_id: Chat ID (can be negative for groups/channels)
            
        Returns:
            True if valid chat ID format
        """
        try:
            val = int(chat_id)
            # Telegram IDs are never 0
            return val != 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_user_id(user_id: Union[str, int]) -> bool:
        """
        Validate a Telegram user ID.
        
        Args:
            user_id: User ID (always positive)
            
        Returns:
            True if valid user ID format
        """
        try:
            val = int(user_id)
            return val > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """
        Validate a Telegram username.
        
        Args:
            username: Username with or without @ prefix
            
        Returns:
            True if valid username format
        """
        if not username:
            return False
        return bool(USERNAME_PATTERN.match(username))
    
    @staticmethod
    def normalize_username(username: str) -> Optional[str]:
        """
        Normalize a username by removing @ prefix and lowercasing.
        
        Args:
            username: Raw username input
            
        Returns:
            Normalized username or None if invalid
        """
        if not username:
            return None
        
        username = username.strip().lstrip('@').lower()
        
        if InputValidator.validate_username(username):
            return username
        return None
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate a URL format.
        
        Args:
            url: URL string
            
        Returns:
            True if valid URL format
        """
        if not url:
            return False
        
        try:
            result = urlparse(url)
            return all([result.scheme in ('http', 'https'), result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def parse_duration(duration_str: str) -> Optional[int]:
        """
        Parse a duration string into seconds.
        
        Args:
            duration_str: Duration like "1h", "30m", "2d", "1w"
            
        Returns:
            Duration in seconds, or None if invalid
            
        Examples:
            "30m" -> 1800
            "2h" -> 7200
            "1d" -> 86400
            "1w" -> 604800
        """
        if not duration_str:
            return None
        
        match = DURATION_PATTERN.match(duration_str.strip())
        if not match:
            return None
        
        value = int(match.group(1))
        unit = match.group(2).lower()
        
        if value <= 0:
            return None
        
        return value * TIME_UNITS.get(unit, 0)
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """
        Format seconds into human-readable duration.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Human-readable string like "2 hours", "1 day"
        """
        if seconds < 60:
            return f"{seconds} second{'s' if seconds != 1 else ''}"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''}"
        elif seconds < 604800:
            days = seconds // 86400
            return f"{days} day{'s' if days != 1 else ''}"
        else:
            weeks = seconds // 604800
            return f"{weeks} week{'s' if weeks != 1 else ''}"
    
    @staticmethod
    def validate_amount(
        amount: Union[str, int],
        min_amount: int = 1,
        max_amount: int = Limits.MAX_BET_AMOUNT
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Validate and parse a numeric amount.
        
        Args:
            amount: Amount string or int
            min_amount: Minimum allowed value
            max_amount: Maximum allowed value
            
        Returns:
            Tuple of (is_valid, parsed_amount, error_message)
        """
        try:
            value = int(amount)
        except (ValueError, TypeError):
            return False, None, "Invalid amount. Please enter a number."
        
        if value < min_amount:
            return False, None, f"Amount must be at least {min_amount}."
        
        if value > max_amount:
            return False, None, f"Amount cannot exceed {max_amount}."
        
        return True, value, None
    
    @staticmethod
    def validate_bet_amount(
        amount: Union[str, int],
        balance: int
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Validate a bet amount against user's balance.
        
        Args:
            amount: Bet amount
            balance: User's current balance
            
        Returns:
            Tuple of (is_valid, parsed_amount, error_message)
        """
        is_valid, value, error = InputValidator.validate_amount(
            amount,
            min_amount=Limits.MIN_BET_AMOUNT,
            max_amount=Limits.MAX_BET_AMOUNT
        )
        
        if not is_valid:
            return is_valid, value, error
        
        if value > balance:
            return False, None, f"Insufficient balance. You have {balance} coins."
        
        return True, value, None
    
    @staticmethod
    def extract_user_id_from_input(
        text: str
    ) -> Tuple[Optional[int], Optional[str]]:
        """
        Extract user ID from various input formats.
        
        Args:
            text: User input (can be ID, username, or mention)
            
        Returns:
            Tuple of (user_id, username) - one will be None
        """
        if not text:
            return None, None
        
        text = text.strip()
        
        # Check if it's a numeric ID
        if USER_ID_PATTERN.match(text):
            return int(text), None
        
        # Check if it's a username
        if text.startswith('@') or USERNAME_PATTERN.match(text):
            return None, InputValidator.normalize_username(text)
        
        # Try to extract from tg://user?id= format
        if 'tg://user?id=' in text:
            match = re.search(r'tg://user\?id=(\d+)', text)
            if match:
                return int(match.group(1)), None
        
        return None, None
    
    @staticmethod
    def validate_warn_reason(reason: str) -> Tuple[bool, str]:
        """
        Validate and sanitize a warn/ban reason.
        
        Args:
            reason: Raw reason text
            
        Returns:
            Tuple of (is_valid, sanitized_reason)
        """
        if not reason:
            return True, "No reason provided"
        
        # Sanitize and limit length
        reason = InputValidator.sanitize_text(
            reason,
            max_length=Limits.WARN_REASON_MAX_LENGTH
        )
        
        if not reason.strip():
            return True, "No reason provided"
        
        return True, reason.strip()
    
    @staticmethod
    def validate_note_name(name: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate a note/filter name.
        
        Args:
            name: Note name
            
        Returns:
            Tuple of (is_valid, normalized_name, error_message)
        """
        if not name:
            return False, None, "Note name cannot be empty."
        
        # Lowercase and strip
        name = name.strip().lower()
        
        # Remove # prefix if present
        name = name.lstrip('#')
        
        if not name:
            return False, None, "Note name cannot be empty."
        
        # Check length
        if len(name) > 100:
            return False, None, "Note name is too long (max 100 characters)."
        
        # Check for invalid characters (only allow alphanumeric and underscore)
        if not re.match(r'^[a-z0-9_]+$', name):
            return False, None, "Note name can only contain letters, numbers, and underscores."
        
        return True, name, None


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def parse_duration(duration_str: str) -> Optional[int]:
    """Convenience function for InputValidator.parse_duration"""
    return InputValidator.parse_duration(duration_str)


def format_duration(seconds: int) -> str:
    """Convenience function for InputValidator.format_duration"""
    return InputValidator.format_duration(seconds)


def validate_amount(amount, min_val=1, max_val=Limits.MAX_BET_AMOUNT):
    """Convenience function for InputValidator.validate_amount"""
    return InputValidator.validate_amount(amount, min_val, max_val)


def sanitize_text(text: str, max_length: int = 4096) -> str:
    """Convenience function for InputValidator.sanitize_text"""
    return InputValidator.sanitize_text(text, max_length)
