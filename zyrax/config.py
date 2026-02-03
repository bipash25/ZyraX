"""
ZyraX Bot Configuration

Loads and validates all environment variables required for the bot.
"""

import os
import sys
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass


class Config:
    """
    Bot configuration loaded from environment variables.
    
    Required environment variables:
        - API_ID: Telegram API ID
        - API_HASH: Telegram API Hash
        - BOT_TOKEN: Bot token from @BotFather
        - MONGO_URL: MongoDB connection string
        - OWNER_ID: Bot owner's Telegram user ID
    
    Optional environment variables:
        - REDIS_URL: Redis connection string (default: redis://localhost:6379)
        - OPENAI_API_KEY: OpenAI API key for image generation
        - GEMINI_API_KEYS: Comma-separated Gemini API keys
        - WEBHOOK_SECRET: Secret for webhook authentication
        - DASHBOARD_PORT: Dashboard port (default: 8080)
        - DASHBOARD_HOST: Dashboard host (default: 0.0.0.0)
        - LOG_LEVEL: Logging level (default: INFO)
        - DEBUG: Enable debug mode (default: false)
    """
    
    # Required configurations
    API_ID: int
    API_HASH: str
    BOT_TOKEN: str
    MONGO_URL: str
    OWNER_ID: int
    
    # Optional configurations with defaults
    REDIS_URL: str = "redis://localhost:6379"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEYS: List[str] = []
    WEBHOOK_SECRET: str = ""
    DASHBOARD_PORT: int = 8080
    DASHBOARD_HOST: str = "0.0.0.0"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    
    # Bot name (set after validation)
    BOT_NAME: str = "ZyraX"
    
    # Internal state
    _validated: bool = False
    
    @classmethod
    def _get_required(cls, key: str) -> str:
        """Get a required environment variable or raise an error."""
        value = os.getenv(key)
        if not value or value.strip() == "":
            raise ConfigurationError(
                f"Missing required environment variable: {key}\n"
                f"Please set {key} in your .env file or environment."
            )
        return value.strip()
    
    @classmethod
    def _get_optional(cls, key: str, default: str = "") -> str:
        """Get an optional environment variable with a default."""
        value = os.getenv(key, default)
        return value.strip() if value else default
    
    @classmethod
    def _get_bool(cls, key: str, default: bool = False) -> bool:
        """Get a boolean environment variable."""
        value = os.getenv(key, "").lower().strip()
        if value in ("true", "1", "yes", "on"):
            return True
        if value in ("false", "0", "no", "off", ""):
            return default
        return default
    
    @classmethod
    def _get_int(cls, key: str, default: int = 0, required: bool = False) -> int:
        """Get an integer environment variable."""
        value = os.getenv(key)
        
        if required and (not value or value.strip() == ""):
            raise ConfigurationError(f"Missing required environment variable: {key}")
        
        if not value or value.strip() == "":
            return default
        
        try:
            return int(value.strip())
        except ValueError:
            raise ConfigurationError(
                f"Invalid value for {key}: '{value}' is not a valid integer"
            )
    
    @classmethod
    def _get_list(cls, key: str, separator: str = ",") -> List[str]:
        """Get a list environment variable (comma-separated by default)."""
        value = os.getenv(key, "")
        if not value:
            return []
        return [item.strip() for item in value.split(separator) if item.strip()]
    
    @classmethod
    def validate(cls) -> None:
        """
        Validate and load all configuration values.
        
        Raises:
            ConfigurationError: If required configuration is missing or invalid
        """
        if cls._validated:
            return
        
        errors: List[str] = []
        
        # Load required configurations
        try:
            cls.API_ID = cls._get_int("API_ID", required=True)
            if cls.API_ID <= 0:
                errors.append("API_ID must be a positive integer")
        except ConfigurationError as e:
            errors.append(str(e))
        
        try:
            cls.API_HASH = cls._get_required("API_HASH")
            if len(cls.API_HASH) != 32:
                errors.append(f"API_HASH should be 32 characters, got {len(cls.API_HASH)}")
        except ConfigurationError as e:
            errors.append(str(e))
        
        try:
            cls.BOT_TOKEN = cls._get_required("BOT_TOKEN")
            if ":" not in cls.BOT_TOKEN:
                errors.append("BOT_TOKEN format is invalid (should contain ':')")
        except ConfigurationError as e:
            errors.append(str(e))
        
        try:
            cls.MONGO_URL = cls._get_required("MONGO_URL")
            if not cls.MONGO_URL.startswith(("mongodb://", "mongodb+srv://")):
                errors.append("MONGO_URL should start with 'mongodb://' or 'mongodb+srv://'")
        except ConfigurationError as e:
            errors.append(str(e))
        
        try:
            cls.OWNER_ID = cls._get_int("OWNER_ID", required=True)
            if cls.OWNER_ID <= 0:
                errors.append("OWNER_ID must be a positive integer")
        except ConfigurationError as e:
            errors.append(str(e))
        
        # Load optional configurations
        cls.REDIS_URL = cls._get_optional("REDIS_URL", "redis://localhost:6379")
        cls.OPENAI_API_KEY = cls._get_optional("OPENAI_API_KEY", "")
        cls.GEMINI_API_KEYS = cls._get_list("GEMINI_API_KEYS")
        cls.WEBHOOK_SECRET = cls._get_optional("WEBHOOK_SECRET", "")
        cls.DASHBOARD_PORT = cls._get_int("DASHBOARD_PORT", default=8080)
        cls.DASHBOARD_HOST = cls._get_optional("DASHBOARD_HOST", "0.0.0.0")
        cls.LOG_LEVEL = cls._get_optional("LOG_LEVEL", "INFO").upper()
        cls.DEBUG = cls._get_bool("DEBUG", False)
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if cls.LOG_LEVEL not in valid_log_levels:
            errors.append(f"LOG_LEVEL must be one of: {', '.join(valid_log_levels)}")
        
        # Check for common mistakes
        if cls.REDIS_URL and not cls.REDIS_URL.startswith("redis://"):
            errors.append("REDIS_URL should start with 'redis://'")
        
        # Report all errors at once
        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ConfigurationError(error_message)
        
        cls._validated = True
    
    @classmethod
    def is_ai_enabled(cls) -> bool:
        """Check if AI features are enabled (Gemini keys available)."""
        return len(cls.GEMINI_API_KEYS) > 0
    
    @classmethod
    def is_image_gen_enabled(cls) -> bool:
        """Check if image generation is enabled (OpenAI key available)."""
        return bool(cls.OPENAI_API_KEY)
    
    @classmethod
    def is_owner(cls, user_id: int) -> bool:
        """Check if a user is the bot owner."""
        return user_id == cls.OWNER_ID
    
    @classmethod
    def get_summary(cls) -> str:
        """Get a summary of the configuration (safe for logging)."""
        if not cls._validated:
            return "Configuration not validated yet"
        
        return (
            f"Configuration Summary:\n"
            f"  API_ID: {cls.API_ID}\n"
            f"  OWNER_ID: {cls.OWNER_ID}\n"
            f"  MONGO: {'configured' if cls.MONGO_URL else 'not set'}\n"
            f"  REDIS: {'configured' if cls.REDIS_URL else 'not set'}\n"
            f"  AI: {'enabled' if cls.is_ai_enabled() else 'disabled'} ({len(cls.GEMINI_API_KEYS)} keys)\n"
            f"  Image Gen: {'enabled' if cls.is_image_gen_enabled() else 'disabled'}\n"
            f"  Dashboard: {cls.DASHBOARD_HOST}:{cls.DASHBOARD_PORT}\n"
            f"  Log Level: {cls.LOG_LEVEL}\n"
            f"  Debug Mode: {cls.DEBUG}"
        )


# Validate configuration at import time
try:
    Config.validate()
except ConfigurationError as e:
    print(f"\n{'='*60}")
    print("CONFIGURATION ERROR")
    print('='*60)
    print(e)
    print('='*60)
    print("\nPlease check your .env file and ensure all required variables are set.")
    print("See .env.sample for an example configuration.\n")
    sys.exit(1)
