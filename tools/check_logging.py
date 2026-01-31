#!/usr/bin/env python3
"""
Logging Consistency Validation Tool
Checks logging usage patterns and consistency
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


def check_logging_patterns(project_root: Path) -> tuple:
    """
    Check logging patterns
    
    Returns:
        Tuple of (warnings list, stats dict)
    """
    warnings = []
    
    files_with_logging = []
    files_with_print = []
    inconsistent_logger_names = []
    missing_log_levels = []
    log_levels_used = {'debug': 0, 'info': 0, 'warning': 0, 'error': 0, 'critical': 0}
    
    # Find all Python files
    py_files = list(project_root.rglob("*.py"))
    py_files = [f for f in py_files if 'venv' not in str(f) and '__pycache__' not in str(f)]
    
    print_info(f"Scanning {len(py_files)} Python files for logging patterns...")
    
    for py_file in py_files:
        relative_path = py_file.relative_to(project_root)
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for logging import
            has_logging = 'import logging' in content
            
            if has_logging:
                files_with_logging.append(str(relative_path))
                
                # Check logger name pattern
                logger_pattern = r'logger = logging\.getLogger\(["\'](.+?)["\']\)'
                logger_matches = re.findall(logger_pattern, content)
                
                if logger_matches:
                    # Should be __name__ or the module path
                    for logger_name in logger_matches:
                        if logger_name != '__name__' and not logger_name.startswith('handlers.'):
                            inconsistent_logger_names.append((str(relative_path), logger_name))
                            print_warning(f"{relative_path}: Logger name '{logger_name}' (use __name__)")
                
                # Count log level usage
                for level in log_levels_used.keys():
                    pattern = f'logger.{level}\\('
                    count = len(re.findall(pattern, content))
                    log_levels_used[level] += count
                
                # Check if file uses logging but never calls logger
                if not any(f'logger.{level}(' in content for level in log_levels_used.keys()):
                    missing_log_levels.append(str(relative_path))
                    print_warning(f"{relative_path}: Imports logging but never uses it")
            
            # Check for print statements (should use logging)
            if 'handlers/' in str(relative_path) or 'core/' in str(relative_path):
                # Look for print() but ignore f-string printing for now
                print_pattern = r'\bprint\s*\('
                if re.search(print_pattern, content):
                    # Exclude if it's in a __main__ block
                    if '__main__' not in content:
                        files_with_print.append(str(relative_path))
                        print_warning(f"{relative_path}: Uses print() instead of logging")
                        warnings.append(f"print() in {relative_path}")
        
        except Exception:
            pass
    
    stats = {
        'total_files': len(py_files),
        'files_with_logging': len(files_with_logging),
        'files_with_print': len(files_with_print),
        'inconsistent_logger_names': len(inconsistent_logger_names),
        'missing_log_levels': len(missing_log_levels),
        'log_levels_used': log_levels_used
    }
    
    return warnings, stats


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("LOGGING CONSISTENCY VALIDATION".center(80))
    print("="*80 + "\n")
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run check
    warnings, stats = check_logging_patterns(project_root)
    
    # Print summary
    print("\n" + "="*80)
    print("RESULTS".center(80))
    print("="*80 + "\n")
    
    print_info(f"Total files scanned: {stats['total_files']}")
    print_info(f"Files using logging: {stats['files_with_logging']}")
    print_info(f"Files using print(): {stats['files_with_print']}")
    print_info(f"Files with inconsistent logger names: {stats['inconsistent_logger_names']}")
    print_info(f"Files importing but not using logging: {stats['missing_log_levels']}")
    
    print("\n📊 Log Level Usage:")
    for level, count in stats['log_levels_used'].items():
        print(f"  • {level.upper():8s}: {count:4d} occurrences")
    
    if warnings:
        print_warning(f"\n{len(warnings)} WARNINGS found")
        print("\n💡 Logging Best Practices:")
        print("  • Use logging instead of print() in production code")
        print("  • Use logger = logging.getLogger(__name__)")
        print("  • Use appropriate log levels (debug, info, warning, error, critical)")
        print("  • Don't import logging if you don't use it")
    else:
        print_success("\n✓ Logging patterns are consistent!")
    
    print()
    
    # Exit with appropriate code (warnings don't cause failure)
    sys.exit(0)


if __name__ == "__main__":
    main()
