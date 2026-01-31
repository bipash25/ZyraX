"""
Comprehensive Codebase Validation Script
Checks for:
- Duplicate commands/aliases
- Missing COMMAND_INFO fields
- File structure issues
- Import errors
- Decorator consistency
- Database field usage
- Datetime usage consistency
- And more...
"""

import sys
import ast
import importlib.util
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import re

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


class CodebaseValidator:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.handlers_dir = project_root / "handlers"
        self.errors = []
        self.warnings = []
        self.info = []
        
        # Tracking dictionaries
        self.commands = {}  # command_name -> file_path
        self.aliases = {}   # alias -> file_path
        self.categories = defaultdict(list)  # category -> [commands]
        self.files_checked = 0
        self.commands_found = 0
        
    def run_all_checks(self):
        """Run all validation checks"""
        print_header("ZYRAX BOT CODEBASE VALIDATION")
        
        # Run checks
        self.check_1_command_structure()
        self.check_2_duplicate_commands()
        self.check_3_file_structure()
        self.check_4_import_consistency()
        self.check_5_decorator_usage()
        self.check_6_datetime_usage()
        self.check_7_database_operations()
        self.check_8_security_issues()
        self.check_9_code_quality()
        
        # Print summary
        self.print_summary()
        
        return len(self.errors) == 0
    
    def check_1_command_structure(self):
        """Check command file structure and COMMAND_INFO validity"""
        print_header("CHECK 1: Command Structure & COMMAND_INFO")
        
        if not self.handlers_dir.exists():
            print_error(f"Handlers directory not found: {self.handlers_dir}")
            self.errors.append("Handlers directory missing")
            return
        
        # Find all Python files in handlers
        py_files = list(self.handlers_dir.rglob("*.py"))
        py_files = [f for f in py_files if not f.name.startswith("_")]
        
        print_info(f"Found {len(py_files)} handler files to check")
        
        for py_file in py_files:
            self.files_checked += 1
            relative_path = py_file.relative_to(self.project_root)
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if file has COMMAND_INFO
                if 'COMMAND_INFO' not in content:
                    # This is okay - not all files need COMMAND_INFO
                    continue
                
                # Parse the file
                try:
                    tree = ast.parse(content)
                except SyntaxError as e:
                    print_error(f"{relative_path}: Syntax error - {e}")
                    self.errors.append(f"Syntax error in {relative_path}")
                    continue
                
                # Find COMMAND_INFO
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
                    
                    if isinstance(node, ast.FunctionDef) and node.name == 'handle':
                        has_handle = True
                
                if command_info:
                    self.commands_found += 1
                    self._validate_command_info(command_info, relative_path)
                    
                    if not has_handle:
                        print_error(f"{relative_path}: Has COMMAND_INFO but no handle() function")
                        self.errors.append(f"Missing handle() in {relative_path}")
                
            except Exception as e:
                print_error(f"{relative_path}: Error reading file - {e}")
                self.errors.append(f"Error reading {relative_path}")
        
        print_info(f"Checked {self.files_checked} files, found {self.commands_found} commands")
    
    def _validate_command_info(self, info: Dict, file_path: Path):
        """Validate COMMAND_INFO dictionary"""
        required_fields = ['name', 'description', 'category']
        recommended_fields = ['usage', 'aliases']
        
        # Check required fields
        for field in required_fields:
            if field not in info:
                print_error(f"{file_path}: Missing required field '{field}' in COMMAND_INFO")
                self.errors.append(f"Missing '{field}' in {file_path}")
        
        # Check recommended fields
        for field in recommended_fields:
            if field not in info:
                print_warning(f"{file_path}: Missing recommended field '{field}' in COMMAND_INFO")
                self.warnings.append(f"Missing recommended '{field}' in {file_path}")
        
        # Validate field types
        if 'name' in info:
            name = info['name']
            if not isinstance(name, str):
                print_error(f"{file_path}: 'name' must be a string")
                self.errors.append(f"Invalid 'name' type in {file_path}")
            else:
                # Track command name
                if name in self.commands:
                    print_error(f"{file_path}: Duplicate command name '{name}' (also in {self.commands[name]})")
                    self.errors.append(f"Duplicate command '{name}'")
                else:
                    self.commands[name] = file_path
        
        if 'aliases' in info:
            aliases = info['aliases']
            if not isinstance(aliases, list):
                print_error(f"{file_path}: 'aliases' must be a list")
                self.errors.append(f"Invalid 'aliases' type in {file_path}")
            else:
                for alias in aliases:
                    if alias in self.aliases:
                        print_error(f"{file_path}: Duplicate alias '{alias}' (also in {self.aliases[alias]})")
                        self.errors.append(f"Duplicate alias '{alias}'")
                    elif alias in self.commands:
                        print_error(f"{file_path}: Alias '{alias}' conflicts with command in {self.commands[alias]}")
                        self.errors.append(f"Conflicting alias '{alias}'")
                    else:
                        self.aliases[alias] = file_path
        
        if 'category' in info:
            category = info['category']
            if isinstance(category, str):
                self.categories[category.upper()].append(info.get('name', 'unknown'))
    
    def check_2_duplicate_commands(self):
        """Check for duplicate or conflicting commands/aliases"""
        print_header("CHECK 2: Duplicate Commands & Aliases")
        
        # Already checked in check_1, just summarize
        total_commands = len(self.commands)
        total_aliases = len(self.aliases)
        
        print_info(f"Total unique commands: {total_commands}")
        print_info(f"Total unique aliases: {total_aliases}")
        
        # Check for aliases that might conflict with command names
        conflicts = set(self.aliases.keys()) & set(self.commands.keys())
        if conflicts:
            print_error(f"Found {len(conflicts)} alias/command conflicts: {conflicts}")
            self.errors.append(f"{len(conflicts)} alias/command conflicts")
        else:
            print_success("No alias/command conflicts found")
        
        # Print categories
        print_info(f"\nCommands by category ({len(self.categories)} categories):")
        for category, cmds in sorted(self.categories.items()):
            print(f"  • {category:15s}: {len(cmds):3d} commands")
    
    def check_3_file_structure(self):
        """Check project file structure"""
        print_header("CHECK 3: File Structure")
        
        required_files = [
            "bot.py",
            "config.py",
            "requirements.txt",
            ".env.example",
            "README.md"
        ]
        
        required_dirs = [
            "handlers",
            "core",
            "middleware",
            "utils"
        ]
        
        # Check required files
        for file_name in required_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                print_success(f"Required file exists: {file_name}")
            else:
                if file_name == ".env.example":
                    print_warning(f"Recommended file missing: {file_name}")
                    self.warnings.append(f"Missing {file_name}")
                else:
                    print_error(f"Required file missing: {file_name}")
                    self.errors.append(f"Missing {file_name}")
        
        # Check required directories
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                py_files = list(dir_path.rglob("*.py"))
                print_success(f"Directory '{dir_name}' exists ({len(py_files)} .py files)")
            else:
                print_error(f"Required directory missing: {dir_name}")
                self.errors.append(f"Missing directory {dir_name}")
    
    def check_4_import_consistency(self):
        """Check import statements consistency"""
        print_header("CHECK 4: Import Consistency")
        
        datetime_issues = []
        deprecated_imports = []
        
        py_files = list(self.project_root.rglob("*.py"))
        py_files = [f for f in py_files if 'venv' not in str(f) and 'ZyraXLegacy' not in str(f)]
        
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                relative_path = py_file.relative_to(self.project_root)
                
                # Check for deprecated datetime usage
                if 'datetime.utcnow()' in content:
                    datetime_issues.append(str(relative_path))
                    print_warning(f"{relative_path}: Uses deprecated datetime.utcnow()")
                
                if re.search(r'datetime\.now\(\s*\)', content):
                    if 'timezone.utc' not in content and 'now_utc()' not in content:
                        datetime_issues.append(str(relative_path))
                        print_warning(f"{relative_path}: Uses datetime.now() without timezone")
                
            except Exception as e:
                pass
        
        if datetime_issues:
            print_warning(f"Found {len(datetime_issues)} files with datetime issues")
            self.warnings.extend(datetime_issues)
        else:
            print_success("All datetime usage is consistent ✓")
    
    def check_5_decorator_usage(self):
        """Check decorator usage in command handlers"""
        print_header("CHECK 5: Decorator Usage")
        
        handler_files = list(self.handlers_dir.rglob("*.py"))
        handler_files = [f for f in handler_files if not f.name.startswith("_")]
        
        issues = []
        
        for py_file in handler_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'COMMAND_INFO' not in content:
                    continue
                
                if 'def handle(' not in content:
                    continue
                
                relative_path = py_file.relative_to(self.project_root)
                
                # Check for @log_command
                if '@log_command' not in content:
                    print_warning(f"{relative_path}: Missing @log_command decorator")
                    self.warnings.append(f"Missing @log_command in {relative_path}")
                
                # Check for permission decorators in admin commands
                if 'category": "admin' in content or 'category": "moderation' in content:
                    if '@require_admin' not in content:
                        print_warning(f"{relative_path}: Admin command without @require_admin")
                        issues.append(str(relative_path))
                
            except Exception:
                pass
        
        if not issues:
            print_success("Decorator usage looks good")
    
    def check_6_datetime_usage(self):
        """Check datetime usage patterns"""
        print_header("CHECK 6: Datetime Usage Patterns")
        
        py_files = list(self.project_root.rglob("*.py"))
        py_files = [f for f in py_files if 'venv' not in str(f) and 'ZyraXLegacy' not in str(f)]
        
        now_utc_files = []
        issue_files = []
        
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                relative_path = py_file.relative_to(self.project_root)
                
                if 'now_utc()' in content:
                    now_utc_files.append(str(relative_path))
                
                # Check for problematic patterns
                if 'datetime.utcnow()' in content:
                    issue_files.append((str(relative_path), 'datetime.utcnow()'))
                if re.search(r'datetime\.now\(\s*\)', content):
                    issue_files.append((str(relative_path), 'datetime.now() without tz'))
                
            except Exception:
                pass
        
        print_info(f"Files using now_utc(): {len(now_utc_files)}")
        
        if issue_files:
            print_error(f"Found {len(issue_files)} files with datetime issues:")
            for file, issue in issue_files[:10]:  # Show first 10
                print(f"  • {file}: {issue}")
            self.errors.extend([f[0] for f in issue_files])
        else:
            print_success("All datetime usage is timezone-aware! ✓")
    
    def check_7_database_operations(self):
        """Check database operation patterns"""
        print_header("CHECK 7: Database Operations")
        
        py_files = list(self.project_root.rglob("*.py"))
        py_files = [f for f in py_files if 'venv' not in str(f) and 'ZyraXLegacy' not in str(f)]
        
        db_files = []
        missing_error_handling = []
        
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'db.' in content or 'database.' in content:
                    relative_path = py_file.relative_to(self.project_root)
                    db_files.append(str(relative_path))
                    
                    # Check for error handling around DB operations
                    if 'await db.' in content or 'await database.' in content:
                        if 'try:' not in content:
                            missing_error_handling.append(str(relative_path))
                
            except Exception:
                pass
        
        print_info(f"Files with database operations: {len(db_files)}")
        
        if missing_error_handling:
            print_warning(f"{len(missing_error_handling)} files might lack DB error handling")
        else:
            print_success("Database operations appear to have error handling")
    
    def check_8_security_issues(self):
        """Check for common security issues"""
        print_header("CHECK 8: Security Checks")
        
        py_files = list(self.project_root.rglob("*.py"))
        py_files = [f for f in py_files if 'venv' not in str(f) and 'ZyraXLegacy' not in str(f)]
        
        issues = []
        
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                relative_path = py_file.relative_to(self.project_root)
                
                # Check for hardcoded credentials
                if re.search(r'password\s*=\s*["\'](?!.*\{.*\}).+["\']', content, re.IGNORECASE):
                    print_warning(f"{relative_path}: Possible hardcoded password")
                    issues.append(str(relative_path))
                
                # Check for SQL injection risks (if any raw SQL)
                if 'execute(' in content and ('SELECT' in content.upper() or 'INSERT' in content.upper()):
                    print_warning(f"{relative_path}: Check for SQL injection risks")
                    issues.append(str(relative_path))
                
                # Check eval/exec usage
                if re.search(r'\beval\s*\(', content) or re.search(r'\bexec\s*\(', content):
                    if 'owner' not in str(relative_path).lower():
                        print_error(f"{relative_path}: Uses eval() or exec() - DANGEROUS!")
                        self.errors.append(f"Dangerous eval/exec in {relative_path}")
                
            except Exception:
                pass
        
        if not issues:
            print_success("No obvious security issues found")
    
    def check_9_code_quality(self):
        """Check code quality metrics"""
        print_header("CHECK 9: Code Quality")
        
        py_files = list(self.project_root.rglob("*.py"))
        py_files = [f for f in py_files if 'venv' not in str(f) and 'ZyraXLegacy' not in str(f)]
        
        total_lines = 0
        large_files = []
        long_functions = []
        
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                total_lines += len(lines)
                relative_path = py_file.relative_to(self.project_root)
                
                # Check file size
                if len(lines) > 500:
                    large_files.append((str(relative_path), len(lines)))
                
                # Parse and check function sizes
                try:
                    tree = ast.parse(''.join(lines))
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            func_length = node.end_lineno - node.lineno
                            if func_length > 100:
                                long_functions.append((str(relative_path), node.name, func_length))
                except:
                    pass
                
            except Exception:
                pass
        
        print_info(f"Total lines of code: {total_lines:,}")
        print_info(f"Total Python files: {len(py_files)}")
        print_info(f"Average lines per file: {total_lines // len(py_files)}")
        
        if large_files:
            print_warning(f"\n{len(large_files)} files over 500 lines:")
            for file, lines in sorted(large_files, key=lambda x: x[1], reverse=True)[:5]:
                print(f"  • {file}: {lines} lines")
        
        if long_functions:
            print_warning(f"\n{len(long_functions)} functions over 100 lines:")
            for file, func, lines in sorted(long_functions, key=lambda x: x[2], reverse=True)[:5]:
                print(f"  • {file}::{func}(): {lines} lines")
    
    def print_summary(self):
        """Print validation summary"""
        print_header("VALIDATION SUMMARY")
        
        print(f"\n{Colors.BOLD}Statistics:{Colors.ENDC}")
        print(f"  • Files checked: {self.files_checked}")
        print(f"  • Commands found: {self.commands_found}")
        print(f"  • Categories: {len(self.categories)}")
        print(f"  • Unique commands: {len(self.commands)}")
        print(f"  • Unique aliases: {len(self.aliases)}")
        
        print(f"\n{Colors.BOLD}Results:{Colors.ENDC}")
        
        if self.errors:
            print_error(f"✗ {len(self.errors)} ERRORS found")
            for error in self.errors[:10]:  # Show first 10
                print(f"    - {error}")
            if len(self.errors) > 10:
                print(f"    ... and {len(self.errors) - 10} more")
        else:
            print_success("✓ No errors found!")
        
        if self.warnings:
            print_warning(f"⚠ {len(self.warnings)} WARNINGS")
            for warning in self.warnings[:10]:  # Show first 10
                print(f"    - {warning}")
            if len(self.warnings) > 10:
                print(f"    ... and {len(self.warnings) - 10} more")
        else:
            print_success("✓ No warnings!")
        
        print(f"\n{Colors.BOLD}Final Grade:{Colors.ENDC}")
        
        if len(self.errors) == 0:
            if len(self.warnings) == 0:
                print(f"{Colors.OKGREEN}{Colors.BOLD}A+ EXCELLENT{Colors.ENDC} - Perfect codebase!")
            elif len(self.warnings) < 5:
                print(f"{Colors.OKGREEN}{Colors.BOLD}A GREAT{Colors.ENDC} - Minor improvements suggested")
            elif len(self.warnings) < 15:
                print(f"{Colors.OKBLUE}{Colors.BOLD}B GOOD{Colors.ENDC} - Some improvements recommended")
            else:
                print(f"{Colors.WARNING}{Colors.BOLD}C OKAY{Colors.ENDC} - Many warnings to address")
        elif len(self.errors) < 5:
            print(f"{Colors.WARNING}{Colors.BOLD}D NEEDS WORK{Colors.ENDC} - Fix critical errors")
        else:
            print(f"{Colors.FAIL}{Colors.BOLD}F FAIL{Colors.ENDC} - Major issues found")
        
        print()


def main():
    """Main entry point"""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print(f"Validating codebase at: {project_root}")
    
    # Create validator
    validator = CodebaseValidator(project_root)
    
    # Run validation
    success = validator.run_all_checks()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

