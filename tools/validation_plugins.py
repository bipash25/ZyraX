"""
Validation plugins for specific checks
Each plugin focuses on a specific aspect of code quality
"""
import re
from pathlib import Path
from typing import List
from tools.validation_core import (
    ValidationPlugin, ValidationIssue, Severity, EnhancedASTVisitor, analyze_file
)


class TelegramAPIPlugin(ValidationPlugin):
    """Validates Telegram Bot API usage"""
    
    @property
    def name(self) -> str:
        return "Telegram API Validation"
    
    def validate(self, file_path: Path, content: str, ast_tree) -> List[ValidationIssue]:
        issues = []
        
        # Check message length limits
        if "send_message" in content or "edit_message" in content:
            # Look for potential long messages
            if len(content) > 10000:  # Heuristic
                issues.append(ValidationIssue(
                    severity=Severity.INFO,
                    category="telegram_api",
                    message="File contains message sending - ensure message length limits (4096 chars)",
                    file_path=file_path,
                    fix_suggestion="Add message length validation before sending"
                ))
        
        # Check callback_data length (max 64 bytes)
        callback_pattern = r'callback_data\s*=\s*["\']([^"\']{65,})["\']'
        for match in re.finditer(callback_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                category="telegram_api",
                message=f"callback_data exceeds 64 byte limit: {len(match.group(1))} bytes",
                file_path=file_path,
                line_number=line_num,
                fix_suggestion="Use shorter callback_data or implement a lookup system"
            ))
        
        # Check for deprecated API methods
        deprecated_methods = {
            'getChatMembersCount': 'Use get_chat_member_count instead',
            'kickChatMember': 'Use ban_chat_member instead',
        }
        
        for old_method, suggestion in deprecated_methods.items():
            if old_method in content:
                line_num = content.find(old_method)
                line_num = content[:line_num].count('\n') + 1
                issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    category="telegram_api",
                    message=f"Deprecated method '{old_method}' found",
                    file_path=file_path,
                    line_number=line_num,
                    fix_suggestion=suggestion
                ))
        
        # Check for proper API error handling
        if any(api_call in content for api_call in ['send_message', 'edit_message', 'delete_message']):
            if 'TelegramError' not in content and 'telegram.error' not in content:
                issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    category="telegram_api",
                    message="Telegram API calls found but no TelegramError handling detected",
                    file_path=file_path,
                    fix_suggestion="Add try-except blocks for telegram.error.TelegramError"
                ))
        
        return issues


class SecurityPlugin(ValidationPlugin):
    """Validates security-related issues"""
    
    @property
    def name(self) -> str:
        return "Security Validation"
    
    def validate(self, file_path: Path, content: str, ast_tree) -> List[ValidationIssue]:
        issues = []
        
        # Check for hardcoded tokens
        token_patterns = [
            (r'["\'](\d{10}:[A-Za-z0-9_-]{35})["\']', 'Potential hardcoded bot token'),
            (r'TOKEN\s*=\s*["\']([^"\']+)["\']', 'Hardcoded TOKEN variable'),
            (r'API_KEY\s*=\s*["\']([^"\']+)["\']', 'Hardcoded API_KEY variable'),
        ]
        
        for pattern, message in token_patterns:
            for match in re.finditer(pattern, content):
                if 'example' not in match.group(0).lower() and 'your_' not in match.group(0).lower():
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append(ValidationIssue(
                        severity=Severity.CRITICAL,
                        category="security",
                        message=message,
                        file_path=file_path,
                        line_number=line_num,
                        fix_suggestion="Move sensitive data to environment variables or config files"
                    ))
        
        # Check for eval/exec usage
        dangerous_funcs = ['eval(', 'exec(', '__import__(']
        for func in dangerous_funcs:
            if func in content:
                line_num = content.find(func)
                line_num = content[:line_num].count('\n') + 1
                issues.append(ValidationIssue(
                    severity=Severity.CRITICAL,
                    category="security",
                    message=f"Dangerous function {func.rstrip('(')} detected",
                    file_path=file_path,
                    line_number=line_num,
                    fix_suggestion="Avoid using eval/exec - use safer alternatives"
                ))
        
        # Check for command injection vulnerabilities
        if 'subprocess' in content or 'os.system' in content:
            if 'shell=True' in content:
                line_num = content.find('shell=True')
                line_num = content[:line_num].count('\n') + 1
                issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    category="security",
                    message="subprocess with shell=True can lead to command injection",
                    file_path=file_path,
                    line_number=line_num,
                    fix_suggestion="Use shell=False and pass command as a list"
                ))
        
        # Check for SQL injection (basic)
        sql_patterns = [
            r'\.execute\(["\'].*%s.*["\'].*%',
            r'\.execute\(f["\'].*\{.*\}.*["\']',
            r'["\']SELECT.*\+.*["\']',
        ]
        
        for pattern in sql_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    category="security",
                    message="Potential SQL injection vulnerability",
                    file_path=file_path,
                    line_number=line_num,
                    fix_suggestion="Use parameterized queries instead of string formatting"
                ))
        
        # Check for unsafe pickle/yaml usage
        if 'pickle.loads' in content or 'yaml.load(' in content:
            line_num = content.find('pickle.loads' if 'pickle.loads' in content else 'yaml.load(')
            line_num = content[:line_num].count('\n') + 1
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                category="security",
                message="Unsafe deserialization detected",
                file_path=file_path,
                line_number=line_num,
                fix_suggestion="Use safe_load for YAML or verify pickle source"
            ))
        
        return issues


