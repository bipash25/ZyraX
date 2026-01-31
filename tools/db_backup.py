#!/usr/bin/env python3
"""
Database Backup Utility
Creates backups of MongoDB database
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
import os


def print_success(text):
    print(f"\033[92m✓ {text}\033[0m")


def print_error(text):
    print(f"\033[91m✗ {text}\033[0m")


def print_info(text):
    print(f"\033[96mℹ {text}\033[0m")


def load_env():
    """Load environment variables"""
    env_file = Path(__file__).parent.parent / ".env"
    
    if not env_file.exists():
        print_error(".env file not found!")
        return None
    
    env_vars = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip().strip('"').strip("'")
    
    return env_vars


def create_backup(output_dir: Path = None):
    """Create MongoDB backup"""
    
    # Load MongoDB URI from env
    env_vars = load_env()
    
    if not env_vars or 'MONGODB_URI' not in env_vars:
        print_error("MONGODB_URI not found in .env file!")
        sys.exit(1)
    
    mongo_uri = env_vars['MONGODB_URI']
    
    # Create backup directory
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "data" / "backups"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate backup filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"zyrax_backup_{timestamp}"
    backup_path = output_dir / backup_name
    
    print_info(f"Creating backup: {backup_name}")
    print_info(f"Output directory: {output_dir}")
    
    # Run mongodump
    try:
        cmd = [
            'mongodump',
            '--uri', mongo_uri,
            '--out', str(backup_path)
        ]
        
        print_info("Running mongodump...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes
        )
        
        if result.returncode == 0:
            print_success(f"Backup created successfully!")
            print_info(f"Location: {backup_path}")
            
            # Get backup size
            total_size = sum(
                f.stat().st_size for f in backup_path.rglob('*') if f.is_file()
            )
            size_mb = total_size / (1024 * 1024)
            print_info(f"Backup size: {size_mb:.2f} MB")
            
            return True
        else:
            print_error("Backup failed!")
            print(result.stderr)
            return False
    
    except FileNotFoundError:
        print_error("mongodump not found! Please install MongoDB tools.")
        print_info("Install: https://www.mongodb.com/try/download/database-tools")
        return False
    except subprocess.TimeoutExpired:
        print_error("Backup timed out!")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def list_backups(backup_dir: Path = None):
    """List available backups"""
    
    if backup_dir is None:
        backup_dir = Path(__file__).parent.parent / "data" / "backups"
    
    if not backup_dir.exists():
        print_info("No backups found.")
        return
    
    backups = sorted(backup_dir.glob("zyrax_backup_*"), reverse=True)
    
    if not backups:
        print_info("No backups found.")
        return
    
    print_info(f"Found {len(backups)} backup(s):\n")
    
    for backup in backups:
        # Get backup size
        total_size = sum(
            f.stat().st_size for f in backup.rglob('*') if f.is_file()
        )
        size_mb = total_size / (1024 * 1024)
        
        # Get backup date
        mtime = backup.stat().st_mtime
        date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"  • {backup.name}")
        print(f"    Size: {size_mb:.2f} MB | Created: {date_str}\n")


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("DATABASE BACKUP UTILITY".center(80))
    print("="*80 + "\n")
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'list':
            list_backups()
        elif sys.argv[1] == 'create':
            success = create_backup()
            sys.exit(0 if success else 1)
        else:
            print("Usage: python db_backup.py [create|list]")
            sys.exit(1)
    else:
        # Default: create backup
        success = create_backup()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
