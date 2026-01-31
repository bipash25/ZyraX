"""
Core validation classes and utilities
Provides structured validation results, plugin architecture, and enhanced AST analysis
"""
import ast
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a single validation issue"""
    severity: Severity
    category: str
    message: str
    file_path: Path
    line_number: Optional[int] = None
    column: Optional[int] = None
    context: Optional[str] = None
    fix_suggestion: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __str__(self):
        location = f"{self.file_path}"
        if self.line_number:
            location += f":{self.line_number}"
            if self.column:
                location += f":{self.column}"
        
        msg = f"[{self.severity.value.upper()}] {location} - {self.message}"
        if self.fix_suggestion:
            msg += f"\n  💡 Suggestion: {self.fix_suggestion}"
        return msg
    
    def to_dict(self):
        """Convert to dictionary for JSON export"""
        return {
            "severity": self.severity.value,
            "category": self.category,
            "message": self.message,
            "file": str(self.file_path),
            "line": self.line_number,
            "column": self.column,
            "context": self.context,
            "fix_suggestion": self.fix_suggestion,
            "timestamp": self.timestamp.isoformat()
        }


class ValidationResult:
    """Aggregates validation issues and provides reporting"""
    
    def __init__(self):
        self.issues: List[ValidationIssue] = []
        self.stats = {
            "files_checked": 0,
            "commands_found": 0,
            "start_time": datetime.now(timezone.utc),
            "end_time": None
        }
    
    def add_issue(self, issue: ValidationIssue):
        """Add a validation issue"""
        self.issues.append(issue)
    
    def add(self, severity: Severity, category: str, message: str, 
            file_path: Path, line_number: Optional[int] = None,
            fix_suggestion: Optional[str] = None):
        """Convenience method to add an issue"""
        issue = ValidationIssue(
            severity=severity,
            category=category,
            message=message,
            file_path=file_path,
            line_number=line_number,
            fix_suggestion=fix_suggestion
        )
        self.add_issue(issue)
    
    def get_by_severity(self, severity: Severity) -> List[ValidationIssue]:
        """Get all issues of a specific severity"""
        return [i for i in self.issues if i.severity == severity]
    
    def get_by_category(self, category: str) -> List[ValidationIssue]:
        """Get all issues in a specific category"""
        return [i for i in self.issues if i.category == category]
    
    def count_by_severity(self) -> Dict[Severity, int]:
        """Count issues by severity"""
        counts = defaultdict(int)
        for issue in self.issues:
            counts[issue.severity] += 1
        return dict(counts)
    
    def has_errors(self) -> bool:
        """Check if there are any errors or critical issues"""
        return any(i.severity in [Severity.ERROR, Severity.CRITICAL] for i in self.issues)
    
    def to_json(self, indent: int = 2) -> str:
        """Export results as JSON"""
        data = {
            "summary": {
                "total_issues": len(self.issues),
                "by_severity": {s.value: len(self.get_by_severity(s)) for s in Severity},
                "stats": self.stats
            },
            "issues": [issue.to_dict() for issue in self.issues]
        }
        return json.dumps(data, indent=indent)
    
    def finalize(self):
        """Mark validation as complete"""
        self.stats["end_time"] = datetime.now(timezone.utc)
        self.stats["duration_seconds"] = (
            self.stats["end_time"] - self.stats["start_time"]
        ).total_seconds()


class ValidationPlugin(ABC):
    """Base class for validation plugins"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get("enabled", True)
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name"""
        pass
    
    @abstractmethod
    def validate(self, file_path: Path, content: str, 
                 ast_tree: Optional[ast.AST]) -> List[ValidationIssue]:
        """
        Validate a file and return issues
        
        Args:
            file_path: Path to the file being validated
            content: File content as string
            ast_tree: Parsed AST tree (may be None if parsing failed)
        
        Returns:
            List of validation issues found
        """
        pass


class EnhancedASTVisitor(ast.NodeVisitor):
    """Enhanced AST visitor for extracting detailed information"""
    
    def __init__(self):
        self.command_info: Optional[Dict[str, Any]] = None
        self.handle_function: Optional[ast.FunctionDef] = None
        self.decorators: List[str] = []
        self.imports: Set[str] = []
        self.function_defs: List[ast.FunctionDef] = []
        self.async_functions: List[ast.AsyncFunctionDef] = []
        self.datetime_calls: List[tuple] = []  # (line, col, call_name)
        self.database_operations: List[tuple] = []
        self.api_calls: List[tuple] = []
    
    def visit_Import(self, node):
        """Track imports"""
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Track from imports"""
        if node.module:
            for alias in node.names:
                self.imports.add(f"{node.module}.{alias.name}")
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """Extract COMMAND_INFO dictionary"""
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "COMMAND_INFO":
                self.command_info = self._extract_dict_value(node.value)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """Track function definitions and handle function"""
        self.function_defs.append(node)
        if node.name == "handle":
            self.handle_function = node
            self.decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        """Track async function definitions"""
        self.async_functions.append(node)
        if node.name == "handle":
            self.handle_function = node
            self.decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Track function calls for datetime, DB operations, etc."""
        call_name = self._get_call_name(node)
        
        # Track datetime calls
        if 'datetime' in call_name or 'utcnow' in call_name:
            self.datetime_calls.append((node.lineno, node.col_offset, call_name))
        
        # Track database operations
        if any(db in call_name for db in ['find_one', 'insert_one', 'update_one', 'delete_one']):
            self.database_operations.append((node.lineno, node.col_offset, call_name))
        
        # Track Telegram API calls
        if any(api in call_name for api in ['send_message', 'edit_message', 'delete_message']):
            self.api_calls.append((node.lineno, node.col_offset, call_name))
        
        self.generic_visit(node)
    
    def _get_decorator_name(self, decorator) -> str:
        """Extract decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        return "unknown"
    
    def _get_call_name(self, node: ast.Call) -> str:
        """Extract the full name of a function call"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            # Build full attribute path (e.g., datetime.utcnow)
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts))
        return "unknown"
    
    def _extract_dict_value(self, node) -> Optional[Dict[str, Any]]:
        """Extract dictionary value from AST node"""
        if not isinstance(node, ast.Dict):
            return None
        
        result = {}
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Constant):
                key_name = key.value
                result[key_name] = self._extract_value(value)
        return result
    
    def _extract_value(self, node) -> Any:
        """Extract value from AST node"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.List):
            return [self._extract_value(elt) for elt in node.elts]
        elif isinstance(node, ast.Dict):
            return self._extract_dict_value(node)
        elif isinstance(node, ast.Name):
            return f"<variable:{node.id}>"
        elif isinstance(node, (ast.JoinedStr, ast.FormattedValue)):
            return "<f-string>"
        else:
            return f"<{type(node).__name__}>"


def parse_file_safe(file_path: Path) -> tuple[Optional[str], Optional[ast.AST], Optional[str]]:
    """
    Safely parse a Python file
    
    Returns:
        Tuple of (content, ast_tree, error_message)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content, filename=str(file_path))
            return content, tree, None
        except SyntaxError as e:
            return content, None, f"Syntax error: {e}"
    
    except Exception as e:
        return None, None, f"Failed to read file: {e}"


def analyze_file(file_path: Path) -> tuple[Optional[str], Optional[EnhancedASTVisitor], Optional[str]]:
    """
    Analyze a Python file and extract information
    
    Returns:
        Tuple of (content, visitor, error_message)
    """
    content, tree, error = parse_file_safe(file_path)
    
    if error:
        return content, None, error
    
    if tree is None:
        return content, None, "No AST tree available"
    
    visitor = EnhancedASTVisitor()
    try:
        visitor.visit(tree)
        return content, visitor, None
    except Exception as e:
        return content, None, f"AST analysis failed: {e}"

