import asyncio
import time
import aiohttp
import feedparser
from zyrax.database.mongo import db
from zyrax.utils.logger import logger
from pyrogram import Client

async def check_rss_feeds(client: Client):
    # Iterate all settings docs that have rss_feeds
    settings_col = await db.get_collection("settings")
    cursor = settings_col.find({"rss_feeds": {"$exists": True, "$not": {"$size": 0}}})
    
    async for doc in cursor:
        chat_id = doc["chat_id"]
        feeds = doc["rss_feeds"]
        
        # We need to track last_entry_link per feed per chat to avoid dupes
        # For simplicity, we assume we fetch only new items since last run?
        # A proper RSS reader stores state.
        # Let's store "rss_state": {url: last_link} in the doc.
        rss_state = doc.get("rss_state", {})
        
        updated_state = False
        
        for url in feeds:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10) as resp:
                        if resp.status != 200:
                            continue
                        text = await resp.text()
                        
                feed = feedparser.parse(text)
                if not feed.entries:
                    continue
                    
                latest_entry = feed.entries[0]
                latest_link = latest_entry.link
                latest_title = latest_entry.title
                
                # Check state
                last_seen = rss_state.get(url)
                
                if last_seen != latest_link:
                    # New Item!
                    # Only send if we had a previous state (to avoid spamming on add)
                    # OR maybe send the latest one immediately on add? 
                    # Convention: If last_seen is None, just set it without sending (initial sync)
                    if last_seen is not None:
                        await client.send_message(
                            chat_id,
                            f"📰 **New RSS Entry**\n\n**{latest_title}**\n{latest_link}"
                        )
                    
                    rss_state[url] = latest_link
                    updated_state = True
            except Exception as e:
                logger.error(f"RSS Error for {url}: {e}")
        
        if updated_state:
            await settings_col.update_one(
                {"chat_id": chat_id},
                {"$set": {"rss_state": rss_state}}
            )

async def scheduler_loop(client: Client):
    logger.info("Scheduler started.")
    while True:
        try:
            await check_rss_feeds(client)
            # Sleep 5 minutes
            await asyncio.sleep(300)
        except Exception as e:
            logger.error(f"Scheduler Loop Error: {e}")
            await asyncio.sleep(60)
