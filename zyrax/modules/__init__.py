import glob
import importlib
import os
import sys
from os.path import basename, isfile, join

MOD_HELP = {}

def load_modules():
    mod_paths = glob.glob(join(os.path.dirname(__file__), "*.py"))
    all_modules = [ basename(f)[:-3] for f in mod_paths if isfile(f) and not f.endswith('__init__.py')]
    
    print(f"Found modules: {all_modules}")
    
    for module_name in all_modules:
        try:
            imported_module = importlib.import_module("zyrax.modules." + module_name)
            if hasattr(imported_module, "__mod_name__") and hasattr(imported_module, "__help__"):
                MOD_HELP[imported_module.__mod_name__] = imported_module.__help__
            print(f"Imported: {module_name}")
        except Exception as e:
            print(f"Failed to import {module_name}: {e}")

    return all_modules
