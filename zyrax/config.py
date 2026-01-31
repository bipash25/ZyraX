import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    MONGO_URL = os.getenv("MONGO_URL", "")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
