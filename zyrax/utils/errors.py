from pyrogram.errors import (
    FloodWait, UserNotParticipant, ChatAdminRequired,
    MessageDeleteForbidden, RPCError
)
import asyncio
from functools import wraps
from zyrax.utils.logger import logger
from zyrax.config import Config

class ErrorHandler:
    @staticmethod
    async def handle(client, message, error):
        if isinstance(error, FloodWait):
            logger.warning(f"FloodWait: Sleeping for {error.value}s")
            await message.reply(f"⏳ Flood control. Retry in {error.value}s")
            # We don't auto-sleep here to avoid blocking, just warn user
            
        elif isinstance(error, ChatAdminRequired):
            await message.reply("❌ I need admin rights to do this!")
            
        elif isinstance(error, UserNotParticipant):
            await message.reply("⚠️ User is not in this chat")
            
        elif isinstance(error, MessageDeleteForbidden):
            await message.reply("❌ I can't delete that message (too old or not mine)")
            
        else:
            logger.error(f"Unhandled error in {message.chat.id}: {error}", exc_info=True)
            await message.reply("⚠️ Something went wrong. Error logged.")
            
            # Optional: Send to owner
            if Config.OWNER_ID:
                try:
                    await client.send_message(
                        Config.OWNER_ID,
                        f"🚨 Error in chat {message.chat.id}:\n{str(error)}"
                    )
                except:
                    pass

def error_handler(func):
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        try:
            return await func(client, message, *args, **kwargs)
        except Exception as e:
            await ErrorHandler.handle(client, message, e)
    return wrapper
