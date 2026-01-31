"""
Cryptographic utilities for secure captcha handling
"""
import hashlib
import secrets


def generate_salt() -> str:
    """
    Generate a random salt for hashing
    
    Returns:
        32-character hex string
    """
    return secrets.token_hex(16)


def generate_secure_token() -> str:
    """
    Generate a secure random token for callback data
    
    Returns:
        URL-safe token string
    """
    return secrets.token_urlsafe(16)


def hash_answer(answer: str, salt: str) -> str:
    """
    Hash a captcha answer with salt using SHA256
    
    Args:
        answer: The captcha answer to hash
        salt: Random salt for hashing
    
    Returns:
        SHA256 hash as hex string
    """
    return hashlib.sha256(f"{answer}{salt}".encode()).hexdigest()


def verify_answer(user_answer: str, answer_hash: str, salt: str) -> bool:
    """
    Verify a user's answer against stored hash
    
    Args:
        user_answer: The answer provided by user
        answer_hash: Stored hash to compare against
        salt: Salt used for original hash
    
    Returns:
        True if answer matches, False otherwise
    """
    computed_hash = hash_answer(user_answer.lower(), salt)
    return computed_hash == answer_hash