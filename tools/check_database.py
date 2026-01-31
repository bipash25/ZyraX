#!/usr/bin/env python3
"""
Database Operations Validation Tool
Checks database operation patterns and error handling
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


def check_database_operations(project_root: Path) -> tuple:
    """
    Check database operation patterns
    
    Returns:
        Tuple of (warnings list, stats dict)
    """
    warnings = []
    
    db_files = []
    missing_error_handling = []
    potential_n_plus_1 = []
    
    # Find all Python files
    py_files = list(project_root.rglob("*.py"))
    py_files = [f for f in py_files if 'venv' not in str(f) and '__pycache__' not in str(f)]
    
    print_info(f"Scanning {len(py_files)} Python files for database operations...")
    
    for py_file in py_files:
        relative_path = py_file.relative_to(project_root)
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for database operations
            has_db_ops = any(op in content for op in [
                'db.', 'database.', 'find_one', 'insert_one', 'update_one', 
                'delete_one', 'find()', 'aggregate'
            ])
            
            if not has_db_ops:
                continue
            
            db_files.append(str(relative_path))
            
            # Check for error handling around DB operations
            has_await_db = 'await db.' in content or 'await database.' in content
            has_try_except = 'try:' in content and 'except' in content
            
            if has_await_db and not has_try_except:
                missing_error_handling.append(str(relative_path))
                print_warning(f"{relative_path}: Database operations without try-except")
                warnings.append(f"Missing DB error handling in {relative_path}")
            
            # Check for potential N+1 queries (DB operations in loops)
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if any(op in line for op in ['find_one', 'update_one', 'insert_one']):
                    # Check if inside a loop (simple heuristic)
                    context_start = max(0, i - 10)
                    context = '\n'.join(lines[context_start:i+1])
                    if 'for ' in context or 'while ' in context:
                        potential_n_plus_1.append((str(relative_path), i+1))
                        print_warning(f"{relative_path}:{i+1}: Potential N+1 query (DB op in loop)")
        
        except Exception:
            pass
    
    stats = {
        'db_files': len(db_files),
        'missing_error_handling': len(missing_error_handling),
        'potential_n_plus_1': len(potential_n_plus_1)
    }
    
    return warnings, stats


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("DATABASE OPERATIONS VALIDATION".center(80))
    print("="*80 + "\n")
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run check
    warnings, stats = check_database_operations(project_root)
    
    # Print summary
    print("\n" + "="*80)
    print("RESULTS".center(80))
    print("="*80 + "\n")
    
    print_info(f"Files with database operations: {stats['db_files']}")
    print_info(f"Files missing error handling: {stats['missing_error_handling']}")
    print_info(f"Potential N+1 queries detected: {stats['potential_n_plus_1']}")
    
    if warnings:
        print_warning(f"\n{len(warnings)} WARNINGS found")
        if stats['missing_error_handling'] > 0:
            print_warning(f"\n💡 Tip: Wrap database operations in try-except blocks")
        if stats['potential_n_plus_1'] > 0:
            print_warning(f"\n💡 Tip: Consider using bulk operations or aggregation for loops")
    else:
        print_success("\n✓ Database operations have proper error handling!")
    
    print()
    
    # Exit with appropriate code (warnings don't cause failure)
    sys.exit(0)


if __name__ == "__main__":
    main()
