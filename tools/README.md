# ZyraX Development Tools

This directory contains development and maintenance tools for the ZyraX bot.

---

## 🔍 Validation Tools

### Comprehensive Validation: `validate_codebase.py`

Comprehensive codebase validation script that runs all checks and provides a grading system.

#### Usage

```bash
# From project root
python tools/validate_codebase.py

# Or from tools directory
cd tools
python validate_codebase.py
```

### Individual Validation Tools

Each validation check has been separated into its own standalone tool for targeted analysis:

#### 1. **`check_command_structure.py`** - Command Structure Validation
- Validates all `COMMAND_INFO` dictionaries
- Checks for required fields: `name`, `description`, `category`
- Verifies recommended fields: `usage`, `aliases`
- Ensures all commands have `handle()` function
- Detects duplicate command names and aliases

```bash
python tools/check_command_structure.py
```

#### 2. **`check_duplicates.py`** - Duplicate Detection
- Finds duplicate command names
- Finds duplicate aliases
- Detects alias/command conflicts
- Lists commands by category

```bash
python tools/check_duplicates.py
```

#### 3. **`check_file_structure.py`** - File Structure Validation
- Verifies required files exist (`bot.py`, `config.py`, etc.)
- Checks required directories (`handlers`, `core`, `middleware`, `utils`)
- Counts Python files in each directory

```bash
python tools/check_file_structure.py
```

#### 4. **`check_imports.py`** - Import Consistency
- Detects deprecated `datetime.utcnow()` usage
- Finds `datetime.now()` without timezone
- Ensures consistent use of `now_utc()`

```bash
python tools/check_imports.py
```

#### 5. **`check_decorators.py`** - Decorator Usage
- Checks for `@log_command` decorator
- Verifies `@require_admin` on admin commands
- Validates permission decorators

```bash
python tools/check_decorators.py
```

#### 6. **`check_datetime.py`** - Datetime Patterns
- Ensures all datetimes are timezone-aware
- Counts files using `now_utc()`
- Lists files with datetime issues

```bash
python tools/check_datetime.py
```

#### 7. **`check_database.py`** - Database Operations
- Finds files with database operations
- Checks for error handling around DB queries
- Detects potential N+1 query problems

```bash
python tools/check_database.py
```

#### 8. **`check_security.py`** - Security Checks
- Detects hardcoded passwords and tokens
- Warns about SQL injection risks
- Flags dangerous `eval()` or `exec()` usage
- Checks for shell injection vulnerabilities

```bash
python tools/check_security.py
```

#### 9. **`check_code_quality.py`** - Code Quality Metrics
- Counts total lines of code
- Identifies files over 500 lines
- Finds functions over 100 lines
- Calculates average file size

```bash
python tools/check_code_quality.py
```

#### 10. **`check_error_handling.py`** - Error Handling Patterns
- Detects bare except clauses
- Finds generic Exception catches
- Checks for logging in handlers
- Verifies async function error handling
- Ensures user-friendly error messages

```bash
python tools/check_error_handling.py
```

#### 11. **`check_logging.py`** - Logging Consistency
- Checks logging import patterns
- Verifies logger name consistency
- Detects print() statements in production code
- Analyzes log level usage
- Identifies unused logging imports

```bash
python tools/check_logging.py
```

#### 12. **`check_telegram_limits.py`** - Telegram API Compliance
- Validates message length (4096 chars)
- Checks callback_data size (64 bytes)
- Detects rate limit risks
- Identifies deprecated API methods
- Finds missing rate limit handling

```bash
python tools/check_telegram_limits.py
```

#### 13. **`check_documentation.py`** - Documentation Coverage
- Checks module docstrings
- Validates function docstrings
- Analyzes class documentation
- Calculates documentation coverage
- Reports missing documentation

```bash
python tools/check_documentation.py
```

#### 14. **`check_performance.py`** - Performance Anti-patterns
- Detects string concatenation in loops
- Finds unnecessary copies
- Identifies synchronous I/O in async functions
- Checks for inefficient data structures
- Reports performance concerns

