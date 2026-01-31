#!/usr/bin/env python3
"""
File Structure Validation Tool
Checks project file structure for required files and directories
"""

import sys
from pathlib import Path


def print_success(text):
    print(f"\033[92m✓ {text}\033[0m")


def print_warning(text):
    print(f"\033[93m⚠ {text}\033[0m")


def print_error(text):
    print(f"\033[91m✗ {text}\033[0m")


def check_file_structure(project_root: Path) -> tuple:
    """
    Check project file structure
    
    Returns:
        Tuple of (errors list, warnings list)
    """
    errors = []
    warnings = []
    
    required_files = [
        "bot.py",
        "config.py",
        "requirements.txt",
        "README.md"
    ]
    
    optional_files = [
        ".env.example",
        ".gitignore",
        "LICENSE",
        "pyproject.toml"
    ]
    
    required_dirs = [
        "handlers",
        "core",
        "middleware",
        "utils"
    ]
    
    optional_dirs = [
        "tools",
        "docs",
        "tests",
        "data"
    ]
    
    print("Checking required files...")
    for file_name in required_files:
        file_path = project_root / file_name
        if file_path.exists():
            print_success(f"Required file exists: {file_name}")
        else:
            print_error(f"Required file missing: {file_name}")
            errors.append(f"Missing {file_name}")
    
    print("\nChecking optional files...")
    for file_name in optional_files:
        file_path = project_root / file_name
        if file_path.exists():
            print_success(f"Optional file exists: {file_name}")
        else:
            print_warning(f"Recommended file missing: {file_name}")
            warnings.append(f"Missing {file_name}")
    
    print("\nChecking required directories...")
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists() and dir_path.is_dir():
            py_files = list(dir_path.rglob("*.py"))
            print_success(f"Directory '{dir_name}' exists ({len(py_files)} .py files)")
        else:
            print_error(f"Required directory missing: {dir_name}")
            errors.append(f"Missing directory {dir_name}")
    
    print("\nChecking optional directories...")
    for dir_name in optional_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists() and dir_path.is_dir():
            py_files = list(dir_path.rglob("*.py"))
            print_success(f"Directory '{dir_name}' exists ({len(py_files)} .py files)")
    
    return errors, warnings


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("FILE STRUCTURE VALIDATION".center(80))
    print("="*80 + "\n")
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print(f"Project root: {project_root}\n")
    
    # Run check
    errors, warnings = check_file_structure(project_root)
    
    # Print summary
    print("\n" + "="*80)
    print("RESULTS".center(80))
    print("="*80 + "\n")
    
    if errors:
        print_error(f"{len(errors)} ERRORS found:")
        for error in errors:
            print(f"  - {error}")
    else:
        print_success("✓ All required files and directories exist!")
    
    if warnings:
        print_warning(f"\n{len(warnings)} WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
    
    print()
    
    # Exit with appropriate code
    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
