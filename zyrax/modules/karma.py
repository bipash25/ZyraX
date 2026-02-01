from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.database.mongo import db
from zyrax.utils.errors import error_handler
import time

__mod_name__ = "Karma"
__help__ = """
/karma - Check your karma
Reply with +1, thanks, ty to give karma.
Reply with -1, boo to remove karma.
"""

# Cooldown: {user_id: timestamp}
karma_cooldowns = {}

POSITIVE_TRIGGERS = ["+", "+1", "thanks", "thx", "ty", "pro", "cool", "good"]
NEGATIVE_TRIGGERS = ["-", "-1", "boo", "noob", "bad", "fuck", "shit"]

@Client.on_message(filters.group & filters.reply & ~filters.bot, group=2)
async def karma_handler(client: Client, message: Message):
    if not message.text:
        return
        
    text = message.text.lower().strip()
    sender = message.from_user
    receiver = message.reply_to_message.from_user
    
    if not receiver or receiver.id == sender.id or receiver.is_bot:
        return
        
    # Check triggers
    change = 0
    if text in POSITIVE_TRIGGERS:
        change = 1
    elif text in NEGATIVE_TRIGGERS:
        change = -1
    else:
        return # No trigger
        
    # Cooldown check
    current_time = time.time()
    if sender.id in karma_cooldowns and current_time - karma_cooldowns[sender.id] < 30:
        return # Silent fail on cooldown
        
    karma_cooldowns[sender.id] = current_time
    
    # Apply
    new_karma = await db.change_karma(receiver.id, change)
    
    direction = "increased" if change > 0 else "decreased"
    await message.reply_text(
        f"{receiver.mention}'s karma {direction} to **{new_karma}**!"
    )

@Client.on_message(filters.command("karma") & filters.group)
@error_handler
async def get_karma_cmd(client: Client, message: Message):
    user = message.from_user
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        # TODO: Lookup by username not implemented generically yet
        pass
        
    karma = await db.get_karma(user.id)
    await message.reply_text(f"**{user.mention}** has **{karma}** karma points.")
