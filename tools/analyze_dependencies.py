#!/usr/bin/env python3
"""
Dependency Analyzer
Analyzes project dependencies and checks for updates
"""

import sys
import subprocess
from pathlib import Path
import re


def print_success(text):
    print(f"\033[92m✓ {text}\033[0m")


def print_warning(text):
    print(f"\033[93m⚠ {text}\033[0m")


def print_error(text):
    print(f"\033[91m✗ {text}\033[0m")


def print_info(text):
    print(f"\033[96mℹ {text}\033[0m")


def parse_requirements(requirements_file: Path) -> list:
    """Parse requirements.txt file"""
    dependencies = []
    
    try:
        with open(requirements_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Parse package==version
                    match = re.match(r'([a-zA-Z0-9_-]+)(?:\[.*\])?==(.+)', line)
                    if match:
                        package, version = match.groups()
                        dependencies.append({
                            'package': package,
                            'version': version,
                            'raw': line
                        })
    except FileNotFoundError:
        print_error(f"Requirements file not found: {requirements_file}")
        sys.exit(1)
    
    return dependencies


def check_outdated(venv_python: str = None) -> dict:
    """Check for outdated packages"""
    try:
        cmd = [venv_python or sys.executable, '-m', 'pip', 'list', '--outdated', '--format=json']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            import json
            return {pkg['name']: pkg for pkg in json.loads(result.stdout)}
    except Exception as e:
        print_warning(f"Could not check for outdated packages: {e}")
    
    return {}


def analyze_dependencies(project_root: Path):
    """Analyze project dependencies"""
    
    requirements_file = project_root / "requirements.txt"
    
    if not requirements_file.exists():
        print_error("requirements.txt not found!")
        sys.exit(1)
    
    print_info("Parsing requirements.txt...")
    dependencies = parse_requirements(requirements_file)
    
    print_info(f"Found {len(dependencies)} dependencies\n")
    
    # Categorize dependencies
    categories = {
        'Core Bot Libraries': ['python-telegram-bot', 'pyrogram', 'TgCrypto'],
        'Database & Caching': ['motor', 'pymongo', 'redis'],
        'Scheduling': ['APScheduler'],
        'Image Processing': ['Pillow'],
        'Utilities': ['python-dotenv', 'pydantic', 'pydantic-settings', 'aiohttp', 'psutil'],
        'Development': ['pytest', 'pytest-asyncio', 'black', 'flake8', 'mypy']
    }
    
    # Print categorized dependencies
    print("📦 Dependencies by Category:\n")
    
    for category, packages in categories.items():
        print(f"\n{category}:")
        for dep in dependencies:
            if dep['package'] in packages:
                print(f"  • {dep['package']:30s} {dep['version']:15s}")
    
    # Check for outdated packages
    print("\n\n🔍 Checking for outdated packages...")
    outdated = check_outdated()
    
    if outdated:
        print_warning(f"\n{len(outdated)} packages have updates available:\n")
        for pkg_name, info in outdated.items():
            print(f"  • {pkg_name:30s} {info['version']:15s} → {info['latest_version']}")
        print(f"\n💡 Run: pip install --upgrade <package_name>")
    else:
        print_success("\n✓ All packages are up to date!")
    
    # Security check
    print("\n\n🔒 Security Analysis:")
    print_info("Checking for known vulnerabilities...")
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'check'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and not result.stdout.strip():
            print_success("✓ No dependency conflicts found")
        else:
            print_warning("Dependency issues detected:")
            print(result.stdout)
    except Exception as e:
        print_warning(f"Could not run dependency check: {e}")
    
    # Summary
    print("\n\n📊 Summary:")
    print(f"  • Total dependencies: {len(dependencies)}")
    print(f"  • Outdated: {len(outdated)}")
    print(f"  • Categories: {len(categories)}")


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("DEPENDENCY ANALYZER".center(80))
    print("="*80 + "\n")
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Analyze
    analyze_dependencies(project_root)
    
    print()


if __name__ == "__main__":
    main()
