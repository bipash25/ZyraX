import asyncio
import time
import aiohttp
import feedparser
from zyrax.database.mongo import db
from zyrax.utils.logger import logger
from zyrax.constants import Timeouts
from pyrogram import Client
from pyrogram.enums import ParseMode

async def check_rss_feeds(client: Client):
    # Iterate all settings docs that have rss_feeds
    settings_col = await db.get_collection("settings")
    cursor = settings_col.find({"rss_feeds": {"$exists": True, "$not": {"$size": 0}}})
    
    async for doc in cursor:
        chat_id = doc["chat_id"]
        feeds = doc["rss_feeds"]
        
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
                
                last_seen = rss_state.get(url)
                
                if last_seen != latest_link:
                    if last_seen is not None:
                        await client.send_message(
                            chat_id,
                            f"**New RSS Entry**\n\n**{latest_title}**\n{latest_link}"
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


async def check_reminders(client: Client):
    """Check for due reminders and send them"""
    current_time = time.time()
    reminders = await db.get_due_reminders(current_time)
    
    for reminder in reminders:
        try:
            await client.send_message(
                reminder["chat_id"],
                f"**Reminder for** <a href='tg://user?id={reminder['user_id']}'>User</a>\n\n"
                f"{reminder['text']}",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send reminder: {e}")
        
        await db.delete_reminder(reminder["_id"])


async def check_temp_bans(client: Client):
    """Check for expired temporary bans/mutes"""
    current_time = time.time()
    temp_actions = await db.get_collection("temp_actions")
    
    cursor = temp_actions.find({"expires_at": {"$lte": current_time}})
    
    async for action in cursor:
        try:
            if action["type"] == "ban":
                await client.unban_chat_member(action["chat_id"], action["user_id"])
                await client.send_message(
                    action["chat_id"],
                    f"User {action['user_id']} has been automatically unbanned (temp ban expired)."
                )
            elif action["type"] == "mute":
                from pyrogram.types import ChatPermissions
                await client.restrict_chat_member(
                    action["chat_id"],
                    action["user_id"],
                    ChatPermissions(
                        can_send_messages=True,
                        can_send_media_messages=True,
                        can_send_polls=True,
                        can_add_web_page_previews=True
                    )
                )
                await client.send_message(
                    action["chat_id"],
                    f"User {action['user_id']} has been automatically unmuted (temp mute expired)."
                )
        except Exception as e:
            logger.error(f"Failed to lift temp action: {e}")
        
        await temp_actions.delete_one({"_id": action["_id"]})


async def check_raid_mode(client: Client):
    """Check for expired raid modes"""
    current_time = time.time()
    settings = await db.get_collection("settings")
    
    cursor = settings.find({
        "raid.enabled": True,
        "raid.expires": {"$lte": current_time}
    })
    
    async for doc in cursor:
        await settings.update_one(
            {"_id": doc["_id"]},
            {"$set": {"raid.enabled": False}}
        )
        try:
            await client.send_message(
                doc["chat_id"],
                "**Anti-Raid Mode** has been automatically disabled (expired)."
            )
        except Exception:
            pass


async def cleanup_stale_games():
    """Clean up old/abandoned games from memory."""
    try:
        from zyrax.modules.games.base import cleanup_all_games
        results = cleanup_all_games(max_age=Timeouts.GAME_MAX_AGE)
        
        total_cleaned = sum(results.values())
        if total_cleaned > 0:
            logger.info(f"Cleaned up {total_cleaned} stale games: {results}")
    except ImportError:
        # Games module not loaded
        pass
    except Exception as e:
        logger.error(f"Game cleanup error: {e}")


async def scheduler_loop(client: Client):
    logger.info("Scheduler started.")
    game_cleanup_counter = 0
    
    while True:
        try:
            # Run all scheduled tasks
            await asyncio.gather(
                check_rss_feeds(client),
                check_reminders(client),
                check_temp_bans(client),
                check_raid_mode(client),
                return_exceptions=True
            )
            
            # Run game cleanup every 5 minutes (10 iterations * 30 seconds)
            game_cleanup_counter += 1
            if game_cleanup_counter >= 10:
                await cleanup_stale_games()
                game_cleanup_counter = 0
            
            # Sleep 30 seconds between checks
            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f"Scheduler Loop Error: {e}")
            await asyncio.sleep(60)
