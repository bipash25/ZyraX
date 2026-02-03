"""
Module Loader

Dynamically loads all module files and registers their handlers.
"""

import glob
import importlib
import os
import sys
import time
import traceback
from os.path import basename, isfile, join
from typing import Dict, List, Optional, Set, Any

from zyrax.utils.logger import logger


# Module help text registry
MOD_HELP: Dict[str, str] = {}

# Loaded module names
LOADED_MODULES: Set[str] = set()

# Failed modules with error info
FAILED_MODULES: Dict[str, str] = {}

# Module load times for performance tracking
LOAD_TIMES: Dict[str, float] = {}


def get_module_paths() -> List[str]:
    """Get all Python module file paths."""
    mod_dir = os.path.dirname(__file__)
    mod_paths = glob.glob(join(mod_dir, "*.py"))
    return [
        f for f in mod_paths 
        if isfile(f) and not f.endswith('__init__.py')
    ]


def get_package_names() -> List[str]:
    """Get all package directory names (directories with __init__.py)."""
    mod_dir = os.path.dirname(__file__)
    packages = []
    for item in os.listdir(mod_dir):
        item_path = join(mod_dir, item)
        if os.path.isdir(item_path) and not item.startswith('_'):
            init_file = join(item_path, "__init__.py")
            if os.path.isfile(init_file):
                packages.append(item)
    return packages


def get_module_names() -> List[str]:
    """Get all module names (files without .py extension + packages)."""
    file_modules = [basename(f)[:-3] for f in get_module_paths()]
    package_modules = get_package_names()
    return file_modules + package_modules


def load_module(module_name: str) -> bool:
    """
    Load a single module by name.
    
    Args:
        module_name: Name of the module (without .py)
        
    Returns:
        True if loaded successfully
    """
    full_name = f"zyrax.modules.{module_name}"
    start_time = time.time()
    
    try:
        # Import the module
        imported_module = importlib.import_module(full_name)
        
        # Register help text if available
        if hasattr(imported_module, "__mod_name__") and hasattr(imported_module, "__help__"):
            MOD_HELP[imported_module.__mod_name__] = imported_module.__help__
        
        # Track load time
        load_time = time.time() - start_time
        LOAD_TIMES[module_name] = load_time
        
        LOADED_MODULES.add(module_name)
        logger.info(f"Loaded module: {module_name} ({load_time:.3f}s)")
        
        return True
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        FAILED_MODULES[module_name] = error_msg
        
        # Log full traceback for debugging
        logger.error(f"Failed to load module {module_name}: {error_msg}")
        logger.debug(f"Traceback:\n{traceback.format_exc()}")
        
        return False


def reload_module(module_name: str) -> bool:
    """
    Reload a module (useful for hot-reloading).
    
    Args:
        module_name: Name of the module to reload
        
    Returns:
        True if reloaded successfully
    """
    full_name = f"zyrax.modules.{module_name}"
    
    if full_name not in sys.modules:
        logger.warning(f"Module {module_name} not loaded, loading instead")
        return load_module(module_name)
    
    try:
        # Remove old help entry
        for key in list(MOD_HELP.keys()):
            mod = sys.modules.get(full_name)
            if mod and hasattr(mod, "__mod_name__") and mod.__mod_name__ == key:
                del MOD_HELP[key]
                break
        
        # Reload the module
        importlib.reload(sys.modules[full_name])
        
        # Re-register help
        mod = sys.modules[full_name]
        if hasattr(mod, "__mod_name__") and hasattr(mod, "__help__"):
            MOD_HELP[mod.__mod_name__] = mod.__help__
        
        logger.info(f"Reloaded module: {module_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to reload module {module_name}: {e}")
        return False


def load_modules(exclude: Optional[List[str]] = None) -> List[str]:
    """
    Load all available modules.
    
    Args:
        exclude: List of module names to skip
        
    Returns:
        List of successfully loaded module names
    """
    exclude = exclude or []
    all_modules = get_module_names()
    
    logger.info(f"Found {len(all_modules)} modules to load")
    
    loaded = []
    failed = []
    
    start_time = time.time()
    
    for module_name in sorted(all_modules):
        if module_name in exclude:
            logger.debug(f"Skipping excluded module: {module_name}")
            continue
        
        if load_module(module_name):
            loaded.append(module_name)
        else:
            failed.append(module_name)
    
    total_time = time.time() - start_time
    
    # Summary logging
    logger.info(f"Module loading complete in {total_time:.2f}s")
    logger.info(f"  Loaded: {len(loaded)} modules")
    
    if failed:
        logger.warning(f"  Failed: {len(failed)} modules - {', '.join(failed)}")
    
    # Log slowest modules
    if LOAD_TIMES:
        slowest = sorted(LOAD_TIMES.items(), key=lambda x: x[1], reverse=True)[:5]
        if slowest and slowest[0][1] > 0.5:  # Only log if slowest > 0.5s
            logger.debug("Slowest modules:")
            for name, time_taken in slowest:
                if time_taken > 0.1:
                    logger.debug(f"  {name}: {time_taken:.3f}s")
    
    return loaded


def get_loaded_modules() -> List[str]:
    """Get list of successfully loaded module names."""
    return list(LOADED_MODULES)


def get_failed_modules() -> Dict[str, str]:
    """Get dict of failed modules with their error messages."""
    return dict(FAILED_MODULES)


def get_module_help(module_name: str) -> Optional[str]:
    """Get help text for a module by its display name."""
    return MOD_HELP.get(module_name)


def get_all_help() -> Dict[str, str]:
    """Get all module help texts."""
    return dict(MOD_HELP)


def get_load_stats() -> Dict[str, Any]:
    """
    Get module loading statistics.
    
    Returns:
        Dict with loading statistics
    """
    return {
        "total_modules": len(get_module_names()),
        "loaded": len(LOADED_MODULES),
        "failed": len(FAILED_MODULES),
        "total_load_time": sum(LOAD_TIMES.values()),
        "average_load_time": (
            sum(LOAD_TIMES.values()) / len(LOAD_TIMES) 
            if LOAD_TIMES else 0
        ),
        "slowest_module": (
            max(LOAD_TIMES.items(), key=lambda x: x[1])[0] 
            if LOAD_TIMES else None
        ),
        "failed_modules": list(FAILED_MODULES.keys()),
    }
