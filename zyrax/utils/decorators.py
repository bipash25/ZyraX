from functools import wraps
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

def require_admin(permissions=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(client, message: Message, *args, **kwargs):
            if not message.from_user:
                return
            
            # Check if user is admin
            user = await message.chat.get_member(message.from_user.id)
            if user.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                return await message.reply_text("You need to be an admin to use this command!")
            
            # TODO: Check specific permissions if provided
            
            return await func(client, message, *args, **kwargs)
        return wrapper
    return decorator
