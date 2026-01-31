#!/usr/bin/env python3
"""
Changelog Generator
Generates CHANGELOG.md from git commits
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
import re


def print_info(text):
    print(f"\033[96mℹ {text}\033[0m")


def print_success(text):
    print(f"\033[92m✓ {text}\033[0m")


def print_error(text):
    print(f"\033[91m✗ {text}\033[0m")


def get_git_tags():
    """Get all git tags"""
    try:
        result = subprocess.run(
            ['git', 'tag', '--sort=-v:refname'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        return []


def get_commits_between(tag1=None, tag2=None):
    """Get commits between two tags"""
    try:
        if tag1 and tag2:
            cmd = ['git', 'log', f'{tag2}..{tag1}', '--pretty=format:%H|%s|%an|%ai']
        elif tag1:
            cmd = ['git', 'log', f'{tag1}', '--pretty=format:%H|%s|%an|%ai']
        else:
            cmd = ['git', 'log', '--pretty=format:%H|%s|%an|%ai']
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                hash, message, author, date = line.split('|', 3)
                commits.append({
                    'hash': hash[:7],
                    'message': message,
                    'author': author,
                    'date': date
                })
        
        return commits
    except subprocess.CalledProcessError:
        return []


def categorize_commit(message):
    """Categorize commit based on message"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['feat', 'feature', 'add']):
        return 'Features'
    elif any(word in message_lower for word in ['fix', 'bug', 'patch']):
        return 'Bug Fixes'
    elif any(word in message_lower for word in ['docs', 'documentation']):
        return 'Documentation'
    elif any(word in message_lower for word in ['refactor', 'restructure']):
        return 'Refactoring'
    elif any(word in message_lower for word in ['test', 'testing']):
        return 'Tests'
    elif any(word in message_lower for word in ['chore', 'build', 'ci']):
        return 'Chores'
    elif any(word in message_lower for word in ['perf', 'performance', 'optimize']):
        return 'Performance'
    elif any(word in message_lower for word in ['security', 'secure']):
        return 'Security'
    else:
        return 'Other Changes'


def generate_changelog(output_file='CHANGELOG.md'):
    """Generate changelog"""
    
    project_root = Path(__file__).parent.parent
    output_path = project_root / output_file
    
    print_info("Fetching git history...")
    
    tags = get_git_tags()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Header
        f.write("# Changelog\n\n")
        f.write("All notable changes to ZyraX Bot will be documented in this file.\n\n")
        f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        
        if tags:
            # Write for each version
            for i, tag in enumerate(tags):
                print_info(f"Processing version {tag}...")
                
                # Get commits for this version
                prev_tag = tags[i + 1] if i + 1 < len(tags) else None
                commits = get_commits_between(tag, prev_tag)
                
                if not commits:
                    continue
                
                # Group commits by category
                categorized = {}
                for commit in commits:
                    category = categorize_commit(commit['message'])
                    if category not in categorized:
                        categorized[category] = []
                    categorized[category].append(commit)
                
                # Write version header
                f.write(f"## [{tag}] - {commits[0]['date'][:10]}\n\n")
                
                # Write categories
                category_order = [
                    'Features', 'Bug Fixes', 'Performance', 'Security',
                    'Documentation', 'Refactoring', 'Tests', 'Chores', 'Other Changes'
                ]
                
                for category in category_order:
                    if category in categorized:
                        f.write(f"### {category}\n\n")
                        for commit in categorized[category]:
                            # Format commit message
                            message = commit['message']
                            # Remove conventional commit prefix
                            message = re.sub(r'^(feat|fix|docs|refactor|test|chore|perf|security)(\(.+?\))?:\s*', '', message, flags=re.IGNORECASE)
                            f.write(f"- {message} ([`{commit['hash']}`](commit/{commit['hash']}))\n")
                        f.write("\n")
                
                f.write("---\n\n")
        else:
            # No tags, list all commits
            print_info("No tags found, listing all commits...")
            commits = get_commits_between()
            
            if commits:
                # Group by category
                categorized = {}
                for commit in commits:
                    category = categorize_commit(commit['message'])
                    if category not in categorized:
                        categorized[category] = []
                    categorized[category].append(commit)
                
                f.write("## [Unreleased]\n\n")
                
                for category, commits_list in sorted(categorized.items()):
                    f.write(f"### {category}\n\n")
                    for commit in commits_list:
                        message = commit['message']
                        message = re.sub(r'^(feat|fix|docs|refactor|test|chore|perf|security)(\(.+?\))?:\s*', '', message, flags=re.IGNORECASE)
                        f.write(f"- {message} ([`{commit['hash']}`](commit/{commit['hash']}))\n")
                    f.write("\n")
    
    print_success(f"Changelog generated: {output_path}")


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("CHANGELOG GENERATOR".center(80))
    print("="*80 + "\n")
    
    try:
        generate_changelog()
        print()
    except Exception as e:
        print_error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
