from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from zyrax.database.mongo import db
from zyrax.utils.decorators import require_admin
from zyrax.utils.errors import error_handler
from zyrax.utils.images import generate_welcome_image
from zyrax.utils.formatting import format_text

__mod_name__ = "Welcome"
__help__ = """
/setwelcome <text> - Set a custom welcome message
/welcomemode <text|image> - Switch between text and generated image welcome
/delwelcome - Delete the custom welcome message
/setgoodbye <text> - Set a custom goodbye message
/delgoodbye - Delete the custom goodbye message
/rules - Show chat rules
/setrules <text> - Set chat rules
/clearrules - Clear chat rules

Variables for welcome/goodbye:
{first} - User's first name
{username} - User's username (or mention if none)
{mention} - User's mention
{chatname} - Chat name
{id} - User ID
"""

@Client.on_message(filters.new_chat_members & filters.group)
@error_handler
async def welcome(client: Client, message: Message):
    for member in message.new_chat_members:
        # Check if it's the bot itself
        if member.id == client.me.id:
             await message.reply_text(f"Hello! I am ZyraX. Thanks for adding me to {message.chat.title}!")
             continue

        # Get custom welcome
        welcome_data = await db.get_welcome(message.chat.id)
        
        # Determine mode (default text)
        mode = welcome_data.get("type", "text") if welcome_data else "text"
        
        if mode == "image":
             # Generate Image
            img_bio = generate_welcome_image(member.first_name, member.id, message.chat.title)
            
            caption = f"Welcome {member.mention} to **{message.chat.title}**!"
            if welcome_data and welcome_data.get("content"):
                caption = await format_text(welcome_data["content"], member, message.chat)
            
            await message.reply_photo(photo=img_bio, caption=caption)

        elif welcome_data and welcome_data.get("content"):
            # Text Mode with custom content
            content = await format_text(welcome_data["content"], member, message.chat)
            await message.reply_text(content)
        else:
            # Default welcome
            await message.reply_text(f"Welcome {member.mention} to {message.chat.title}!")

@Client.on_message(filters.command("welcomemode") & filters.group)
@require_admin()
@error_handler
async def set_welcome_mode(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /welcomemode <text|image>")
    
    mode = message.command[1].lower()
    if mode not in ["text", "image"]:
        return await message.reply_text("Invalid mode. Use 'text' or 'image'.")
    
    # We update the 'type' field using set_welcome. 
    # To avoid overwriting content, we first get it.
    # Actually set_welcome implementation I wrote earlier takes args separately.
    
    # Let's just update the type directly or use set_welcome if I updated it to handle partial updates.
    # The set_welcome in mongo.py I just updated:
    # if content: data["content"] = content
    # if type: data["type"] = type
    # So if I pass type only, it updates type. Good.
    
    await db.set_welcome(message.chat.id, type=mode)
    await message.reply_text(f"Welcome mode set to: **{mode}**")

@Client.on_message(filters.left_chat_member & filters.group)
@error_handler
async def goodbye(client: Client, message: Message):
    member = message.left_chat_member
    if member.id == client.me.id:
        return 
    
    # Get custom goodbye
    goodbye_data = await db.get_goodbye(message.chat.id)
    if goodbye_data and goodbye_data.get("content"):
        content = await format_text(goodbye_data["content"], member, message.chat)
        await message.reply_text(content)
    else:
        await message.reply_text(f"Goodbye {member.mention}!")

@Client.on_message(filters.command("setwelcome") & filters.group)
@require_admin()
@error_handler
async def set_welcome(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text("Usage: /setwelcome <text> or reply to a message")
    
    if message.reply_to_message:
        content = message.reply_to_message.text or message.reply_to_message.caption
    else:
        content = message.text.split(None, 1)[1]
        
    await db.set_welcome(message.chat.id, content=content)
    await message.reply_text("Welcome message set!")

@Client.on_message(filters.command("delwelcome") & filters.group)
@require_admin()
@error_handler
async def del_welcome(client: Client, message: Message):
    await db.delete_welcome(message.chat.id)
    await message.reply_text("Welcome message deleted (reset to default).")

@Client.on_message(filters.command("setgoodbye") & filters.group)
@require_admin()
@error_handler
async def set_goodbye(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text("Usage: /setgoodbye <text> or reply to a message")
    
    if message.reply_to_message:
        content = message.reply_to_message.text or message.reply_to_message.caption
    else:
        content = message.text.split(None, 1)[1]
        
    await db.set_goodbye(message.chat.id, content=content)
    await message.reply_text("Goodbye message set!")

@Client.on_message(filters.command("delgoodbye") & filters.group)
@require_admin()
@error_handler
async def del_goodbye(client: Client, message: Message):
    await db.delete_goodbye(message.chat.id)
    await message.reply_text("Goodbye message deleted (reset to default).")

# Rules System

@Client.on_message(filters.command("rules") & filters.group)
@error_handler
async def get_rules(client: Client, message: Message):
    rules = await db.get_rules(message.chat.id)
    if not rules:
        return await message.reply_text("No rules set for this chat.")
        
    # Send rules in PM if button clicked? For now just reply.
    # We can add a button "Read Rules in PM" if rules are long.
    
    if len(rules) > 500:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Read Rules", url=f"https://t.me/{client.me.username}?start=rules_{message.chat.id}")]]
        )
        await message.reply_text("The rules are quite long. Click below to read them.", reply_markup=keyboard)
    else:
        await message.reply_text(f"**Rules for {message.chat.title}:**\n\n{rules}")

@Client.on_message(filters.command("setrules") & filters.group)
@require_admin()
@error_handler
async def set_rules(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text("Usage: /setrules <text> or reply to a message")
    
    if message.reply_to_message:
        content = message.reply_to_message.text or message.reply_to_message.caption
    else:
        content = message.text.split(None, 1)[1]
        
    await db.set_rules(message.chat.id, rules=content)
    await message.reply_text("Rules set successfully!")

@Client.on_message(filters.command("clearrules") & filters.group)
@require_admin()
@error_handler
async def clear_rules(client: Client, message: Message):
    await db.set_rules(message.chat.id, rules=None)
    await message.reply_text("Rules cleared!")

# PM Handler for deep linked rules
@Client.on_message(filters.command("start") & filters.private)
async def start_rules(client: Client, message: Message):
    if len(message.command) > 1 and message.command[1].startswith("rules_"):
        chat_id = int(message.command[1].split("_")[1])
        # Since Telegram chat IDs for groups are negative, we need to handle that.
        # But deep links strip the minus sign usually? No, let's assume raw ID is passed.
        # Wait, if we pass rules_-100123, it comes as rules_-100123.
        
        rules = await db.get_rules(chat_id)
        if rules:
            await message.reply_text(f"**Rules:**\n\n{rules}")
        else:
            await message.reply_text("Rules not found or chat not accessible.")
    else:
        # Default start behavior (can import from another module or just pass)
        pass 
