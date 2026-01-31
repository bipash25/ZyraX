#!/usr/bin/env python3
"""
Datetime Usage Validation Tool
Checks datetime usage patterns for timezone awareness
"""

import sys
import re
from pathlib import Path


def print_success(text):
    print(f"\033[92m✓ {text}\033[0m")


def print_error(text):
    print(f"\033[91m✗ {text}\033[0m")


def print_info(text):
    print(f"\033[96mℹ {text}\033[0m")


def check_datetime_usage(project_root: Path) -> tuple:
    """
    Check datetime usage patterns
    
    Returns:
        Tuple of (errors list, stats dict)
    """
    errors = []
    
    now_utc_files = []
    utcnow_files = []
    naive_now_files = []
    
    # Find all Python files
    py_files = list(project_root.rglob("*.py"))
    py_files = [f for f in py_files if 'venv' not in str(f) and '__pycache__' not in str(f)]
    
    print_info(f"Scanning {len(py_files)} Python files for datetime usage...")
    
    for py_file in py_files:
        relative_path = py_file.relative_to(project_root)
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Track now_utc() usage (good pattern)
            if 'now_utc()' in content:
                now_utc_files.append(str(relative_path))
            
            # Check for deprecated datetime.utcnow()
            if 'datetime.utcnow()' in content:
                utcnow_files.append(str(relative_path))
                print_error(f"{relative_path}: Uses deprecated datetime.utcnow()")
                errors.append(f"Deprecated datetime.utcnow() in {relative_path}")
            
            # Check for naive datetime.now()
            if re.search(r'datetime\.now\(\s*\)', content):
                # Check if timezone is specified elsewhere
                if 'timezone.utc' not in content and 'now_utc()' not in content:
                    naive_now_files.append(str(relative_path))
                    print_error(f"{relative_path}: Uses datetime.now() without timezone")
                    errors.append(f"Naive datetime.now() in {relative_path}")
        
        except Exception:
            pass
    
    stats = {
        'total_files': len(py_files),
        'now_utc_files': len(now_utc_files),
        'utcnow_files': len(utcnow_files),
        'naive_now_files': len(naive_now_files)
    }
    
    return errors, stats


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("DATETIME USAGE VALIDATION".center(80))
    print("="*80 + "\n")
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run check
    errors, stats = check_datetime_usage(project_root)
    
    # Print summary
    print("\n" + "="*80)
    print("RESULTS".center(80))
    print("="*80 + "\n")
    
    print_info(f"Total files scanned: {stats['total_files']}")
    print_info(f"Files using now_utc() helper: {stats['now_utc_files']}")
    print_info(f"Files with datetime.utcnow(): {stats['utcnow_files']}")
    print_info(f"Files with naive datetime.now(): {stats['naive_now_files']}")
    
    if errors:
        print_error(f"\n{len(errors)} ERRORS found:")
        for error in errors[:15]:
            print(f"  - {error}")
        if len(errors) > 15:
            print(f"  ... and {len(errors) - 15} more")
        print("\n💡 Tip: Use now_utc() from utils.time_parser for timezone-aware datetimes")
    else:
        print_success("\n✓ All datetime usage is timezone-aware!")
    
    print()
    
    # Exit with appropriate code
    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
