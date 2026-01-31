import pytest
import time
import sys
import os
from unittest.mock import MagicMock
sys.path.append(os.getcwd())
sys.modules["pyrogram"] = MagicMock()
sys.modules["pyrogram.types"] = MagicMock()
from zyrax.utils.ratelimit import CommandRateLimit

def test_rate_limiter():
    limiter = CommandRateLimit()
    user_id = 12345
    command = "test_cmd"
    
    # Should allow 2 attempts
    assert limiter.check(user_id, command, max_attempts=2, window=1) is True
    assert limiter.check(user_id, command, max_attempts=2, window=1) is True
    
    # Should block 3rd attempt
    assert limiter.check(user_id, command, max_attempts=2, window=1) is False
    
    # Wait for window to pass
    time.sleep(1.1)
    
    # Should allow again
    result = limiter.check(user_id, command, max_attempts=2, window=1)
    print(f"After sleep result: {result}")
    assert result is True

if __name__ == "__main__":
    test_rate_limiter()
    print("Test passed!")