```bash
python tools/check_performance.py
```

### Master Validation Runner

#### **`run_all_checks.py`** - Run All Checks
Runs all validation checks sequentially and provides a comprehensive report with:
- Individual check results
- Success/failure summary
- Duration tracking
- Final grade (A+ to F)

```bash
# Run all checks
python tools/run_all_checks.py

# Or from tools directory
cd tools && ./run_all_checks.py
```

### Quick Commands

```bash
# Run all checks with master runner (RECOMMENDED)
python tools/run_all_checks.py

# Run all checks manually
cd tools
for tool in check_*.py; do echo "=== Running $tool ===" && python $tool; done

# Run specific check
python tools/check_security.py

# Run multiple specific checks
python tools/check_command_structure.py && python tools/check_duplicates.py

# Run critical checks only
python tools/check_security.py && python tools/check_duplicates.py && python tools/check_telegram_limits.py
```

#### Grading System

| Grade | Errors | Warnings | Status |
|-------|--------|----------|--------|
| **A+** | 0 | 0 | Perfect! |
| **A** | 0 | 1-4 | Excellent |
| **B** | 0 | 5-14 | Good |
| **C** | 0 | 15+ | Okay |
| **D** | 1-4 | Any | Needs Work |
| **F** | 5+ | Any | Major Issues |

#### Example Output

```
================================================================================
                    ZYRAX BOT CODEBASE VALIDATION
================================================================================

ℹ Found 89 handler files to check
ℹ Checked 89 files, found 67 commands

✓ No errors found!
✓ No warnings!

Final Grade: A+ EXCELLENT - Perfect codebase!
```

---

### Enhanced Validation: `validation_core.py` + `validation_plugins.py`

Advanced plugin-based validation system with structured output, severity levels, and configurable checks.

#### Key Improvements Over Basic Validation

✅ **Plugin Architecture** - Modular, extensible design  
✅ **Enhanced AST Analysis** - Proper decorator and function detection  
✅ **Structured Output** - Severity levels, line numbers, fix suggestions  
✅ **Configuration File** - YAML-based customization  
✅ **Telegram-Specific Validations** - Message/callback limits, deprecated APIs  
✅ **Advanced Security Checks** - Token detection, injection vulnerabilities  
✅ **JSON Export** - Machine-readable results for CI/CD  

#### Available Plugins

1. **TelegramAPIPlugin** - Validates Telegram API usage
   - Message length limits (4096 chars)
   - Callback data length (64 bytes)
   - Deprecated API methods
   - Error handling for API calls

2. **SecurityPlugin** - Security vulnerability detection
   - Hardcoded tokens and API keys
   - eval/exec usage
   - Command injection risks
   - SQL injection vulnerabilities
   - Unsafe deserialization

3. **DatetimePlugin** - Timezone-aware datetime checks
   - Deprecated datetime.utcnow()
   - Naive datetime.now()
   - Suggests now_utc() helper

4. **DecoratorPlugin** - Decorator validation
   - Required decorators by command category
   - Decorator order
   - @require_admin on admin commands
   - @log_command for audit trails

5. **AsyncAwaitPlugin** - Async/await best practices
   - Blocking I/O detection
   - open() instead of aiofiles
   - requests instead of aiohttp
   - time.sleep() in async code

6. **CommandStructurePlugin** - COMMAND_INFO validation
   - Required and recommended fields
   - handle() function existence

7. **DatabasePlugin** - Database operation checks
   - Error handling around DB operations
   - N+1 query problems
   - Transaction usage

#### Usage

```bash
# Basic usage
python tools/validate_enhanced.py

# With configuration
python tools/validate_enhanced.py --config .validation-config.yml

# JSON output
python tools/validate_enhanced.py --output json > results.json

# Specific directory
python tools/validate_enhanced.py --path handlers/moderation

# Only errors
python tools/validate_enhanced.py --severity error
```

#### Configuration Example

Create `.validation-config.yml` in the project root:

