import pytest
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add project root
sys.path.append(os.getcwd())

# Setup Mocks
sys.modules["zyrax.database.mongo"] = MagicMock()
mock_db = MagicMock()
sys.modules["zyrax.database.mongo"].db = mock_db

# Async mocks for DB methods
mock_db.set_welcome = AsyncMock()
mock_db.get_welcome = AsyncMock()
mock_db.set_captcha = AsyncMock()
mock_db.get_captcha_settings = AsyncMock()
mock_db.add_blacklist = AsyncMock()

sys.modules["pyrogram"] = MagicMock()
sys.modules["pyrogram.types"] = MagicMock()
sys.modules["pyrogram.enums"] = MagicMock()
sys.modules["pyrogram.errors"] = MagicMock()

# Import modules to test
from zyrax.utils.images import generate_welcome_image
from zyrax.utils.formatting import parse_buttons, format_text

# Get the mock reference
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@pytest.mark.asyncio
async def test_image_generation():
    # Test that it returns a BytesIO object
    bio = generate_welcome_image("TestUser", 12345, "Test Chat")
    assert bio is not None
    assert bio.tell() == 0 # Check if seek(0) was called

@pytest.mark.asyncio
async def test_format_welcome():
    user = MagicMock()
    user.first_name = "Alice"
    user.username = "alice"
    user.mention = "@alice"
    user.id = 123
    
    chat = MagicMock()
    chat.title = "Wonderland"
    chat.id = 999
    
    template = "Hi {first}, welcome to {chatname}"
    result = await format_text(template, user, chat)
    assert result == "Hi Alice, welcome to Wonderland"

def test_parse_buttons():
    # Reset mock
    InlineKeyboardMarkup.reset_mock()
    InlineKeyboardButton.reset_mock()
    
    # Test 1: Buttons at end
    text = "Hello world\n\n[Google](https://google.com)"
    cleaned, markup = parse_buttons(text)
    
    assert cleaned == "Hello world"
    # Verify InlineKeyboardMarkup was initialized
    assert InlineKeyboardMarkup.called
    # Get arguments passed to constructor
    args, kwargs = InlineKeyboardMarkup.call_args
    buttons = args[0]
    assert len(buttons) == 1
    assert len(buttons[0]) == 1
    # Check button details (InlineKeyboardButton is also a mock)
    # We can check if InlineKeyboardButton was called with correct args
    # But since we construct it inside, we can inspect the list passed to Markup
    btn_mock = buttons[0][0]
    # This btn_mock is the return value of InlineKeyboardButton("Google", url="...")
    # So we can't easily check properties unless we spy on InlineKeyboardButton constructor calls too
    # But checking that we passed a list of lists to Markup is decent enough verification of structure parsing
    
    # Let's verify InlineKeyboardButton calls
    # Note: InlineKeyboardButton is called for each button.
    # We expect call("Google", url="https://google.com")
    
    # Since we can't easily map which call corresponds to which position in the list (without complexity),
    # let's just check if it was called with these args.
    InlineKeyboardButton.assert_any_call("Google", url="https://google.com")


    # Test 2: Multiple buttons same row
    InlineKeyboardMarkup.reset_mock()
    text = "Click below\n[Google](https://google.com) [Yahoo](https://yahoo.com)"
    cleaned, markup = parse_buttons(text)
    assert cleaned == "Click below"
    args, _ = InlineKeyboardMarkup.call_args
    buttons = args[0]
    assert len(buttons) == 1
    assert len(buttons[0]) == 2 # 1 row, 2 cols

    # Test 3: Multiple rows
    InlineKeyboardMarkup.reset_mock()
    text = "Menu\n[One](url1)\n[Two](url2)"
    cleaned, markup = parse_buttons(text)
    assert cleaned == "Menu"
    args, _ = InlineKeyboardMarkup.call_args
    buttons = args[0]
    assert len(buttons) == 2 # 2 rows
    assert len(buttons[0]) == 1
    assert len(buttons[1]) == 1

    # Test 4: No buttons
    InlineKeyboardMarkup.reset_mock()
    text = "Just text"
    cleaned, markup = parse_buttons(text)
    assert cleaned == "Just text"
    assert markup is None
    assert not InlineKeyboardMarkup.called

