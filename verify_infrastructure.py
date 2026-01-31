import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from zyrax.config import Config
from dotenv import load_dotenv

load_dotenv()

async def verify_mongo():
    print("Testing MongoDB Connection...")
    try:
        url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        client = AsyncIOMotorClient(url)
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB Connection Successful!")
        return True
    except Exception as e:
        print(f"❌ MongoDB Connection Failed: {e}")
        return False

async def verify_redis():
    print("Testing Redis Connection...")
    try:
        url = os.getenv("REDIS_URL", "redis://localhost:6379")
        client = redis.from_url(url, decode_responses=True)
        # Test connection
        await client.ping()
        print("✅ Redis Connection Successful!")
        await client.close()
        return True
    except Exception as e:
        print(f"❌ Redis Connection Failed: {e}")
        return False

async def main():
    print("--- Infrastructure Verification ---")
    mongo_ok = await verify_mongo()
    redis_ok = await verify_redis()
    
    if mongo_ok and redis_ok:
        print("\n🎉 All Systems Operational!")
        exit(0)
    else:
        print("\n⚠️  Some systems failed.")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
