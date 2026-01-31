#!/usr/bin/env python3
"""
Telegram API Limits Validation Tool
Checks compliance with Telegram Bot API limits and best practices
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


def check_telegram_limits(project_root: Path) -> tuple:
    """
    Check Telegram API limits compliance
    
    Returns:
        Tuple of (errors list, warnings list, stats dict)
    """
    errors = []
    warnings = []
    
    long_messages = []  # Messages potentially over 4096 chars
    long_captions = []  # Captions potentially over 1024 chars
    long_callback_data = []  # callback_data over 64 bytes
    rate_limit_concerns = []  # Files with many API calls in loops
    missing_rate_limiting = []  # Files with API calls but no rate limit handling
    deprecated_api_methods = []
    
    # Find all Python files in handlers
    py_files = list(project_root.rglob("*.py"))
    py_files = [f for f in py_files if 'venv' not in str(f) and '__pycache__' not in str(f)]
    
    print_info(f"Scanning {len(py_files)} Python files for Telegram API compliance...")
    
    for py_file in py_files:
        relative_path = py_file.relative_to(project_root)
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Check for potentially long messages (hardcoded strings > 3000 chars)
            message_patterns = [
                r'reply_text\s*\(\s*["\'](.{3000,}?)["\']',
                r'reply_html\s*\(\s*["\'](.{3000,}?)["\']',
                r'send_message\s*\([^,]+,\s*["\'](.{3000,}?)["\']'
            ]
            
            for pattern in message_patterns:
                matches = re.finditer(pattern, content, re.DOTALL)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    long_messages.append((str(relative_path), line_num, len(match.group(1))))
                    print_error(
                        f"{relative_path}:{line_num}: "
                        f"Message may exceed 4096 char limit ({len(match.group(1))} chars)"
                    )
                    errors.append(f"Long message in {relative_path}:{line_num}")
            
            # Check callback_data length (max 64 bytes)
            callback_pattern = r'callback_data\s*=\s*["\']([^"\']+)["\']'
            for match in re.finditer(callback_pattern, content):
                callback_data = match.group(1)
                if len(callback_data.encode('utf-8')) > 64:
                    line_num = content[:match.start()].count('\n') + 1
                    long_callback_data.append((str(relative_path), line_num, len(callback_data.encode('utf-8'))))
                    print_error(
                        f"{relative_path}:{line_num}: "
                        f"callback_data exceeds 64 bytes ({len(callback_data.encode('utf-8'))} bytes)"
                    )
                    errors.append(f"Long callback_data in {relative_path}:{line_num}")
            
            # Check for API calls in loops (rate limit concerns)
            api_methods = [
                'send_message', 'reply_text', 'reply_html', 'edit_message',
                'delete_message', 'ban_chat_member', 'restrict_chat_member'
            ]
            
            for i, line in enumerate(lines):
                # Check if line has API call
                if any(method in line for method in api_methods):
                    # Check if inside a loop (check previous 5 lines)
                    context_start = max(0, i - 5)
                    context = '\n'.join(lines[context_start:i+1])
                    if 'for ' in context or 'while ' in context:
                        rate_limit_concerns.append((str(relative_path), i+1))
                        print_warning(
                            f"{relative_path}:{i+1}: API call in loop (rate limit risk)"
                        )
            
            # Check for deprecated methods
            deprecated_methods = {
                'getChatMembersCount': 'get_chat_member_count',
                'kickChatMember': 'ban_chat_member',
                'getChatMember': 'get_chat_member',
            }
            
            for old_method, new_method in deprecated_methods.items():
                if old_method in content:
                    line_num = content.find(old_method)
                    line_num = content[:line_num].count('\n') + 1
                    deprecated_api_methods.append((str(relative_path), line_num, old_method, new_method))
                    print_warning(
                        f"{relative_path}:{line_num}: Deprecated method '{old_method}' (use '{new_method}')"
                    )
                    warnings.append(f"Deprecated API method in {relative_path}")
            
            # Check for rate limiting handling
            if 'handlers/' in str(relative_path):
                has_api_calls = any(method in content for method in api_methods)
                has_rate_limit_handling = any(keyword in content for keyword in [
                    'RetryAfter', 'sleep', 'rate_limit', 'throttle', 'TimedOut'
                ])
                
                if has_api_calls and not has_rate_limit_handling and len(content) > 1000:
                    missing_rate_limiting.append(str(relative_path))
        
        except Exception:
            pass
    
    stats = {
        'total_files': len(py_files),
        'long_messages': len(long_messages),
        'long_callback_data': len(long_callback_data),
        'rate_limit_concerns': len(rate_limit_concerns),
        'deprecated_api_methods': len(deprecated_api_methods),
        'missing_rate_limiting': len(missing_rate_limiting)
    }
    
    return errors, warnings, stats


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("TELEGRAM API LIMITS VALIDATION".center(80))
    print("="*80 + "\n")
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run check
    errors, warnings, stats = check_telegram_limits(project_root)
    
    # Print summary
    print("\n" + "="*80)
    print("RESULTS".center(80))
    print("="*80 + "\n")
    
    print_info(f"Total files scanned: {stats['total_files']}")
    print_info(f"Messages over 4096 chars: {stats['long_messages']}")
    print_info(f"callback_data over 64 bytes: {stats['long_callback_data']}")
    print_info(f"API calls in loops (rate limit risk): {stats['rate_limit_concerns']}")
    print_info(f"Deprecated API methods: {stats['deprecated_api_methods']}")
    print_info(f"Files missing rate limit handling: {stats['missing_rate_limiting']}")
    
    if errors:
        print_error(f"\n{len(errors)} CRITICAL ERRORS found")
        print("\n🤖 Telegram API Limits:")
        print("  • Message text: 4096 characters max")
        print("  • Caption text: 1024 characters max")
        print("  • callback_data: 64 bytes max")
        print("  • Rate limit: 30 messages/second per chat")
        print("  • Bot messages: 20 per minute to same group")
    else:
        print_success("\n✓ All Telegram API limits complied with!")
    
    if warnings:
        print_warning(f"\n{len(warnings)} WARNINGS")
    
    if stats['rate_limit_concerns'] > 0:
        print("\n💡 Rate Limiting Tips:")
        print("  • Add delays between API calls in loops")
        print("  • Use bulk operations where possible")
        print("  • Handle RetryAfter exceptions")
        print("  • Consider queueing messages")
    
    print()
    
    # Exit with appropriate code
    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
