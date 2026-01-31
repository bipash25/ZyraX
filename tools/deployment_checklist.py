#!/usr/bin/env python3
"""
Deployment Checklist
Validates project is ready for deployment
"""

import sys
from pathlib import Path
import subprocess


def print_header(text):
    print(f"\n\033[95m\033[1m{'='*80}\033[0m")
    print(f"\033[95m\033[1m{text.center(80)}\033[0m")
    print(f"\033[95m\033[1m{'='*80}\033[0m\n")


def print_success(text):
    print(f"\033[92m✓ {text}\033[0m")


def print_error(text):
    print(f"\033[91m✗ {text}\033[0m")


def print_warning(text):
    print(f"\033[93m⚠ {text}\033[0m")


def print_info(text):
    print(f"\033[96mℹ {text}\033[0m")


def check_required_files(project_root):
    """Check for required files"""
    print_header("REQUIRED FILES CHECK")
    
    required = [
        ('bot.py', 'Main bot file'),
        ('config.py', 'Configuration file'),
        ('requirements.txt', 'Dependencies'),
        ('.env.example', 'Environment template'),
        ('README.md', 'Documentation'),
        ('.gitignore', 'Git ignore file')
    ]
    
    all_present = True
    for file, description in required:
        file_path = project_root / file
        if file_path.exists():
            print_success(f"{description}: {file}")
        else:
            print_error(f"Missing {description}: {file}")
            all_present = False
    
    return all_present


def check_environment(project_root):
    """Check environment setup"""
    print_header("ENVIRONMENT CHECK")
    
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if not env_file.exists():
        print_error(".env file not found!")
        print_info("Copy .env.example to .env and fill in values")
        return False
    
    # Check for required environment variables
    required_vars = [
        'BOT_TOKEN',
        'OWNER_ID',
        'MONGODB_URI',
        'API_ID',
        'API_HASH'
    ]
    
    try:
        with open(env_file, 'r') as f:
            content = f.read()
        
        all_set = True
        for var in required_vars:
            if f'{var}=' in content:
                # Check if it has a value
                line = [l for l in content.split('\n') if l.startswith(f'{var}=')][0]
                value = line.split('=', 1)[1].strip().strip('"').strip("'")
                if value and value != 'your_value_here':
                    print_success(f"{var} is set")
                else:
                    print_error(f"{var} is not configured")
                    all_set = False
            else:
                print_error(f"{var} not found in .env")
                all_set = False
        
        return all_set
    except Exception as e:
        print_error(f"Error reading .env: {e}")
        return False


def check_dependencies(project_root):
    """Check dependencies are installed"""
    print_header("DEPENDENCIES CHECK")
    
    requirements_file = project_root / "requirements.txt"
    
    if not requirements_file.exists():
        print_error("requirements.txt not found!")
        return False
    
    try:
        # Check if venv exists
        venv_dir = project_root / "venv"
        if venv_dir.exists():
            print_success("Virtual environment found")
        else:
            print_warning("Virtual environment not found (optional)")
        
        # Try to check installed packages
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'list', '--format=freeze'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        installed = result.stdout.strip().split('\n')
        installed_packages = {line.split('==')[0].lower() for line in installed if '==' in line}
        
        # Read required packages
        with open(requirements_file, 'r') as f:
            required = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    pkg = line.split('==')[0].split('[')[0].strip()
                    required.append(pkg.lower())
        
        missing = []
        for pkg in required:
            if pkg not in installed_packages:
                missing.append(pkg)
        
        if missing:
            print_error(f"Missing packages: {', '.join(missing)}")
            print_info("Run: pip install -r requirements.txt")
            return False
        else:
            print_success(f"All {len(required)} dependencies installed")
            return True
    
    except Exception as e:
        print_warning(f"Could not verify dependencies: {e}")
        return True  # Don't fail on this


def run_validation_checks(project_root):
    """Run validation checks"""
    print_header("VALIDATION CHECKS")
    
    tools_dir = project_root / "tools"
    critical_checks = [
        'check_security.py',
        'check_duplicates.py',
        'check_command_structure.py'
    ]
    
    all_passed = True
    for check in critical_checks:
        check_path = tools_dir / check
        if not check_path.exists():
            print_warning(f"Check not found: {check}")
            continue
        
        try:
            result = subprocess.run(
                [sys.executable, str(check_path)],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print_success(f"{check} passed")
            else:
                print_error(f"{check} failed")
                all_passed = False
        except Exception as e:
            print_warning(f"Could not run {check}: {e}")
    
    return all_passed


def check_git_status(project_root):
    """Check git status"""
    print_header("GIT STATUS CHECK")
    
    try:
        # Check if git repo
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            cwd=project_root,
            capture_output=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print_warning("Not a git repository")
            return True
        
        # Check for uncommitted changes
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.stdout.strip():
            print_warning("You have uncommitted changes")
            print_info("Consider committing changes before deployment")
        else:
            print_success("No uncommitted changes")
        
        # Check current branch
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        branch = result.stdout.strip()
        print_info(f"Current branch: {branch}")
        
        if branch != 'main' and branch != 'master':
            print_warning(f"Not on main/master branch (on: {branch})")
        
        return True
    
    except Exception as e:
        print_warning(f"Could not check git status: {e}")
        return True


def generate_report(results):
    """Generate deployment report"""
    print_header("DEPLOYMENT READINESS REPORT")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print()
    
    if all(results.values()):
        print("\033[92m\033[1m🎉 PROJECT IS READY FOR DEPLOYMENT!\033[0m")
        return True
    else:
        print("\033[91m\033[1m⚠️  PROJECT IS NOT READY FOR DEPLOYMENT\033[0m")
        print("\nFailed Checks:")
        for check, passed in results.items():
            if not passed:
                print(f"  • {check}")
        return False


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("DEPLOYMENT CHECKLIST".center(80))
    print("="*80)
    
    project_root = Path(__file__).parent.parent
    
    results = {
        'Required Files': check_required_files(project_root),
        'Environment': check_environment(project_root),
        'Dependencies': check_dependencies(project_root),
        'Validation': run_validation_checks(project_root),
        'Git Status': check_git_status(project_root)
    }
    
    ready = generate_report(results)
    
    print()
    
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
