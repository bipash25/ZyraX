import asyncio
import uvicorn
from pyrogram import Client, idle
from pytgcalls import PyTgCalls
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
    
    # Initialize PyTgCalls
    call_client = PyTgCalls(app)
    app.call_client = call_client # Attach to app for modules to access
    
    # Inject bot instance into dashboard state
    dashboard_app.state.bot = app

    # Start Bot & Calls
    await app.start()
    await call_client.start()
    logger.info("ZyraX and Music Player started successfully!")
    
    # Start Dashboard (concurrently)
    dashboard_task = asyncio.create_task(start_dashboard())
    logger.info("Dashboard running on 0.0.0.0:8080")
    
    # Start Backup Loop
    from zyrax.utils.backup import backup_database
    backup_task = asyncio.create_task(backup_database())
    
    # Start Scheduler Loop
    from zyrax.utils.scheduler import scheduler_loop
    scheduler_task = asyncio.create_task(scheduler_loop(app))
    
    await idle()
    await app.stop()
    # Cancel tasks
    dashboard_task.cancel()
    backup_task.cancel()
    scheduler_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
