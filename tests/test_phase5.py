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
mock_db.cache.get = AsyncMock(return_value=None)
mock_db.cache.set = AsyncMock()

sys.modules["pyrogram"] = MagicMock()
sys.modules["pyrogram.types"] = MagicMock()
sys.modules["pyrogram.errors"] = MagicMock() # Add this line
sys.modules["zyrax.utils.ratelimit"] = MagicMock()
def mock_rate_limit(*args, **kwargs):
    def decorator(func):
        return func
    return decorator
sys.modules["zyrax.utils.ratelimit"].rate_limit = mock_rate_limit

# Mock Client.on_message decorator
def mock_on_message(*args, **kwargs):
    def decorator(func):
        return func
    return decorator
sys.modules["pyrogram"].Client.on_message = mock_on_message

from zyrax.modules.fun import coin, choose
from zyrax.modules.utilities import ping

@pytest.mark.asyncio
async def test_fun_coin():
    client = MagicMock()
    message = MagicMock()
    message.reply_text = AsyncMock()
    
    await coin(client, message)
    message.reply_text.assert_called()
    args = message.reply_text.call_args[0][0]
    assert "Heads" in args or "Tails" in args

@pytest.mark.asyncio
async def test_fun_choose():
    client = MagicMock()
    message = MagicMock()
    message.command = ["/choice", "A", "B"]
    message.text = "/choice A, B"
    message.reply_text = AsyncMock()
    
    await choose(client, message)
    message.reply_text.assert_called()
    args = message.reply_text.call_args[0][0]
    assert "A" in args or "B" in args

@pytest.mark.asyncio
async def test_utils_ping():
    client = MagicMock()
    message = MagicMock()
    message.reply_text = AsyncMock()
    # Mock return of reply_text (the message sent) to allow edit_text
    sent_message = MagicMock()
    sent_message.edit_text = AsyncMock()
    message.reply_text.return_value = sent_message
    
    await ping(client, message)
    message.reply_text.assert_called_with("Pong!")
    sent_message.edit_text.assert_called()
