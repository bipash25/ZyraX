"""
Create and send database backup
"""
import logging
import json
from pathlib import Path
from datetime import datetime
from bson import ObjectId
from telegram import Update
from telegram.ext import ContextTypes
from core.decorators import owner_only, log_command
from utils.time_parser import now_utc

logger = logging.getLogger(__name__)

COMMAND_INFO = {
    "name": "dbbackup",
    "aliases": ["fullbackup", "dbexport"],
    "description": "Create and send database backup",
    "usage": "/dbbackup",
    "category": "owner",
    "scope": ["private"]
}


@log_command
@owner_only
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Create database backup and send as file
    """
    db = context.application.bot_data.get('database')
    if not db:
        await update.message.reply_text("❌ Database not available")
        return
    
    msg = await update.message.reply_text("⏳ Creating database backup...")
    
    try:
        # Create backup directory
        backup_dir = Path("data/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = now_utc().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"backup_{timestamp}.json"
        
        # Collect data from all collections
        backup_data = {
            "timestamp": now_utc().isoformat(),
            "version": "2.0.0",
            "collections": {}
        }
        
        collections = [
            "users", "chats", "federations", "filters", "notes",
            "warnings", "blocklists", "scheduled_actions", "action_logs"
        ]
        
        for collection_name in collections:
            await msg.edit_text(f"⏳ Backing up {collection_name}...")
            
            collection = db.get_collection(collection_name)
            cursor = collection.find({})
            docs = await cursor.to_list(length=None)
            
            # Convert ObjectId and datetime to strings recursively
            def make_serializable(obj):
                """Recursively convert datetime and ObjectId objects to strings"""
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, ObjectId):
                    return str(obj)
                elif isinstance(obj, dict):
                    return {k: make_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [make_serializable(item) for item in obj]
                else:
                    return obj
            
            serializable_docs = []
            for doc in docs:
                serializable_doc = make_serializable(doc)
                serializable_docs.append(serializable_doc)
            
            backup_data["collections"][collection_name] = serializable_docs
        
        # Write to file
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        file_size = backup_file.stat().st_size / (1024 * 1024)  # MB
        
        # Send file
        with open(backup_file, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=f"zyrax_backup_{timestamp}.json",
                caption=f"💾 <b>Database Backup</b>\n\n"
                        f"Size: {file_size:.2f} MB\n"
                        f"Collections: {len(collections)}\n"
                        f"Created: {now_utc().strftime('%Y-%m-%d %H:%M:%S')} UTC",
                parse_mode='HTML'
            )
        
        await msg.delete()
        
        logger.info(f"Database backup created: {backup_file}")
        
    except Exception as e:
        logger.error(f"Error creating database backup: {e}")
        await msg.edit_text(f"❌ Error: {str(e)}")

