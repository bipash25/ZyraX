from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps
from pyrogram.types import Message

class CommandRateLimit:
    def __init__(self):
        self.attempts = defaultdict(list)
    
    def check(self, user_id: int, command: str, max_attempts: int = 10, window: int = 60) -> bool:
        key = f"{user_id}:{command}"
        now = datetime.now()
        cutoff = now - timedelta(seconds=window)
        
        # Clean old attempts
        self.attempts[key] = [t for t in self.attempts[key] if t > cutoff]
        
        if len(self.attempts[key]) >= max_attempts:
            return False
        
        self.attempts[key].append(now)
        return True

# Decorator
rate_limiter = CommandRateLimit()

def rate_limit(max_attempts=10, window=60):
    def decorator(func):
        @wraps(func)
        async def wrapper(client, message: Message, *args, **kwargs):
            if not message.from_user:
                return await func(client, message, *args, **kwargs)
                
            if not rate_limiter.check(message.from_user.id, func.__name__, max_attempts, window):
                return await message.reply("⏳ Slow down! You are being rate limited.")
            return await func(client, message, *args, **kwargs)
        return wrapper
    return decorator
