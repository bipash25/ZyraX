"""
Time parsing utility
Converts time strings like "5m", "2h", "3d" to seconds
"""
import re
from datetime import datetime, timezone
from typing import Optional, Tuple


def now_utc() -> datetime:
    """
    Get current UTC time (timezone-aware)
    
    Returns:
        Current UTC time with timezone info
    """
    return datetime.now(timezone.utc)


def parse_time(time_string: str) -> Optional[int]:
    """
    Parse time string to seconds
    
    Supports formats:
    - 5s = 5 seconds
    - 5m = 5 minutes
    - 5h = 5 hours
    - 5d = 5 days
    - 5w = 5 weeks
    
    Args:
        time_string: Time string to parse
        
    Returns:
        Time in seconds or None if invalid
    """
    if not time_string:
        return None
    
    # Remove whitespace
    time_string = time_string.strip().lower()
    
    # Match pattern: number + unit
    match = re.match(r'^(\d+)([smhdw])$', time_string)
    
    if not match:
        return None
    
    value = int(match.group(1))
    unit = match.group(2)
    
    # Convert to seconds
    multipliers = {
        's': 1,           # seconds
        'm': 60,          # minutes
        'h': 3600,        # hours
        'd': 86400,       # days
        'w': 604800       # weeks
    }
    
    return value * multipliers[unit]


def format_time(seconds: int) -> str:
    """
    Format seconds into human-readable string
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string (e.g., "2 hours 30 minutes")
    """
    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''}"
    
    parts = []
    
    # Weeks
    if seconds >= 604800:
        weeks = seconds // 604800
        parts.append(f"{weeks} week{'s' if weeks != 1 else ''}")
        seconds %= 604800
    
    # Days
    if seconds >= 86400:
        days = seconds // 86400
        parts.append(f"{days} day{'s' if days != 1 else ''}")
        seconds %= 86400
    
    # Hours
    if seconds >= 3600:
        hours = seconds // 3600
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        seconds %= 3600
    
    # Minutes
    if seconds >= 60:
        minutes = seconds // 60
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        seconds %= 60
    
    # Remaining seconds
    if seconds > 0:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    
    return " ".join(parts)


def parse_time_with_reason(args: list) -> Tuple[Optional[int], Optional[str]]:
    """
    Parse time and reason from command arguments
    
    Args:
        args: List of command arguments (after user identifier)
        
    Returns:
        Tuple of (duration_seconds, reason)
        If no time specified, returns (None, reason)
    """
    if not args:
        return None, None
    
    # First arg might be time
    duration = parse_time(args[0])
    
    if duration:
        # Time was specified, rest is reason
        reason = " ".join(args[1:]) if len(args) > 1 else None
        return duration, reason
    else:
        # No time, all args are reason
        reason = " ".join(args) if args else None
        return None, reason


def validate_duration(seconds: int, min_seconds: int = 30, max_seconds: int = 31536000) -> Tuple[bool, str]:
    """
    Validate duration is within acceptable range
    
    Args:
        seconds: Duration in seconds
        min_seconds: Minimum allowed (default 30s)
        max_seconds: Maximum allowed (default 365 days)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if seconds < min_seconds:
        return False, f"Duration must be at least {format_time(min_seconds)}"
    
    if seconds > max_seconds:
        return False, f"Duration cannot exceed {format_time(max_seconds)}"
    
    return True, ""


# Time range constants
MIN_BAN_TIME = 30  # 30 seconds
MAX_BAN_TIME = 31536000  # 365 days
MIN_MUTE_TIME = 30  # 30 seconds
MAX_MUTE_TIME = 31536000  # 365 days