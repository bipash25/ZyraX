from pyrogram import Client
from pyrogram.types import Message, User
from typing import Optional, Union

async def extract_user(client: Client, message: Message) -> Optional[Union[User, int]]:
    """
    Extracts user from message reply or command arguments.
    Returns User object or ID (int) or None.
    """
    if message.reply_to_message:
        return message.reply_to_message.from_user

    if len(message.command) > 1:
        user_arg = message.command[1]
        
        # Check for mention or username
        if user_arg.startswith("@"):
            try:
                return await client.get_users(user_arg)
            except Exception:
                return None
        
        # Check for ID
        if user_arg.isdigit():
            try:
                return await client.get_users(int(user_arg))
            except Exception:
                # If get_users fails (user not seen), return int ID
                return int(user_arg)
                
        # Try as username without @
        try:
            return await client.get_users(user_arg)
        except Exception:
            pass
            
    return None