```yaml
checks:
  command_structure:
    enabled: true
    severity: "error"
    required_fields: [name, description, category, usage]
    recommended_fields: [aliases, scope]
  
  security:
    enabled: true
    severity: "critical"
    checks:
      - hardcoded_tokens
      - sql_injection
      - command_injection
  
  telegram_api:
    enabled: true
    severity: "warning"

paths:
  ignore_patterns:
    - "*/venv/*"
    - "*/tests/*"
```

#### Output Formats

**Terminal Output:**
```
[ERROR] handlers/admin/promote.py:25 - Missing required field 'usage'
  💡 Suggestion: Add 'usage' field to COMMAND_INFO dictionary

[WARNING] handlers/economy/gamble.py:42 - Blocking I/O: requests
  💡 Suggestion: Use aiohttp for async HTTP requests
```

**JSON Output:**
```json
{
  "summary": {
    "total_issues": 15,
    "by_severity": {
      "critical": 0,
      "error": 3,
      "warning": 7,
      "info": 5
    }
  },
  "issues": [...]
}
```

---

## 🔧 Integration

### Pre-commit Hook

```bash
# In .git/hooks/pre-commit
#!/bin/bash
python tools/validate_codebase.py
if [ $? -ne 0 ]; then
    echo "Validation failed! Fix errors before committing."
    exit 1
fi
```

### GitHub Actions

```yaml
name: Code Quality
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Run validation
        run: python tools/validate_codebase.py
```

---

## 📊 Comparison: Basic vs Enhanced

| Feature | Basic Validator | Enhanced Validator |
|---------|-----------------|-------------------|
| Output Format | Terminal only | Terminal, JSON |
| Line Numbers | Limited | Full support |
| Severity Levels | Basic (✓/⚠/✗) | 4 levels with icons |
| Fix Suggestions | None | Automatic suggestions |
| AST Analysis | Basic | Deep analysis |
| Configuration | Hardcoded | YAML config file |
| Extensibility | Monolithic | Plugin architecture |
| Telegram Checks | Basic | Comprehensive |
| Security Checks | Basic | Advanced |

**Recommendation:** Use basic validator for quick checks, enhanced validator for CI/CD and detailed analysis.

---

## 🛠️ Future Tools

Planned tools for this directory:

- `generate_docs.py` - Auto-generate command documentation
- `test_runner.py` - Run all unit tests with coverage
- `performance_profiler.py` - Profile bot performance
- `migration_helper.py` - Database migration tool
- `backup_manager.py` - Automated backup system
- `deployment_checker.py` - Pre-deployment validation

---

## 📝 Adding Custom Validation Plugins

### 1. Create Plugin Class

```python
from tools.validation_core import ValidationPlugin, ValidationIssue, Severity

class MyCustomPlugin(ValidationPlugin):
    @property
    def name(self) -> str:
        return "My Custom Validation"
    
    def validate(self, file_path, content, ast_tree):
        issues = []
        
        # Your validation logic here
        if "bad_pattern" in content:
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                category="custom",
                message="Found bad pattern",
                file_path=file_path,
                fix_suggestion="Replace with good pattern"
            ))
        
        return issues
```

### 2. Register Plugin

```python
# In validate_enhanced.py
from tools.validation_plugins import MyCustomPlugin

validator.register_plugin(MyCustomPlugin(config))
```

### 3. Add Configuration

```yaml
# In .validation-config.yml
checks:
  my_custom:
    enabled: true
    severity: "warning"
```

---

## 💡 Best Practices

1. ✅ Run basic validation frequently during development
2. ✅ Run enhanced validation before committing
3. ✅ Enable all checks initially, then tune based on your needs
4. ✅ Set appropriate severity levels for your project
5. ✅ Review warnings regularly - they often indicate real problems
6. ✅ Integrate into CI/CD pipeline
7. ✅ Update configuration as your codebase evolves

---

## 🆘 Support

For issues or suggestions:
1. Check the configuration file
2. Review the plugin documentation
3. Run with `--verbose` flag for detailed output
4. Create an issue with the full error message

---

**Last Updated:** October 5, 2025  
**Version:** 2.0.0