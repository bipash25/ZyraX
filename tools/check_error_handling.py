#!/usr/bin/env python3
"""
Error Handling Validation Tool
Checks for proper error handling patterns and exception management
"""

import sys
import ast
from pathlib import Path


def print_success(text):
    print(f"\033[92m✓ {text}\033[0m")


def print_warning(text):
    print(f"\033[93m⚠ {text}\033[0m")


def print_error(text):
    print(f"\033[91m✗ {text}\033[0m")


def print_info(text):
    print(f"\033[96mℹ {text}\033[0m")


class ErrorHandlingVisitor(ast.NodeVisitor):
    """AST visitor to analyze error handling"""
    
    def __init__(self):
        self.try_blocks = []
        self.bare_except = []
        self.generic_except = []
        self.has_logging = False
        self.async_functions = []
        
    def visit_Try(self, node):
        self.try_blocks.append(node)
        
        for handler in node.handlers:
            # Check for bare except
            if handler.type is None:
                self.bare_except.append((node.lineno, "Bare except clause"))
            # Check for too generic except
            elif isinstance(handler.type, ast.Name) and handler.type.id == 'Exception':
                self.generic_except.append((node.lineno, "Generic Exception catch"))
        
        self.generic_visit(node)
    
    def visit_Import(self, node):
        for alias in node.names:
            if alias.name == 'logging':
                self.has_logging = True
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if node.module == 'logging':
            self.has_logging = True
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        self.async_functions.append(node)
        self.generic_visit(node)


def check_error_handling(project_root: Path) -> tuple:
    """
    Check error handling patterns
    
    Returns:
        Tuple of (errors list, warnings list, stats dict)
    """
    errors = []
    warnings = []
    
    files_without_logging = []
    files_with_bare_except = []
    files_with_generic_except = []
    async_without_try_except = []
    missing_user_friendly_errors = []
    
    # Find all Python files
    py_files = list(project_root.rglob("*.py"))
    py_files = [f for f in py_files if 'venv' not in str(f) and '__pycache__' not in str(f)]
    
    print_info(f"Scanning {len(py_files)} Python files for error handling...")
    
    for py_file in py_files:
        relative_path = py_file.relative_to(project_root)
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip if no function definitions
            if 'def ' not in content:
                continue
            
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            
            visitor = ErrorHandlingVisitor()
            visitor.visit(tree)
            
            # Check for logging import in handlers
            if 'handlers/' in str(relative_path) and not visitor.has_logging:
                files_without_logging.append(str(relative_path))
                print_warning(f"{relative_path}: No logging import in handler")
            
            # Check for bare except
            if visitor.bare_except:
                files_with_bare_except.append((str(relative_path), len(visitor.bare_except)))
                print_error(f"{relative_path}: {len(visitor.bare_except)} bare except clause(s)")
                errors.append(f"Bare except in {relative_path}")
            
            # Check for generic Exception catch
            if visitor.generic_except:
                files_with_generic_except.append((str(relative_path), len(visitor.generic_except)))
                print_warning(f"{relative_path}: {len(visitor.generic_except)} generic Exception catch(es)")
                warnings.append(f"Generic Exception in {relative_path}")
            
            # Check async functions have error handling
            if visitor.async_functions:
                for async_func in visitor.async_functions:
                    # Check if function body has try-except
                    has_try = any(isinstance(node, ast.Try) for node in ast.walk(async_func))
                    if not has_try and len(async_func.body) > 5:  # Ignore trivial functions
                        async_without_try_except.append((str(relative_path), async_func.name))
            
            # Check for user-friendly error messages in handlers
            if 'handlers/' in str(relative_path):
                if 'reply_text' in content or 'reply_html' in content:
                    # Check if there are generic "Error" messages
                    if '"Error"' in content or "'Error'" in content:
                        if '❌' not in content:
                            missing_user_friendly_errors.append(str(relative_path))
        
        except Exception:
            pass
    
    stats = {
        'total_files': len(py_files),
        'files_without_logging': len(files_without_logging),
        'files_with_bare_except': len(files_with_bare_except),
        'files_with_generic_except': len(files_with_generic_except),
        'async_without_try_except': len(async_without_try_except),
        'missing_user_friendly_errors': len(missing_user_friendly_errors)
    }
    
    return errors, warnings, stats


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("ERROR HANDLING VALIDATION".center(80))
    print("="*80 + "\n")
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run check
    errors, warnings, stats = check_error_handling(project_root)
    
    # Print summary
    print("\n" + "="*80)
    print("RESULTS".center(80))
    print("="*80 + "\n")
    
    print_info(f"Total files scanned: {stats['total_files']}")
    print_info(f"Handler files without logging: {stats['files_without_logging']}")
    print_info(f"Files with bare except: {stats['files_with_bare_except']}")
    print_info(f"Files with generic Exception: {stats['files_with_generic_except']}")
    print_info(f"Async functions without try-except: {stats['async_without_try_except']}")
    
    if errors:
        print_error(f"\n{len(errors)} CRITICAL ERRORS found:")
        for error in errors[:10]:
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
        print("\n💡 Best Practices:")
        print("  • Avoid bare 'except:' - catch specific exceptions")
        print("  • Don't catch generic Exception unless logging it")
        print("  • Always log errors with context")
        print("  • Provide user-friendly error messages")
    else:
        print_success("\n✓ Error handling looks good!")
    
    if warnings:
        print_warning(f"\n{len(warnings)} WARNINGS")
    
    print()
    
    # Exit with appropriate code
    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
