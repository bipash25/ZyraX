#!/usr/bin/env python3
"""
Security Issues Validation Tool
Checks for common security vulnerabilities
"""

import sys
import re
from pathlib import Path


def print_success(text):
    print(f"\033[92m✓ {text}\033[0m")


def print_warning(text):
    print(f"\033[93m⚠ {text}\033[0m")


def print_error(text):
    print(f"\033[91m✗ {text}\033[0m")


def print_info(text):
    print(f"\033[96mℹ {text}\033[0m")


def check_security_issues(project_root: Path) -> tuple:
    """
    Check for common security issues
    
    Returns:
        Tuple of (errors list, warnings list, stats dict)
    """
    errors = []
    warnings = []
    
    hardcoded_secrets = []
    eval_exec_usage = []
    sql_injection_risks = []
    shell_injection_risks = []
    
    # Find all Python files
    py_files = list(project_root.rglob("*.py"))
    py_files = [f for f in py_files if 'venv' not in str(f) and '__pycache__' not in str(f)]
    
    print_info(f"Scanning {len(py_files)} Python files for security issues...")
    
    for py_file in py_files:
        relative_path = py_file.relative_to(project_root)
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for hardcoded credentials/tokens
            # Bot token pattern: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
            token_pattern = r'["\'](\d{10}:[A-Za-z0-9_-]{35})["\']'
            if re.search(token_pattern, content):
                if 'example' not in content.lower() and 'your_token' not in content.lower():
                    hardcoded_secrets.append(str(relative_path))
                    print_error(f"{relative_path}: Possible hardcoded bot token")
                    errors.append(f"Hardcoded token in {relative_path}")
            
            # Check for hardcoded passwords
            password_pattern = r'password\s*=\s*["\'](?!.*\{.*\}).{8,}["\']'
            if re.search(password_pattern, content, re.IGNORECASE):
                if 'example' not in content.lower():
                    hardcoded_secrets.append(str(relative_path))
                    print_warning(f"{relative_path}: Possible hardcoded password")
                    warnings.append(f"Hardcoded password in {relative_path}")
            
            # Check for eval/exec usage
            if re.search(r'\beval\s*\(', content) or re.search(r'\bexec\s*\(', content):
                # Allow in owner commands
                if 'owner' not in str(relative_path).lower():
                    eval_exec_usage.append(str(relative_path))
                    print_error(f"{relative_path}: Uses eval() or exec() - DANGEROUS!")
                    errors.append(f"Dangerous eval/exec in {relative_path}")
            
            # Check for SQL injection risks
            sql_patterns = [
                r'\.execute\(["\'].*%s.*["\'].*%',
                r'\.execute\(f["\'].*SELECT.*\{',
                r'["\']SELECT.*\+.*["\']'
            ]
            for pattern in sql_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    sql_injection_risks.append(str(relative_path))
                    print_warning(f"{relative_path}: Potential SQL injection risk")
                    warnings.append(f"SQL injection risk in {relative_path}")
                    break
            
            # Check for shell injection risks
            if 'subprocess' in content or 'os.system' in content:
                if 'shell=True' in content:
                    shell_injection_risks.append(str(relative_path))
                    print_error(f"{relative_path}: subprocess with shell=True - command injection risk")
                    errors.append(f"Shell injection risk in {relative_path}")
        
        except Exception:
            pass
    
    stats = {
        'total_files': len(py_files),
        'hardcoded_secrets': len(hardcoded_secrets),
        'eval_exec_usage': len(eval_exec_usage),
        'sql_injection_risks': len(sql_injection_risks),
        'shell_injection_risks': len(shell_injection_risks)
    }
    
    return errors, warnings, stats


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("SECURITY ISSUES VALIDATION".center(80))
    print("="*80 + "\n")
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run check
    errors, warnings, stats = check_security_issues(project_root)
    
    # Print summary
    print("\n" + "="*80)
    print("RESULTS".center(80))
    print("="*80 + "\n")
    
    print_info(f"Total files scanned: {stats['total_files']}")
    print_info(f"Files with hardcoded secrets: {stats['hardcoded_secrets']}")
    print_info(f"Files with eval/exec: {stats['eval_exec_usage']}")
    print_info(f"Files with SQL injection risks: {stats['sql_injection_risks']}")
    print_info(f"Files with shell injection risks: {stats['shell_injection_risks']}")
    
    if errors:
        print_error(f"\n{len(errors)} CRITICAL ERRORS found:")
        for error in errors:
            print(f"  - {error}")
        print("\n🔒 Security Tips:")
        print("  • Move secrets to environment variables")
        print("  • Avoid eval/exec in user-facing code")
        print("  • Use shell=False with subprocess")
        print("  • Use parameterized queries for databases")
    else:
        print_success("\n✓ No critical security issues found!")
    
    if warnings:
        print_warning(f"\n{len(warnings)} WARNINGS:")
        for warning in warnings[:10]:
            print(f"  - {warning}")
    
    print()
    
    # Exit with appropriate code
    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
