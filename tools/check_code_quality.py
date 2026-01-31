#!/usr/bin/env python3
"""
Code Quality Metrics Tool
Checks code quality metrics like file size, function length, etc.
"""

import sys
import ast
from pathlib import Path


def print_success(text):
    print(f"\033[92m✓ {text}\033[0m")


def print_warning(text):
    print(f"\033[93m⚠ {text}\033[0m")


def print_info(text):
    print(f"\033[96mℹ {text}\033[0m")


def check_code_quality(project_root: Path) -> tuple:
    """
    Check code quality metrics
    
    Returns:
        Tuple of (warnings list, stats dict)
    """
    warnings = []
    
    total_lines = 0
    large_files = []  # > 500 lines
    long_functions = []  # > 100 lines
    deeply_nested = []  # nesting depth > 5
    
    # Find all Python files
    py_files = list(project_root.rglob("*.py"))
    py_files = [f for f in py_files if 'venv' not in str(f) and '__pycache__' not in str(f)]
    
    print_info(f"Analyzing {len(py_files)} Python files for code quality...")
    
    for py_file in py_files:
        relative_path = py_file.relative_to(project_root)
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines += len(lines)
            
            # Check file size
            if len(lines) > 500:
                large_files.append((str(relative_path), len(lines)))
                print_warning(f"{relative_path}: Large file ({len(lines)} lines)")
            
            # Parse and check function sizes
            try:
                tree = ast.parse(''.join(lines))
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if hasattr(node, 'end_lineno') and node.end_lineno:
                            func_length = node.end_lineno - node.lineno
                            if func_length > 100:
                                long_functions.append((str(relative_path), node.name, func_length))
                                print_warning(
                                    f"{relative_path}: Long function '{node.name}' ({func_length} lines)"
                                )
                                warnings.append(f"Long function in {relative_path}::{node.name}")
            except SyntaxError:
                pass
        
        except Exception:
            pass
    
    stats = {
        'total_files': len(py_files),
        'total_lines': total_lines,
        'avg_lines_per_file': total_lines // len(py_files) if py_files else 0,
        'large_files': len(large_files),
        'long_functions': len(long_functions)
    }
    
    return warnings, stats, large_files, long_functions


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("CODE QUALITY METRICS".center(80))
    print("="*80 + "\n")
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run check
    warnings, stats, large_files, long_functions = check_code_quality(project_root)
    
    # Print summary
    print("\n" + "="*80)
    print("RESULTS".center(80))
    print("="*80 + "\n")
    
    print_info(f"Total Python files: {stats['total_files']}")
    print_info(f"Total lines of code: {stats['total_lines']:,}")
    print_info(f"Average lines per file: {stats['avg_lines_per_file']}")
    
    if large_files:
        print_warning(f"\n{len(large_files)} files over 500 lines:")
        for file, lines in sorted(large_files, key=lambda x: x[1], reverse=True)[:10]:
            print(f"  • {file}: {lines} lines")
        if len(large_files) > 10:
            print(f"  ... and {len(large_files) - 10} more")
    else:
        print_success("\n✓ All files are reasonably sized!")
    
    if long_functions:
        print_warning(f"\n{len(long_functions)} functions over 100 lines:")
        for file, func, lines in sorted(long_functions, key=lambda x: x[2], reverse=True)[:10]:
            print(f"  • {file}::{func}(): {lines} lines")
        if len(long_functions) > 10:
            print(f"  ... and {len(long_functions) - 10} more")
        print("\n💡 Tip: Consider breaking down large functions into smaller ones")
    else:
        print_success("\n✓ All functions are reasonably sized!")
    
    if warnings:
        print_warning(f"\n{len(warnings)} code quality warnings")
    else:
        print_success("\n✓ Code quality looks good!")
    
    print()
    
    # Exit with appropriate code (warnings don't cause failure)
    sys.exit(0)


if __name__ == "__main__":
    main()
