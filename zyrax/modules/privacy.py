from pyrogram import Client, filters
from pyrogram.types import Message
from zyrax.database.mongo import db
from zyrax.utils.errors import error_handler
import json
import os

__mod_name__ = "Privacy"
__help__ = """
/mydata - Export all your data (GDPR)
/deletedata - Delete all your data from the bot (GDPR)
"""

@Client.on_message(filters.command("mydata"))
@error_handler
async def mydata(client: Client, message: Message):
    user_id = message.from_user.id
    msg = await message.reply_text("Exporting your data...")
    
    data = await db.get_user_full_data(user_id)
    if not data:
        return await msg.edit_text("No data found for you.")
    
    # Convert ObjectIds to str
    def json_serial(obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return str(obj)

    file_path = f"downloads/{user_id}_data.json"
    with open(file_path, "w") as f:
        json.dump(data, f, default=json_serial, indent=4)
        
    await message.reply_document(file_path, caption="Here is all the data I have stored about you.")
    os.remove(file_path)
    await msg.delete()

@Client.on_message(filters.command("deletedata"))
async def deletedata(client: Client, message: Message):
    # Confirm
    if len(message.command) < 2 or message.command[1] != "confirm":
        return await message.reply_text(
            "⚠️ **Danger Zone**\n"
            "This will permanently delete your XP, Balance, Inventory, and Warning history.\n"
            "To confirm, type: `/deletedata confirm`"
        )
    
    user_id = message.from_user.id
    await db.delete_user_data(user_id)
    await message.reply_text("✅ All your data has been purged from our database.")
