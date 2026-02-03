"""
ZyraX Database Package

Provides database access through a unified interface.

Usage (Backward Compatible):
    from zyrax.database.mongo import db
    await db.initialize()
    await db.add_warn(chat_id, user_id, reason)

Usage (New Repository Pattern):
    from zyrax.database import db
    await db.initialize()
    await db.users.register(user_id)
    await db.warnings.add(chat_id, user_id, reason)

Direct Repository Access:
    from zyrax.database.repositories import UserRepository
    from zyrax.database.connection import connection
"""

from zyrax.database.mongo import db
from zyrax.database.connection import connection
from zyrax.database.cache import Cache

__all__ = [
    "db",
    "connection",
    "Cache",
]
