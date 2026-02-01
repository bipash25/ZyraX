import re

def parse_duration(duration: str) -> int:
    """
    Parse a time duration string into seconds.
    Supports: s (seconds), m (minutes), h (hours), d (days), w (weeks)
    Example: '2h', '30m', '1d'
    """
    match = re.match(r'^(\d+)([smhdw])$', duration.lower())
    if not match:
        return None
    
    value = int(match.group(1))
    unit = match.group(2)
    
    if unit == 's':
        return value
    elif unit == 'm':
        return value * 60
    elif unit == 'h':
        return value * 3600
    elif unit == 'd':
        return value * 86400
    elif unit == 'w':
        return value * 604800
    
    return None
