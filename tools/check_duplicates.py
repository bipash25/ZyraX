#!/usr/bin/env python3
"""
Duplicate Command/Alias Detection Tool
Checks for duplicate or conflicting commands and aliases
"""

import sys
import ast
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set


def print_success(text):
    print(f"\033[92m✓ {text}\033[0m")


def print_error(text):
    print(f"\033[91m✗ {text}\033[0m")


def print_info(text):
    print(f"\033[96mℹ {text}\033[0m")


def extract_command_data(tree: ast.AST) -> tuple:
    """Extract command name and aliases from AST"""
    command_name = None
    aliases = []
    category = None
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'COMMAND_INFO':
                    if isinstance(node.value, ast.Dict):
                        for key, value in zip(node.value.keys, node.value.values):
                            if isinstance(key, ast.Constant):
                                if key.value == 'name' and isinstance(value, ast.Constant):
                                    command_name = value.value
                                elif key.value == 'category' and isinstance(value, ast.Constant):
                                    category = value.value
                                elif key.value == 'aliases' and isinstance(value, ast.List):
                                    aliases = [
                                        item.value for item in value.elts
                                        if isinstance(item, ast.Constant)
                                    ]
    
    return command_name, aliases, category


def check_duplicates(project_root: Path) -> tuple:
    """
    Check for duplicate commands and aliases
    
    Returns:
        Tuple of (errors list, commands dict, aliases dict, categories dict)
    """
    handlers_dir = project_root / "handlers"
    errors = []
    
    commands = {}  # command_name -> file_path
    aliases = {}   # alias -> file_path
    categories = defaultdict(list)  # category -> [commands]
    
    if not handlers_dir.exists():
        print_error(f"Handlers directory not found: {handlers_dir}")
        errors.append("Handlers directory missing")
        return errors, commands, aliases, categories
    
    # Find all Python files
    py_files = list(handlers_dir.rglob("*.py"))
    py_files = [f for f in py_files if not f.name.startswith("_")]
    
    print_info(f"Scanning {len(py_files)} files for duplicates...")
    
    for py_file in py_files:
        relative_path = py_file.relative_to(project_root)
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'COMMAND_INFO' not in content:
                continue
            
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            
            command_name, alias_list, category = extract_command_data(tree)
            
            if command_name:
                # Check for duplicate command name
                if command_name in commands:
                    print_error(
                        f"Duplicate command '{command_name}':\n"
                        f"  - {commands[command_name]}\n"
                        f"  - {relative_path}"
                    )
                    errors.append(f"Duplicate command '{command_name}'")
                else:
                    commands[command_name] = relative_path
                
                # Track category
                if category:
                    categories[category.upper()].append(command_name)
            
            # Check for duplicate aliases
            for alias in alias_list:
                if alias in aliases:
                    print_error(
                        f"Duplicate alias '{alias}':\n"
                        f"  - {aliases[alias]}\n"
                        f"  - {relative_path}"
                    )
                    errors.append(f"Duplicate alias '{alias}'")
                elif alias in commands:
                    print_error(
                        f"Alias '{alias}' conflicts with command:\n"
                        f"  - Command in: {commands[alias]}\n"
                        f"  - Alias in: {relative_path}"
                    )
                    errors.append(f"Conflicting alias '{alias}'")
                else:
                    aliases[alias] = relative_path
        
        except Exception as e:
            pass
    
    return errors, commands, aliases, categories


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("DUPLICATE COMMAND/ALIAS DETECTION".center(80))
    print("="*80 + "\n")
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run check
    errors, commands, aliases, categories = check_duplicates(project_root)
    
    # Print results
    print("\n" + "="*80)
    print("RESULTS".center(80))
    print("="*80 + "\n")
    
    print_info(f"Total unique commands: {len(commands)}")
    print_info(f"Total unique aliases: {len(aliases)}")
    
    # Check for conflicts
    conflicts = set(aliases.keys()) & set(commands.keys())
    if conflicts:
        print_error(f"\nFound {len(conflicts)} alias/command conflicts:")
        for conflict in conflicts:
            print(f"  • {conflict}")
    else:
        print_success("\nNo alias/command conflicts found")
    
    # Print error summary
    if errors:
        print_error(f"\n{len(errors)} ERRORS found:")
        for error in errors[:20]:
            print(f"  - {error}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more")
    else:
        print_success("\n✓ No duplicate commands or aliases found!")
    
    # Print categories
    if categories:
        print(f"\n\nCommands by category ({len(categories)} categories):")
        for category, cmds in sorted(categories.items()):
            print(f"  • {category:15s}: {len(cmds):3d} commands")
    
    print()
    
    # Exit with appropriate code
    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
