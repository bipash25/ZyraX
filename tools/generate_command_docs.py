#!/usr/bin/env python3
"""
Command Documentation Generator
Automatically generates Markdown documentation for all bot commands
"""

import sys
import ast
from pathlib import Path
from collections import defaultdict
from datetime import datetime


def extract_command_info(file_path: Path) -> dict:
    """Extract COMMAND_INFO from a handler file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'COMMAND_INFO' not in content:
            return None
        
        tree = ast.parse(content)
        
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
                            return command_info
    except Exception:
        return None
    
    return None


def generate_documentation(project_root: Path, output_file: str = "COMMANDS.md"):
    """Generate command documentation"""
    
    handlers_dir = project_root / "handlers"
    
    if not handlers_dir.exists():
        print(f"Error: Handlers directory not found: {handlers_dir}")
        sys.exit(1)
    
    # Collect all commands
    commands_by_category = defaultdict(list)
    
    py_files = list(handlers_dir.rglob("*.py"))
    py_files = [f for f in py_files if not f.name.startswith("_")]
    
    for py_file in py_files:
        command_info = extract_command_info(py_file)
        if command_info:
            category = command_info.get('category', 'misc').upper()
            commands_by_category[category].append(command_info)
    
    # Sort categories
    sorted_categories = sorted(commands_by_category.keys())
    
    # Generate Markdown
    output_path = project_root / output_file
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Header
        f.write("# ZyraX Bot - Command Reference\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("Complete list of all bot commands organized by category.\n\n")
        
        # Table of Contents
        f.write("## 📋 Table of Contents\n\n")
        for category in sorted_categories:
            category_name = category.replace('_', ' ').title()
            f.write(f"- [{category_name}](#{category.lower().replace('_', '-')})\n")
        f.write("\n---\n\n")
        
        # Statistics
        total_commands = sum(len(cmds) for cmds in commands_by_category.values())
        f.write("## 📊 Statistics\n\n")
        f.write(f"- **Total Commands:** {total_commands}\n")
        f.write(f"- **Categories:** {len(sorted_categories)}\n\n")
        
        # Commands by category
        for category in sorted_categories:
            commands = commands_by_category[category]
            category_name = category.replace('_', ' ').title()
            
            f.write(f"## {category_name}\n\n")
            f.write(f"*{len(commands)} commands in this category*\n\n")
            
            # Sort commands by name
            commands.sort(key=lambda x: x.get('name', ''))
            
            for cmd in commands:
                name = cmd.get('name', 'unknown')
                description = cmd.get('description', 'No description')
                usage = cmd.get('usage', f'/{name}')
                aliases = cmd.get('aliases', [])
                
                f.write(f"### `/{name}`\n\n")
                f.write(f"**Description:** {description}\n\n")
                f.write(f"**Usage:** `{usage}`\n\n")
                
                if aliases:
                    alias_str = ", ".join([f"`/{alias}`" for alias in aliases])
                    f.write(f"**Aliases:** {alias_str}\n\n")
                
                # Additional fields
                if cmd.get('admin_only'):
                    f.write("**Permission:** Admin only 🔒\n\n")
                
                if cmd.get('owner_only'):
                    f.write("**Permission:** Owner only 👑\n\n")
                
                if cmd.get('group_only'):
                    f.write("**Scope:** Groups only 👥\n\n")
                
                permissions = cmd.get('permissions', [])
                if permissions:
                    perms_str = ", ".join([f"`{p}`" for p in permissions])
                    f.write(f"**Required Permissions:** {perms_str}\n\n")
                
                f.write("---\n\n")
        
        # Footer
        f.write("## 📝 Notes\n\n")
        f.write("- Commands marked with 🔒 require admin permissions\n")
        f.write("- Commands marked with 👑 are owner-only\n")
        f.write("- Commands marked with 👥 work only in groups\n")
        f.write("- Use `/help <command>` to get detailed help for a specific command\n\n")
        f.write("---\n\n")
        f.write("*This documentation was automatically generated from command source files.*\n")
    
    print(f"✓ Documentation generated: {output_path}")
    print(f"  Total commands: {total_commands}")
    print(f"  Categories: {len(sorted_categories)}")


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("COMMAND DOCUMENTATION GENERATOR".center(80))
    print("="*80 + "\n")
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Generate documentation
    generate_documentation(project_root)
    
    print("\n✓ Done!\n")


if __name__ == "__main__":
    main()
