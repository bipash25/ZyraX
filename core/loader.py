"""
Dynamic command loader
Automatically discovers and registers command handlers
"""
import logging
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Any, Callable
from telegram.ext import Application, CommandHandler

logger = logging.getLogger(__name__)


class CommandLoader:
    """
    Dynamically loads and registers command handlers
    Scans handlers directory for modules with COMMAND_INFO metadata
    """
    
    def __init__(self, app: Application, db, cache):
        """
        Initialize command loader
        
        Args:
            app: PTB Application instance
            db: Database instance
            cache: Cache manager instance
        """
        self.app = app
        self.db = db
        self.cache = cache
        self.commands: Dict[str, Dict[str, Any]] = {}
        self.help_registry: Dict[str, List[Dict]] = {}
        self.loaded_count = 0
    
    async def load_all_handlers(self) -> None:
        """Load all handlers from the handlers directory"""
        handlers_path = Path("handlers")
        
        if not handlers_path.exists():
            logger.error("Handlers directory not found!")
            return
        
        logger.info("Scanning for command handlers...")
        
        # Recursively find all Python files
        py_files = list(handlers_path.rglob("*.py"))
        
        for py_file in py_files:
            # Skip __init__.py and private files
            if py_file.name.startswith("_"):
                continue
            
            # Convert path to module name
            module_path = str(py_file.with_suffix("")).replace("\\", ".").replace("/", ".")
            
            try:
                # Import module
                module = importlib.import_module(module_path)
                
                # Look for COMMAND_INFO and handle function
                if hasattr(module, "COMMAND_INFO") and hasattr(module, "handle"):
                    command_info = getattr(module, "COMMAND_INFO")
                    handle_func = getattr(module, "handle")
                    
                    # Validate and register
                    if self._validate_command_info(command_info):
                        self._register_command(command_info, handle_func, module_path)
                        self.loaded_count += 1
                
                # Check for callback handlers (like help buttons)
                if hasattr(module, "get_callback_handler"):
                    callback_handler_func = getattr(module, "get_callback_handler")
                    callback_handler = callback_handler_func()
                    if callback_handler:
                        self.app.add_handler(callback_handler)
                        logger.debug(f"Registered callback handler from {module_path}")
                
            except Exception as e:
                logger.error(f"Error loading {module_path}: {e}")
        
        # Store command registry in bot_data for access by /help command
        self.app.bot_data['command_registry'] = self.commands
        
        logger.info(f"✓ Loaded {self.loaded_count} commands")
        self._print_summary()
    
    def _validate_command_info(self, info: Dict) -> bool:
        """
        Validate command info structure
        
        Args:
            info: Command info dictionary
            
        Returns:
            True if valid
        """
        required = ["name", "description", "category"]
        
        for field in required:
            if field not in info:
                logger.warning(f"Command missing required field: {field}")
                return False
        
        return True
    
    def _register_command(
        self,
        info: Dict,
        handler: Callable,
        module_path: str
    ) -> None:
        """
        Register a command with PTB
        
        Args:
            info: Command metadata
            handler: Command handler function
            module_path: Module path for debugging
        """
        name = info["name"]
        aliases = info.get("aliases", [])
        category = info.get("category", "misc").upper()
        
        # Store command info (flattened for easy access)
        self.commands[name] = info.copy()
        
        # Add to help registry
        if category not in self.help_registry:
            self.help_registry[category] = []
        
        self.help_registry[category].append({
            "name": name,
            "description": info["description"],
            "usage": info.get("usage", f"/{name}"),
            "aliases": aliases
        })
        
        # Register with PTB
        triggers = [name] + aliases
        
        for trigger in triggers:
            self.app.add_handler(CommandHandler(trigger, handler))
        
        logger.debug(
            f"Registered: /{name} "
            f"({', '.join(f'/{a}' for a in aliases) if aliases else 'no aliases'})"
        )
    
    def _print_summary(self) -> None:
        """Print loading summary"""
        logger.info("=" * 60)
        logger.info("Command Loading Summary:")
        logger.info("-" * 60)
        
        for category in sorted(self.help_registry.keys()):
            count = len(self.help_registry[category])
            commands = ", ".join(cmd["name"] for cmd in self.help_registry[category])
            logger.info(f"  {category:12s}: {count:2d} commands - {commands}")
        
        logger.info("=" * 60)
    
    def get_help_registry(self) -> Dict[str, List[Dict]]:
        """Get the help registry (for /help command)"""
        return self.help_registry.copy()
    
    def get_command_info(self, command_name: str) -> Dict[str, Any]:
        """
        Get info about a specific command
        
        Args:
            command_name: Name of the command
            
        Returns:
            Command info dictionary or empty dict
        """
        return self.commands.get(command_name, {})