from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from zyrax.database.mongo import db

__mod_name__ = "Shop"
__help__ = """
/shop - View the Virtual Shop
/buy <item_id> - Buy an item with ZyraCoins
/inventory - View your owned items
/settitle <title> - Set your chat title (if owned)
"""

SHOP_ITEMS = {
    "title_boss": {"name": "Title: The Boss", "cost": 1000, "type": "title", "value": "The Boss"},
    "title_rich": {"name": "Title: Richie Rich", "cost": 5000, "type": "title", "value": "Richie Rich"},
    "title_king": {"name": "Title: King of Chat", "cost": 10000, "type": "title", "value": "King of Chat"},
    "badge_vip": {"name": "Badge: VIP", "cost": 2500, "type": "badge", "value": "VIP"},
}

@Client.on_message(filters.command("shop") & filters.group)
async def shop_menu(client: Client, message: Message):
    text = "🛒 **ZyraX Virtual Shop**\n\n"
    for item_id, item in SHOP_ITEMS.items():
        text += f"▪️ **{item['name']}**\n   Cost: `{item['cost']}` ZyraCoins\n   ID: `{item_id}`\n\n"
    
    text += "Use `/buy <id>` to purchase!"
    await message.reply_text(text)

@Client.on_message(filters.command("buy") & filters.group)
async def buy_item(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /buy <item_id>")
        
    item_id = message.command[1].lower()
    if item_id not in SHOP_ITEMS:
        return await message.reply_text("Item not found!")
        
    item = SHOP_ITEMS[item_id]
    user_id = message.from_user.id
    
    # Check Funds
    user_data = await db.get_user_data(user_id)
    balance = user_data.get("balance", 0) if user_data else 0
    
    if balance < item["cost"]:
        return await message.reply_text(f"💸 You need `{item['cost']}` coins! You have `{balance}`.")
        
    # Check if already owned
    inventory = user_data.get("inventory", [])
    if item_id in inventory:
        return await message.reply_text("You already own this item!")
        
    # Transaction
    await db.add_balance(user_id, -item["cost"])
    await db.add_inventory_item(user_id, item_id)
    
    await message.reply_text(f"🎉 Purchased **{item['name']}** for `{item['cost']}` coins!")

@Client.on_message(filters.command("inventory"))
async def inventory(client: Client, message: Message):
    user_data = await db.get_user_data(message.from_user.id)
    if not user_data or "inventory" not in user_data or not user_data["inventory"]:
        return await message.reply_text("Your inventory is empty.")
        
    text = "🎒 **Your Inventory:**\n\n"
    for item_id in user_data["inventory"]:
        if item_id in SHOP_ITEMS:
            text += f"▪️ {SHOP_ITEMS[item_id]['name']}\n"
        else:
            text += f"▪️ {item_id} (Legacy)\n"
            
    current_title = user_data.get("title", "None")
    text += f"\nActive Title: **{current_title}**"
    await message.reply_text(text)

@Client.on_message(filters.command("settitle") & filters.group)
async def set_title(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /settitle <text>")
        
    title_text = message.text.split(None, 1)[1]
    user_id = message.from_user.id
    user_data = await db.get_user_data(user_id)
    inventory = user_data.get("inventory", [])
    
    # Verify ownership of a title matching the text OR just check if they own ANY title item?
    # For now, let's say they can only set titles they BOUGHT.
    # Logic: Check if they own an item of type 'title' with value == title_text
    
    owned_titles = [SHOP_ITEMS[i]["value"] for i in inventory if i in SHOP_ITEMS and SHOP_ITEMS[i]["type"] == "title"]
    
    if title_text not in owned_titles:
        return await message.reply_text(f"You don't own the title '{title_text}'. Check /shop!")
        
    await db.set_title(user_id, title_text)
    await message.reply_text(f"✅ Title set to: **{title_text}**")