class DatetimePlugin(ValidationPlugin):
    """Validates datetime usage patterns"""
    
    @property
    def name(self) -> str:
        return "Datetime Validation"
    
    def validate(self, file_path: Path, content: str, ast_tree) -> List[ValidationIssue]:
        issues = []
        
        # Analyze with enhanced visitor if AST available
        if ast_tree:
            _, visitor, _ = analyze_file(file_path)
            if visitor and visitor.datetime_calls:
                for line, col, call_name in visitor.datetime_calls:
                    if 'utcnow' in call_name.lower():
                        issues.append(ValidationIssue(
                            severity=Severity.WARNING,
                            category="datetime",
                            message=f"Deprecated datetime.utcnow() usage",
                            file_path=file_path,
                            line_number=line,
                            fix_suggestion="Replace with now_utc() from utils.time_parser"
                        ))
                    elif 'datetime.now()' in call_name and 'timezone' not in content:
                        issues.append(ValidationIssue(
                            severity=Severity.WARNING,
                            category="datetime",
                            message=f"datetime.now() without timezone awareness",
                            file_path=file_path,
                            line_number=line,
                            fix_suggestion="Use now_utc() or datetime.now(timezone.utc)"
                        ))
        
        return issues


class DecoratorPlugin(ValidationPlugin):
    """Validates decorator usage on command handlers"""
    
    @property
    def name(self) -> str:
        return "Decorator Validation"
    
    def validate(self, file_path: Path, content: str, ast_tree) -> List[ValidationIssue]:
        issues = []
        
        if not ast_tree:
            return issues
        
        _, visitor, _ = analyze_file(file_path)
        if not visitor or not visitor.command_info:
            return issues
        
        # Check if handle function exists
        if not visitor.handle_function:
            return issues
        
        command_category = visitor.command_info.get('category', '').lower()
        decorators = visitor.decorators
        
        # Categories that should have @require_admin
        admin_categories = ['admin', 'moderation', 'federation']
        if command_category in admin_categories and 'require_admin' not in decorators:
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                category="decorators",
                message=f"Admin command in '{command_category}' category without @require_admin",
                file_path=file_path,
                line_number=visitor.handle_function.lineno,
                fix_suggestion=f"Add @require_admin decorator to handle function"
            ))
        
        # Categories that should have @log_command
        log_categories = ['moderation', 'admin', 'federation', 'warnings', 'antiraid', 'antiflood']
        if command_category in log_categories and 'log_command' not in decorators:
            issues.append(ValidationIssue(
                severity=Severity.INFO,
                category="decorators",
                message=f"Command in '{command_category}' category without @log_command",
                file_path=file_path,
                line_number=visitor.handle_function.lineno,
                fix_suggestion="Consider adding @log_command for better audit trails"
            ))
        
        # Check decorator order (log_command should be first)
        if 'log_command' in decorators and decorators[0] != 'log_command':
            issues.append(ValidationIssue(
                severity=Severity.INFO,
                category="decorators",
                message="@log_command should be the first (outermost) decorator",
                file_path=file_path,
                line_number=visitor.handle_function.lineno,
                fix_suggestion="Move @log_command to the top of the decorator stack"
            ))
        
        return issues


