"""
Configuration management using Pydantic
Loads settings from environment variables
"""
from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Bot Configuration
    BOT_TOKEN: str
    BOT_USERNAME: Optional[str] = None
    OWNER_ID: int
    
    # MTProto (Pyrogram)
    TELEGRAM_API_ID: Optional[int] = None
    TELEGRAM_API_HASH: Optional[str] = None
    
    # Database
    MONGO_URI: str = "mongodb://localhost:27017/zyrax"
    MONGO_DB_NAME: str = "zyrax"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Path = Path("data/logs/bot.log")
    
    # Features
    ENABLE_MTPROTO: bool = True
    ENABLE_REDIS: bool = False
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_MESSAGES: int = 20
    RATE_LIMIT_PERIOD: int = 60
    
    @property
    def mtproto_enabled(self) -> bool:
        """Check if MTProto is properly configured"""
        return (
            self.ENABLE_MTPROTO 
            and self.TELEGRAM_API_ID is not None 
            and self.TELEGRAM_API_HASH is not None
        )
    
    @property
    def redis_enabled(self) -> bool:
        """Check if Redis is enabled"""
        return self.ENABLE_REDIS


# Global settings instance
settings = Settings()