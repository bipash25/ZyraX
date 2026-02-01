import asyncio
import os
import shutil
from datetime import datetime
from zyrax.config import Config
from zyrax.utils.logger import logger

async def backup_database():
    while True:
        try:
            # Wait 24 hours
            await asyncio.sleep(86400)
            
            logger.info("Starting scheduled backup...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"backups/backup_{timestamp}"
            
            # Create backup using mongodump (requires tools installed)
            # Or simplified: Dump critical collections to JSON
            from zyrax.database.mongo import db
            import json
            
            os.makedirs(backup_dir, exist_ok=True)
            
            collections = ["users", "chats", "settings", "warnings", "notes", "filters", "audit_logs"]
            
            def json_serial(obj):
                if hasattr(obj, 'isoformat'):
                    return obj.isoformat()
                return str(obj)

            for col_name in collections:
                col = await db.get_collection(col_name)
                cursor = col.find({})
                data = [doc async for doc in cursor]
                
                with open(f"{backup_dir}/{col_name}.json", "w") as f:
                    json.dump(data, f, default=json_serial, indent=2)
            
            # Zip it (AES encryption logic would go here if needed)
            shutil.make_archive(backup_dir, 'zip', backup_dir)
            shutil.rmtree(backup_dir) # Remove raw folder
            
            logger.info(f"Backup created: {backup_dir}.zip")
            
            # Send to owner if bot instance available
            # (Requires app reference, simplified here)
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            await asyncio.sleep(3600) # Retry in 1 hour
