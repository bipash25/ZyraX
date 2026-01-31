#!/usr/bin/env python3
"""
Performance Anti-patterns Validation Tool
Checks for common performance issues and anti-patterns
"""

import sys
import ast
import re
from pathlib import Path


def print_success(text):
    print(f"\033[92m✓ {text}\033[0m")


def print_warning(text):
    print(f"\033[93m⚠ {text}\033[0m")


def print_info(text):
    print(f"\033[96mℹ {text}\033[0m")


def check_performance(project_root: Path) -> tuple:
    """
    Check for performance anti-patterns
    
    Returns:
        Tuple of (warnings list, stats dict)
    """
    warnings = []
    
    inefficient_loops = []
    unnecessary_copies = []
    string_concatenation = []
    missing_indexing = []
    synchronous_io = []
    
    # Find all Python files
    py_files = list(project_root.rglob("*.py"))
    py_files = [f for f in py_files if 'venv' not in str(f) and '__pycache__' not in str(f)]
    
    print_info(f"Scanning {len(py_files)} Python files for performance issues...")
    
    for py_file in py_files:
        relative_path = py_file.relative_to(project_root)
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Check for string concatenation in loops
            for i, line in enumerate(lines):
                if 'for ' in line or 'while ' in line:
                    # Check next few lines for string concatenation
                    loop_context = '\n'.join(lines[i:min(i+10, len(lines))])
                    if '+=' in loop_context and 'str' in loop_context:
                        string_concatenation.append((str(relative_path), i+1))
                        print_warning(
                            f"{relative_path}:{i+1}: String concatenation in loop "
                            "(use list.append + ''.join)"
                        )
            
            # Check for list() or dict() in loops
            for i, line in enumerate(lines):
                if ('list(' in line or 'dict(' in line) and ('for ' in line or 'while ' in line):
                    unnecessary_copies.append((str(relative_path), i+1))
                    print_warning(
                        f"{relative_path}:{i+1}: Creating new list/dict in comprehension "
                        "(unnecessary copy)"
                    )
            
            # Check for missing database indexes
            if 'handlers/' in str(relative_path):
                # Look for find operations without obvious indexing
                if 'find_one' in content or 'find(' in content:
                    if 'ensure_index' not in content and 'create_index' not in content:
                        # This is just informational
                        pass
            
            # Check for synchronous I/O in async functions
            if 'async def' in content:
                sync_io_patterns = [
                    ('open(', 'Use aiofiles'),
                    ('requests.', 'Use aiohttp'),
                    ('time.sleep(', 'Use asyncio.sleep()'),
                    ('urllib.request', 'Use aiohttp'),
                ]
                
                for pattern, suggestion in sync_io_patterns:
                    if pattern in content:
                        line_num = content.find(pattern)
                        line_num = content[:line_num].count('\n') + 1
                        synchronous_io.append((str(relative_path), line_num, pattern, suggestion))
                        print_warning(
                            f"{relative_path}:{line_num}: Synchronous I/O '{pattern}' in async function "
                            f"({suggestion})"
                        )
                        warnings.append(f"Sync I/O in async function in {relative_path}")
            
            # Check for inefficient data structures
            if 'handlers/' in str(relative_path):
                # Check for linear search when dict would be better
                if content.count('for ') > 3 and content.count('if ') > 3:
                    # This is a heuristic - many loops with conditionals might benefit from dicts
                    pass
        
        except Exception:
            pass
    
    stats = {
        'total_files': len(py_files),
        'string_concatenation': len(string_concatenation),
        'unnecessary_copies': len(unnecessary_copies),
        'synchronous_io': len(synchronous_io)
    }
    
    return warnings, stats


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("PERFORMANCE ANTI-PATTERNS VALIDATION".center(80))
    print("="*80 + "\n")
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run check
    warnings, stats = check_performance(project_root)
    
    # Print summary
    print("\n" + "="*80)
    print("RESULTS".center(80))
    print("="*80 + "\n")
    
    print_info(f"Total files scanned: {stats['total_files']}")
    print_info(f"String concatenation in loops: {stats['string_concatenation']}")
    print_info(f"Unnecessary copies: {stats['unnecessary_copies']}")
    print_info(f"Synchronous I/O in async: {stats['synchronous_io']}")
    
    if warnings:
        print_warning(f"\n{len(warnings)} performance warnings")
        print("\n⚡ Performance Tips:")
        print("  • Use list comprehensions instead of loops")
        print("  • Use ''.join(list) instead of += for strings")
        print("  • Use aiohttp instead of requests in async code")
        print("  • Use asyncio.sleep() instead of time.sleep()")
        print("  • Add database indexes for frequently queried fields")
        print("  • Use dict for lookups instead of linear search")
    else:
        print_success("\n✓ No obvious performance issues found!")
    
    print()
    
    # Exit with appropriate code (warnings don't cause failure)
    sys.exit(0)


if __name__ == "__main__":
    main()
