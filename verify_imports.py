import sys
import os

# Add project root to path
sys.path.append(os.getcwd())
os.environ["MONGO_URL"] = "mongodb://localhost:27017"

from unittest.mock import MagicMock
sys.modules["motor.motor_asyncio"] = MagicMock()

try:
    print("Verifying imports...")
    import zyrax.config
    print("Config imported.")
    import zyrax.database.mongo
    print("Database imported.")
    import zyrax.utils.decorators
    print("Decorators imported.")
    
    # Import modules
    import zyrax.modules.admin
    import zyrax.modules.bans
    import zyrax.modules.greetings
    import zyrax.modules.warnings
    import zyrax.modules.users
    import zyrax.modules.utilities
    import zyrax.modules.notes
    import zyrax.modules.filters
    import zyrax.modules.antiflood
    import zyrax.modules.federation
    import zyrax.modules.games
    import zyrax.modules.fun
    import zyrax.modules.ai
    print("All modules imported successfully.")
    
except Exception as e:
    print(f"Verification Failed: {e}")
    sys.exit(1)

print("Project structure verify: PASSED")
