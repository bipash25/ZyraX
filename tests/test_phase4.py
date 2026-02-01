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

# Async mocks
mock_db.get_user_data = AsyncMock(return_value={"balance": 100})
mock_db.add_balance = AsyncMock()
mock_db.cache.get = AsyncMock(return_value=None)
mock_db.cache.set = AsyncMock()

sys.modules["pyrogram"] = MagicMock()
sys.modules["pyrogram.types"] = MagicMock()

# Mock Client.on_message decorator
def mock_on_message(*args, **kwargs):
    def decorator(func):
        return func
    return decorator
sys.modules["pyrogram"].Client.on_message = mock_on_message

sys.modules["zyrax.utils.ratelimit"] = MagicMock()
# Mock rate_limit decorator to just pass through
def mock_rate_limit(*args, **kwargs):
    def decorator(func):
        return func
    return decorator
sys.modules["zyrax.utils.ratelimit"].rate_limit = mock_rate_limit

sys.modules["zyrax.utils.users"] = MagicMock()
# Mock extract_user
async def mock_extract_user(client, message):
    return message.reply_to_message.from_user if message.reply_to_message else None
sys.modules["zyrax.utils.users"].extract_user = mock_extract_user

from zyrax.modules.economy import balance_command, pay_command

@pytest.mark.asyncio
async def test_balance():
    client = MagicMock()
    message = MagicMock()
    message.from_user.id = 123
    message.from_user.first_name = "Test"
    message.reply_to_message = None
    message.command = ["/balance"]
    message.reply_text = AsyncMock() # Make awaitable
    
    await balance_command(client, message)
    
    # Check if get_user_data called
    mock_db.get_user_data.assert_called_with(123)
    # Check reply
    message.reply_text.assert_called()
    assert "100" in message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_pay():
    client = MagicMock()
    message = MagicMock()
    message.from_user.id = 1
    message.reply_to_message.from_user.id = 2
    message.reply_to_message.from_user.is_bot = False
    message.command = ["/pay", "50"]
    message.reply_text = AsyncMock() # Make awaitable
    
    await pay_command(client, message)
    
    # Verify transaction
    # add_balance called with sender -50
    mock_db.add_balance.assert_any_call(1, -50)
    # add_balance called with recipient 50
    mock_db.add_balance.assert_any_call(2, 50)
