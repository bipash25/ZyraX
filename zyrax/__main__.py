import asyncio
import uvicorn
from pyrogram import Client, idle
from zyrax.config import Config
from zyrax.modules import load_modules
from zyrax.utils.logger import logger
from zyrax.dashboard import app as dashboard_app

async def start_dashboard():
    config = uvicorn.Config(dashboard_app, host="0.0.0.0", port=8080, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    # Load all modules dynamically before starting client
    load_modules()
    
    # Initialize Database (Indexes & Cache)
    from zyrax.database.mongo import db
    await db.initialize()
    
    app = Client(
        "ZyraX",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        plugins=dict(root="zyrax.modules")
    )
    
    # Inject bot instance into dashboard state
    dashboard_app.state.bot = app

    # Start Bot
    await app.start()
    logger.info("ZyraX started successfully!")
    
    # Start Dashboard (concurrently)
    # We use asyncio.create_task to run uvicorn in background
    dashboard_task = asyncio.create_task(start_dashboard())
    logger.info("Dashboard running on 0.0.0.0:8080")
    
    await idle()
    await app.stop()
    # Cancel dashboard task on shutdown
    dashboard_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
