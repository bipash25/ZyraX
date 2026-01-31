#!/usr/bin/env python3
"""
Documentation Validation Tool
Checks for docstrings, comments, and documentation completeness
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


class DocstringVisitor(ast.NodeVisitor):
    """AST visitor to check docstrings"""
    
    def __init__(self):
        self.functions = []
        self.classes = []
        self.functions_without_docstring = []
        self.classes_without_docstring = []
        self.module_docstring = None
        
    def visit_Module(self, node):
        self.module_docstring = ast.get_docstring(node)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        self.functions.append(node.name)
        docstring = ast.get_docstring(node)
        if not docstring and not node.name.startswith('_'):
            self.functions_without_docstring.append(node.name)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        self.functions.append(node.name)
        docstring = ast.get_docstring(node)
        if not docstring and not node.name.startswith('_'):
            self.functions_without_docstring.append(node.name)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        self.classes.append(node.name)
        docstring = ast.get_docstring(node)
        if not docstring and not node.name.startswith('_'):
            self.classes_without_docstring.append(node.name)
        self.generic_visit(node)


def check_documentation(project_root: Path) -> tuple:
    """
    Check documentation completeness
    
    Returns:
        Tuple of (warnings list, stats dict)
    """
    warnings = []
    
    files_without_module_docstring = []
    total_functions = 0
    functions_without_docstring = 0
    total_classes = 0
    classes_without_docstring = 0
    
    # Find all Python files
    py_files = list(project_root.rglob("*.py"))
    py_files = [f for f in py_files if 'venv' not in str(f) and '__pycache__' not in str(f)]
    
    print_info(f"Scanning {len(py_files)} Python files for documentation...")
    
    for py_file in py_files:
        relative_path = py_file.relative_to(project_root)
        
        # Skip __init__.py files
        if py_file.name == '__init__.py':
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            
            visitor = DocstringVisitor()
            visitor.visit(tree)
            
            # Check module docstring (especially for important files)
            if 'handlers/' in str(relative_path) or 'core/' in str(relative_path):
                if not visitor.module_docstring:
                    files_without_module_docstring.append(str(relative_path))
                    print_warning(f"{relative_path}: Missing module docstring")
                    warnings.append(f"Missing module docstring in {relative_path}")
            
            # Count functions and classes
            total_functions += len(visitor.functions)
            functions_without_docstring += len(visitor.functions_without_docstring)
            total_classes += len(visitor.classes)
            classes_without_docstring += len(visitor.classes_without_docstring)
            
            # Warn about specific files
            if visitor.functions_without_docstring and 'handlers/' in str(relative_path):
                if len(visitor.functions_without_docstring) > 0:
                    print_info(
                        f"{relative_path}: {len(visitor.functions_without_docstring)} "
                        f"functions without docstrings"
                    )
        
        except Exception:
            pass
    
    # Calculate percentages
    func_doc_percentage = (
        ((total_functions - functions_without_docstring) / total_functions * 100)
        if total_functions > 0 else 100
    )
    class_doc_percentage = (
        ((total_classes - classes_without_docstring) / total_classes * 100)
        if total_classes > 0 else 100
    )
    
    stats = {
        'total_files': len(py_files),
        'files_without_module_docstring': len(files_without_module_docstring),
        'total_functions': total_functions,
        'functions_without_docstring': functions_without_docstring,
        'func_doc_percentage': func_doc_percentage,
        'total_classes': total_classes,
        'classes_without_docstring': classes_without_docstring,
        'class_doc_percentage': class_doc_percentage
    }
    
    return warnings, stats


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("DOCUMENTATION VALIDATION".center(80))
    print("="*80 + "\n")
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run check
    warnings, stats = check_documentation(project_root)
    
    # Print summary
    print("\n" + "="*80)
    print("RESULTS".center(80))
    print("="*80 + "\n")
    
    print_info(f"Total files scanned: {stats['total_files']}")
    print_info(f"Files without module docstring: {stats['files_without_module_docstring']}")
    
    print(f"\n📝 Function Documentation:")
    print(f"  • Total functions: {stats['total_functions']}")
    print(f"  • Without docstrings: {stats['functions_without_docstring']}")
    print(f"  • Documentation coverage: {stats['func_doc_percentage']:.1f}%")
    
    print(f"\n📚 Class Documentation:")
    print(f"  • Total classes: {stats['total_classes']}")
    print(f"  • Without docstrings: {stats['classes_without_docstring']}")
    print(f"  • Documentation coverage: {stats['class_doc_percentage']:.1f}%")
    
    if stats['func_doc_percentage'] >= 80:
        print_success("\n✓ Good documentation coverage!")
    elif stats['func_doc_percentage'] >= 60:
        print_warning("\n⚠ Documentation coverage could be improved")
    else:
        print_warning("\n⚠ Low documentation coverage")
    
    if warnings:
        print_warning(f"\n{len(warnings)} documentation warnings")
    
    print("\n💡 Documentation Tips:")
    print("  • Add module docstrings at the top of files")
    print("  • Document all public functions and classes")
    print("  • Use clear, concise descriptions")
    print("  • Include parameter and return type information")
    
    print()
    
    # Exit with appropriate code (warnings don't cause failure)
    sys.exit(0)


if __name__ == "__main__":
    main()
