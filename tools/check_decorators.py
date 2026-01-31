#!/usr/bin/env python3
"""
Decorator Usage Validation Tool
Checks decorator usage in command handlers
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


def extract_decorators_and_category(tree: ast.AST) -> tuple:
    """Extract decorators from handle function and category from COMMAND_INFO"""
    decorators = []
    category = None
    
    for node in ast.walk(tree):
        # Extract category from COMMAND_INFO
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'COMMAND_INFO':
                    if isinstance(node.value, ast.Dict):
                        for key, value in zip(node.value.keys, node.value.values):
                            if isinstance(key, ast.Constant) and key.value == 'category':
                                if isinstance(value, ast.Constant):
                                    category = value.value
        
        # Extract decorators from handle function
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == 'handle':
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name):
                    decorators.append(decorator.id)
                elif isinstance(decorator, ast.Call):
                    if isinstance(decorator.func, ast.Name):
                        decorators.append(decorator.func.id)
    
    return decorators, category


def check_decorators(project_root: Path) -> tuple:
    """
    Check decorator usage
    
    Returns:
        Tuple of (warnings list, stats dict)
    """
    handlers_dir = project_root / "handlers"
    warnings = []
    
    missing_log_command = []
    missing_require_admin = []
    decorator_order_issues = []
    
    if not handlers_dir.exists():
        return warnings, {}
    
    # Find all handler files
    py_files = list(handlers_dir.rglob("*.py"))
    py_files = [f for f in py_files if not f.name.startswith("_")]
    
    print_info(f"Checking decorators in {len(py_files)} handler files...")
    
    for py_file in py_files:
        relative_path = py_file.relative_to(project_root)
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'COMMAND_INFO' not in content or 'def handle(' not in content:
                continue
            
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            
            decorators, category = extract_decorators_and_category(tree)
            
            if not decorators and not category:
                continue
            
            # Check for @log_command (recommended for all commands)
            if 'log_command' not in decorators:
                print_warning(f"{relative_path}: Missing @log_command decorator")
                missing_log_command.append(str(relative_path))
            
            # Check for permission decorators in admin commands
            admin_categories = ['admin', 'moderation', 'federation', 'antiflood', 'antiraid']
            if category and category.lower() in admin_categories:
                if 'require_admin' not in decorators:
                    print_warning(f"{relative_path}: Admin command without @require_admin")
                    missing_require_admin.append(str(relative_path))
                    warnings.append(f"Missing @require_admin in {relative_path}")
            
            # Check decorator order (log_command should typically be first)
            if decorators and len(decorators) > 1:
                if 'log_command' in decorators and decorators[0] != 'log_command':
                    print_info(f"{relative_path}: @log_command not first (current order: {', '.join(decorators)})")
                    decorator_order_issues.append(str(relative_path))
        
        except Exception:
            pass
    
    stats = {
        'missing_log_command': len(missing_log_command),
        'missing_require_admin': len(missing_require_admin),
        'decorator_order_issues': len(decorator_order_issues)
    }
    
    return warnings, stats


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("DECORATOR USAGE VALIDATION".center(80))
    print("="*80 + "\n")
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run check
    warnings, stats = check_decorators(project_root)
    
    # Print summary
    print("\n" + "="*80)
    print("RESULTS".center(80))
    print("="*80 + "\n")
    
    print_info(f"Commands missing @log_command: {stats['missing_log_command']}")
    print_info(f"Admin commands missing @require_admin: {stats['missing_require_admin']}")
    print_info(f"Commands with decorator order suggestions: {stats['decorator_order_issues']}")
    
    if warnings:
        print_warning(f"\n{len(warnings)} WARNINGS found")
    else:
        print_success("\n✓ Decorator usage looks good!")
    
    print()
    
    # Exit with appropriate code (warnings don't cause failure)
    sys.exit(0)


if __name__ == "__main__":
    main()
