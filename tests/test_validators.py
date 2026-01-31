import pytest
from zyrax.utils.validators import InputValidator

def test_sanitize_text():
    # Test valid text
    assert InputValidator.sanitize_text("Hello World") == "Hello World"
    
    # Test html escaping
    assert InputValidator.sanitize_text("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"
    
    # Test null bytes
    assert InputValidator.sanitize_text("Null\x00Byte") == "NullByte"
    
    # Test length limit
    long_text = "a" * 5000
    assert len(InputValidator.sanitize_text(long_text)) == 4096

def test_validate_chat_id():
    assert InputValidator.validate_chat_id("123456") is True
    assert InputValidator.validate_chat_id("-100123456789") is True
    assert InputValidator.validate_chat_id("invalid") is False

def test_validate_regex():
    assert InputValidator.validate_regex(r"^test$") is True
    assert InputValidator.validate_regex(r"[") is False # Invalid regex
