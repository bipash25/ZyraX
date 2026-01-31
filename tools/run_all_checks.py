#!/usr/bin/env python3
"""
Master Validation Runner
Runs all validation checks and provides a comprehensive report
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


def print_header(text):
    print(f"\n\033[95m\033[1m{'='*80}\033[0m")
    print(f"\033[95m\033[1m{text.center(80)}\033[0m")
    print(f"\033[95m\033[1m{'='*80}\033[0m\n")


def print_success(text):
    print(f"\033[92m✓ {text}\033[0m")


def print_error(text):
    print(f"\033[91m✗ {text}\033[0m")


def print_info(text):
    print(f"\033[96mℹ {text}\033[0m")


def run_check(check_script: Path) -> tuple:
    """
    Run a single check script
    
    Returns:
        Tuple of (success, output)
    """
    try:
        result = subprocess.run(
            [sys.executable, str(check_script)],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0, result.stdout
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def main():
    """Main entry point"""
    print_header("ZYRAX BOT - COMPREHENSIVE VALIDATION")
    
    start_time = datetime.now()
    
    # Get tools directory
    tools_dir = Path(__file__).parent
    
    # Find all check scripts
    check_scripts = sorted(tools_dir.glob("check_*.py"))
    
    if not check_scripts:
        print_error("No check scripts found!")
        sys.exit(1)
    
    print_info(f"Found {len(check_scripts)} validation checks")
    print_info(f"Starting validation at {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {}
    
    # Run each check
    for i, script in enumerate(check_scripts, 1):
        check_name = script.stem.replace('check_', '').replace('_', ' ').title()
        print(f"\n[{i}/{len(check_scripts)}] Running {check_name}...")
        print("-" * 80)
        
        success, output = run_check(script)
        results[check_name] = success
        
        if success:
            print_success(f"{check_name} passed")
        else:
            print_error(f"{check_name} failed")
        
        # Show brief output
        lines = output.split('\n')
        # Show only summary/results section
        in_results = False
        for line in lines:
            if 'RESULTS' in line or 'results' in line.lower():
                in_results = True
            if in_results:
                print(line)
    
    # Print final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print_header("VALIDATION SUMMARY")
    
    passed = sum(1 for success in results.values() if success)
    failed = len(results) - passed
    
    print(f"⏱️  Duration: {duration:.2f} seconds\n")
    print(f"📊 Results:")
    print(f"  • Total checks: {len(results)}")
    print(f"  • Passed: {passed}")
    print(f"  • Failed: {failed}")
    print(f"  • Success rate: {passed/len(results)*100:.1f}%\n")
    
    print("📋 Detailed Results:")
    for check_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        color = "\033[92m" if success else "\033[91m"
        print(f"  {color}{status}\033[0m - {check_name}")
    
    # Final grade
    print("\n🎯 Final Grade:")
    if failed == 0:
        print("\033[92m\033[1m  A+ EXCELLENT - All checks passed!\033[0m")
        grade = 0
    elif failed <= 2:
        print("\033[93m\033[1m  B GOOD - Minor issues found\033[0m")
        grade = 0
    elif failed <= 4:
        print("\033[93m\033[1m  C OKAY - Several issues to address\033[0m")
        grade = 1
    else:
        print("\033[91m\033[1m  F FAIL - Major issues found\033[0m")
        grade = 1
    
    print()
    
    sys.exit(grade)


if __name__ == "__main__":
    main()