class AsyncAwaitPlugin(ValidationPlugin):
    """Validates async/await patterns"""
    
    @property
    def name(self) -> str:
        return "Async/Await Validation"
    
    def validate(self, file_path: Path, content: str, ast_tree) -> List[ValidationIssue]:
        issues = []
        
        if not ast_tree:
            return issues
        
        _, visitor, _ = analyze_file(file_path)
        if not visitor:
            return issues
        
        # Check for blocking I/O in async functions
        blocking_io_patterns = [
            ('open(', 'Use aiofiles for async file operations'),
            ('requests.', 'Use aiohttp for async HTTP requests'),
            ('time.sleep(', 'Use asyncio.sleep() instead'),
        ]
        
        for async_func in visitor.async_functions:
            func_start = async_func.lineno
            func_end = async_func.end_lineno or func_start
            func_content = '\n'.join(content.split('\n')[func_start-1:func_end])
            
            for pattern, suggestion in blocking_io_patterns:
                if pattern in func_content:
                    issues.append(ValidationIssue(
                        severity=Severity.WARNING,
                        category="async_await",
                        message=f"Potential blocking I/O in async function: {pattern.rstrip('(')}",
                        file_path=file_path,
                        line_number=func_start,
                        fix_suggestion=suggestion
                    ))
        
        return issues


class CommandStructurePlugin(ValidationPlugin):
    """Validates command structure and COMMAND_INFO"""
    
    @property
    def name(self) -> str:
        return "Command Structure Validation"
    
    def validate(self, file_path: Path, content: str, ast_tree) -> List[ValidationIssue]:
        issues = []
        
        if not ast_tree:
            return issues
        
        _, visitor, _ = analyze_file(file_path)
        if not visitor:
            return issues
        
        # Check if file has COMMAND_INFO
        if visitor.command_info:
            # Check required fields
            required_fields = self.config.get('required_fields', [])
            for field in required_fields:
                if field not in visitor.command_info:
                    issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        category="command_structure",
                        message=f"Missing required field '{field}' in COMMAND_INFO",
                        file_path=file_path,
                        fix_suggestion=f"Add '{field}' field to COMMAND_INFO dictionary"
                    ))
            
            # Check recommended fields
            recommended_fields = self.config.get('recommended_fields', [])
            for field in recommended_fields:
                if field not in visitor.command_info:
                    issues.append(ValidationIssue(
                        severity=Severity.INFO,
                        category="command_structure",
                        message=f"Missing recommended field '{field}' in COMMAND_INFO",
                        file_path=file_path,
                        fix_suggestion=f"Consider adding '{field}' field to COMMAND_INFO"
                    ))
            
            # Check if handle function exists
            if not visitor.handle_function:
                issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    category="command_structure",
                    message="Has COMMAND_INFO but no handle() function",
                    file_path=file_path,
                    fix_suggestion="Add a handle() or async handle() function"
                ))
        
        return issues


class DatabasePlugin(ValidationPlugin):
    """Validates database operation patterns"""
    
    @property
    def name(self) -> str:
        return "Database Validation"
    
    def validate(self, file_path: Path, content: str, ast_tree) -> List[ValidationIssue]:
        issues = []
        
        if not ast_tree:
            return issues
        
        _, visitor, _ = analyze_file(file_path)
        if not visitor or not visitor.database_operations:
            return issues
        
        # Check for error handling around DB operations
        has_try_except = 'try:' in content and 'except' in content
        
        if not has_try_except and len(visitor.database_operations) > 0:
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                category="database",
                message="Database operations without try-except error handling",
                file_path=file_path,
                fix_suggestion="Wrap database operations in try-except blocks"
            ))
        
        # Check for potential N+1 queries (DB operations in loops)
        if 'for ' in content or 'while ' in content:
            for line, col, call in visitor.database_operations:
                context_start = max(0, line - 5)
                context_end = min(len(content.split('\n')), line + 5)
                context = '\n'.join(content.split('\n')[context_start:context_end])
                
                if 'for ' in context or 'while ' in context:
                    issues.append(ValidationIssue(
                        severity=Severity.WARNING,
                        category="database",
                        message="Potential N+1 query: DB operation inside loop",
                        file_path=file_path,
                        line_number=line,
                        fix_suggestion="Consider using bulk operations or aggregation"
                    ))
        
        return issues

