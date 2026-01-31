from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from zyrax.modules import MOD_HELP

__mod_name__ = "Help"
__help__ = """
/help - Show this menu
/help <module> - Show help for a specific module
"""

@Client.on_message(filters.command("help") & filters.group)
async def help_command(client: Client, message: Message):
    if len(message.command) > 1:
        module_name = message.text.split(None, 1)[1].title()
        if module_name in MOD_HELP:
            await message.reply_text(f"**Help for {module_name}:**\n{MOD_HELP[module_name]}")
        else:
            await message.reply_text("Module not found.")
    else:
        buttons = []
        for mod in sorted(MOD_HELP.keys()):
            buttons.append(InlineKeyboardButton(mod, callback_data=f"help_mod_{mod}"))
        
        # Chunk buttons into rows of 3
        keyboard = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]
        
        await message.reply_text(
            "**ZyraX Help Menu**\nSelect a module to view help:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

@Client.on_callback_query(filters.regex(r"help_mod_(.*)"))
async def help_callback(client: Client, callback_query: CallbackQuery):
    module_name = callback_query.data.split("_")[2]
    if module_name in MOD_HELP:
        await callback_query.edit_message_text(
            f"**Help for {module_name}:**\n{MOD_HELP[module_name]}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="help_back")]])
        )
    else:
        await callback_query.answer("Module not found!", show_alert=True)

@Client.on_callback_query(filters.regex(r"help_back"))
async def help_back(client: Client, callback_query: CallbackQuery):
    buttons = []
    for mod in sorted(MOD_HELP.keys()):
        buttons.append(InlineKeyboardButton(mod, callback_data=f"help_mod_{mod}"))
    
    keyboard = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]
    
    await callback_query.edit_message_text(
        "**ZyraX Help Menu**\nSelect a module to view help:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
