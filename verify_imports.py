import sys
import os

# Add project root to path
sys.path.append(os.getcwd())
os.environ["MONGO_URL"] = "mongodb://localhost:27017"

from unittest.mock import MagicMock
sys.modules["motor.motor_asyncio"] = MagicMock()
sys.modules["redis.asyncio"] = MagicMock()

try:
    print("Verifying imports...")
    import zyrax.config
    print("Config imported.")
    import zyrax.database.mongo
    print("Database imported.")
    import zyrax.utils.decorators
    print("Decorators imported.")
    import zyrax.utils.validators
    import zyrax.utils.ratelimit
    print("Security utils imported.")
    
    # Import modules
    import zyrax.modules.admin
    import zyrax.modules.bans
    import zyrax.modules.welcome
    import zyrax.modules.warnings
    import zyrax.modules.userinfo
    import zyrax.modules.captcha
    import zyrax.modules.blacklist
    import zyrax.modules.reports
    import zyrax.modules.utilities
    import zyrax.modules.fun
    import zyrax.modules.media
    import zyrax.modules.economy
    import zyrax.modules.games
    import zyrax.modules.levels
    import zyrax.modules.notes
    import zyrax.modules.filters
    import zyrax.modules.karma
    import zyrax.modules.music
    import zyrax.modules.ai
    import zyrax.modules.automation
    import zyrax.modules.notes
    import zyrax.modules.filters
    import zyrax.modules.antiflood
    import zyrax.modules.federation
    import zyrax.modules.games
    import zyrax.modules.fun
    import zyrax.modules.ai
    import zyrax.modules.tournaments
    import zyrax.modules.bridge
    print("All modules imported successfully.")
    
except Exception as e:
    print(f"Verification Failed: {e}")
    sys.exit(1)

print("Project structure verify: PASSED")
