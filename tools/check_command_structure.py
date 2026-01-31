#!/usr/bin/env python3
"""
Command Structure Validation Tool
Checks command file structure and COMMAND_INFO validity
"""

import sys
import ast
from pathlib import Path
from collections import defaultdict
from typing import Dict, List


def print_success(text):
    print(f"\033[92m✓ {text}\033[0m")


def print_warning(text):
    print(f"\033[93m⚠ {text}\033[0m")


def print_error(text):
    print(f"\033[91m✗ {text}\033[0m")


def print_info(text):
    print(f"\033[96mℹ {text}\033[0m")


def validate_command_info(info: Dict, file_path: Path, commands: Dict, aliases: Dict) -> List[str]:
    """
    Validate COMMAND_INFO dictionary
    
    Returns:
        List of error messages
    """
    errors = []
    required_fields = ['name', 'description', 'category']
    recommended_fields = ['usage', 'aliases']
    
    # Check required fields
    for field in required_fields:
        if field not in info:
            print_error(f"{file_path}: Missing required field '{field}' in COMMAND_INFO")
            errors.append(f"Missing '{field}' in {file_path}")
    
    # Check recommended fields
    for field in recommended_fields:
        if field not in info:
            print_warning(f"{file_path}: Missing recommended field '{field}' in COMMAND_INFO")
    
    # Validate field types
    if 'name' in info:
        name = info['name']
        if not isinstance(name, str):
            print_error(f"{file_path}: 'name' must be a string")
            errors.append(f"Invalid 'name' type in {file_path}")
        else:
            # Track command name
            if name in commands:
                print_error(f"{file_path}: Duplicate command name '{name}' (also in {commands[name]})")
                errors.append(f"Duplicate command '{name}'")
            else:
                commands[name] = file_path
    
    if 'aliases' in info:
        alias_list = info['aliases']
        if not isinstance(alias_list, list):
            print_error(f"{file_path}: 'aliases' must be a list")
            errors.append(f"Invalid 'aliases' type in {file_path}")
        else:
            for alias in alias_list:
                if alias in aliases:
                    print_error(f"{file_path}: Duplicate alias '{alias}' (also in {aliases[alias]})")
                    errors.append(f"Duplicate alias '{alias}'")
                elif alias in commands:
                    print_error(f"{file_path}: Alias '{alias}' conflicts with command in {commands[alias]}")
                    errors.append(f"Conflicting alias '{alias}'")
                else:
                    aliases[alias] = file_path
    
    return errors


def extract_command_info(tree: ast.AST) -> tuple:
    """
    Extract COMMAND_INFO and check for handle function
    
    Returns:
        Tuple of (command_info dict, has_handle bool)
    """
    command_info = None
    has_handle = False
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'COMMAND_INFO':
                    if isinstance(node.value, ast.Dict):
                        command_info = {}
                        for key, value in zip(node.value.keys, node.value.values):
                            if isinstance(key, ast.Constant):
                                if isinstance(value, ast.Constant):
                                    command_info[key.value] = value.value
                                elif isinstance(value, ast.List):
                                    command_info[key.value] = [
                                        item.value for item in value.elts
                                        if isinstance(item, ast.Constant)
                                    ]
        
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == 'handle':
            has_handle = True
    
    return command_info, has_handle


def check_command_structure(project_root: Path) -> tuple:
    """
    Main command structure check
    
    Returns:
        Tuple of (errors list, warnings list, stats dict)
    """
    handlers_dir = project_root / "handlers"
    errors = []
    warnings = []
    commands = {}
    aliases = {}
    categories = defaultdict(list)
    files_checked = 0
    commands_found = 0
    
    if not handlers_dir.exists():
        print_error(f"Handlers directory not found: {handlers_dir}")
        errors.append("Handlers directory missing")
        return errors, warnings, {}
    
    # Find all Python files in handlers
    py_files = list(handlers_dir.rglob("*.py"))
    py_files = [f for f in py_files if not f.name.startswith("_")]
    
    print_info(f"Found {len(py_files)} handler files to check")
    
    for py_file in py_files:
        files_checked += 1
        relative_path = py_file.relative_to(project_root)
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if file has COMMAND_INFO
            if 'COMMAND_INFO' not in content:
                continue
            
            # Parse the file
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                print_error(f"{relative_path}: Syntax error - {e}")
                errors.append(f"Syntax error in {relative_path}")
                continue
            
            # Extract COMMAND_INFO and check handle function
            command_info, has_handle = extract_command_info(tree)
            
            if command_info:
                commands_found += 1
                file_errors = validate_command_info(command_info, relative_path, commands, aliases)
                errors.extend(file_errors)
                
                if not has_handle:
                    print_error(f"{relative_path}: Has COMMAND_INFO but no handle() function")
                    errors.append(f"Missing handle() in {relative_path}")
                
                # Track categories
                if 'category' in command_info and isinstance(command_info['category'], str):
                    categories[command_info['category'].upper()].append(
                        command_info.get('name', 'unknown')
                    )
        
        except Exception as e:
            print_error(f"{relative_path}: Error reading file - {e}")
            errors.append(f"Error reading {relative_path}")
    
    stats = {
        'files_checked': files_checked,
        'commands_found': commands_found,
        'total_commands': len(commands),
        'total_aliases': len(aliases),
        'categories': dict(categories)
    }
    
    print_info(f"Checked {files_checked} files, found {commands_found} commands")
    
    return errors, warnings, stats


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("COMMAND STRUCTURE VALIDATION".center(80))
    print("="*80 + "\n")
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run check
    errors, warnings, stats = check_command_structure(project_root)
    
    # Print summary
    print("\n" + "="*80)
    print("RESULTS".center(80))
    print("="*80 + "\n")
    
    print(f"Files checked: {stats.get('files_checked', 0)}")
    print(f"Commands found: {stats.get('commands_found', 0)}")
    print(f"Unique commands: {stats.get('total_commands', 0)}")
    print(f"Unique aliases: {stats.get('total_aliases', 0)}")
    
    if errors:
        print_error(f"\n{len(errors)} ERRORS found:")
        for error in errors[:10]:
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
    else:
        print_success("\n✓ No errors found!")
    
    if warnings:
        print_warning(f"\n{len(warnings)} WARNINGS:")
        for warning in warnings[:10]:
            print(f"  - {warning}")
    
    # Print categories
    categories = stats.get('categories', {})
    if categories:
        print(f"\n\nCommands by category ({len(categories)} categories):")
        for category, cmds in sorted(categories.items()):
            print(f"  • {category:15s}: {len(cmds):3d} commands")
    
    print()
    
    # Exit with appropriate code
    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
