import pytest
import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

# Mock database before importing modules that use it
sys.modules["zyrax.database.mongo"] = MagicMock()
sys.modules["zyrax.database.mongo"].db = MagicMock()

# Mock pyrogram imports
mock_pyrogram = MagicMock()
sys.modules["pyrogram"] = mock_pyrogram
sys.modules["pyrogram.types"] = MagicMock()
sys.modules["pyrogram.enums"] = MagicMock()
sys.modules["pyrogram.errors"] = MagicMock()

from zyrax.utils.time_parser import parse_duration
# Now import welcome module. It will use the mocks.
from zyrax.modules.welcome import format_welcome

def test_parse_duration():
    assert parse_duration("10s") == 10
    assert parse_duration("1m") == 60
    assert parse_duration("2h") == 7200
    assert parse_duration("1d") == 86400
    assert parse_duration("1w") == 604800
    assert parse_duration("invalid") is None
    assert parse_duration("10x") is None

@pytest.mark.asyncio
async def test_format_welcome():
    # Mock user and chat objects
    user = MagicMock()
    user.first_name = "John"
    user.username = "john_doe"
    user.mention = "[John](tg://user?id=123)"
    
    chat = MagicMock()
    chat.title = "My Group"
    
    template = "Hello {first}, welcome to {chatname}! Mention: {mention}, Username: {username}"
    expected = "Hello John, welcome to My Group! Mention: [John](tg://user?id=123), Username: @john_doe"
    
    result = await format_welcome(template, user, chat)
    assert result == expected

    # Test without username
    user.username = None
    expected_no_user = "Hello John, welcome to My Group! Mention: [John](tg://user?id=123), Username: [John](tg://user?id=123)"
    result = await format_welcome(template, user, chat)
    assert result == expected_no_user
