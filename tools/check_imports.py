#!/usr/bin/env python3
"""
Import Consistency Validation Tool
Checks import statements for consistency and deprecated patterns
"""

import sys
import re
from pathlib import Path


def print_success(text):
    print(f"\033[92m✓ {text}\033[0m")


def print_warning(text):
    print(f"\033[93m⚠ {text}\033[0m")


def print_info(text):
    print(f"\033[96mℹ {text}\033[0m")


def check_imports(project_root: Path) -> tuple:
    """
    Check import consistency
    
    Returns:
        Tuple of (warnings list, stats dict)
    """
    warnings = []
    
    datetime_issues = []
    deprecated_imports = []
    missing_typing_imports = []
    
    # Find all Python files
    py_files = list(project_root.rglob("*.py"))
    py_files = [f for f in py_files if 'venv' not in str(f) and '__pycache__' not in str(f)]
    
    print_info(f"Scanning {len(py_files)} Python files for import issues...")
    
    for py_file in py_files:
        relative_path = py_file.relative_to(project_root)
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for deprecated datetime usage
            if 'datetime.utcnow()' in content:
                datetime_issues.append(str(relative_path))
                print_warning(f"{relative_path}: Uses deprecated datetime.utcnow()")
                warnings.append(f"Deprecated datetime.utcnow() in {relative_path}")
            
            # Check for datetime.now() without timezone
            if re.search(r'datetime\.now\(\s*\)', content):
                if 'timezone.utc' not in content and 'now_utc()' not in content:
                    datetime_issues.append(str(relative_path))
                    print_warning(f"{relative_path}: Uses datetime.now() without timezone")
                    warnings.append(f"Naive datetime.now() in {relative_path}")
            
            # Check for deprecated imports
            deprecated_patterns = {
                'from datetime import datetime': 'Consider importing timezone as well',
                'import telegram.ext': 'Use specific imports for better clarity',
            }
            
            for pattern, suggestion in deprecated_patterns.items():
                if pattern in content:
                    deprecated_imports.append((str(relative_path), pattern, suggestion))
            
            # Check for missing typing imports in files with type hints
            if ': ' in content or '->' in content:  # Basic type hint detection
                if 'from typing import' not in content and 'import typing' not in content:
                    # Check if actually has type hints
                    type_hint_pattern = r'def \w+\([^)]*:\s*\w+|-> \w+'
                    if re.search(type_hint_pattern, content):
                        missing_typing_imports.append(str(relative_path))
        
        except Exception:
            pass
    
    stats = {
        'total_files': len(py_files),
        'datetime_issues': len(datetime_issues),
        'deprecated_imports': len(deprecated_imports),
        'missing_typing': len(missing_typing_imports)
    }
    
    return warnings, stats


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("IMPORT CONSISTENCY VALIDATION".center(80))
    print("="*80 + "\n")
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run check
    warnings, stats = check_imports(project_root)
    
    # Print summary
    print("\n" + "="*80)
    print("RESULTS".center(80))
    print("="*80 + "\n")
    
    print_info(f"Total files scanned: {stats['total_files']}")
    print_info(f"Files with datetime issues: {stats['datetime_issues']}")
    print_info(f"Files with deprecated imports: {stats['deprecated_imports']}")
    print_info(f"Files missing typing imports: {stats['missing_typing']}")
    
    if warnings:
        print_warning(f"\n{len(warnings)} WARNINGS found")
        if stats['datetime_issues'] == 0:
            print_success("\n✓ All datetime usage is timezone-aware!")
        else:
            print_warning(f"\n⚠ {stats['datetime_issues']} files have datetime issues")
    else:
        print_success("\n✓ All imports are consistent!")
    
    print()
    
    # Exit with appropriate code (warnings don't cause failure)
    sys.exit(0)


if __name__ == "__main__":
    main()
