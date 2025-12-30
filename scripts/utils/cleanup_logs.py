#!/usr/bin/env python3
"""
Log Cleanup Utility

This script helps manage and cleanup old log files to prevent disk space issues.
It can be run manually or scheduled as a cron job.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import shutil

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.logging_config import LOGS_DIR

def cleanup_old_logs(days_threshold=30, dry_run=False):
    """
    Cleanup log files older than specified days.
    
    Args:
        days_threshold: Delete files older than this many days
        dry_run: If True, only show what would be deleted without actually deleting
    """
    log_dirs = [
        LOGS_DIR,
        PROJECT_ROOT / "archive" / "logs",
        PROJECT_ROOT / "task_logs",
        PROJECT_ROOT / "logs"
    ]
    
    deleted_count = 0
    deleted_size = 0
    
    for log_dir in log_dirs:
        if not log_dir.exists():
            continue
            
        print(f"\nScanning directory: {log_dir}")
        
        for log_file in log_dir.glob("*.log*"):
            try:
                # Skip current log files (no suffix)
                if log_file.suffix == ".log" and not any(
                    log_file.name.endswith(f".log.{i}") for i in range(10)
                ):
                    continue
                
                file_age = datetime.now() - datetime.fromtimestamp(log_file.stat().st_mtime)
                
                if file_age > timedelta(days=days_threshold):
                    file_size = log_file.stat().st_size / (1024 * 1024)  # MB
                    
                    if dry_run:
                        print(f"  Would delete: {log_file.name} ({file_size:.2f} MB, {file_age.days} days old)")
                    else:
                        log_file.unlink()
                        print(f"  Deleted: {log_file.name} ({file_size:.2f} MB, {file_age.days} days old)")
                        deleted_count += 1
                        deleted_size += file_size
                        
            except Exception as e:
                print(f"  Error processing {log_file.name}: {e}")
    
    print(f"\nCleanup Summary:")
    print(f"  Files scanned: {sum(1 for d in log_dirs if d.exists() for f in d.glob('*.log*'))}")
    print(f"  Files deleted: {deleted_count}")
    print(f"  Space reclaimed: {deleted_size:.2f} MB")
    
    return deleted_count, deleted_size

def cleanup_large_logs(max_size_mb=50, dry_run=False):
    """
    Cleanup log files larger than specified size.
    
    Args:
        max_size_mb: Delete files larger than this size in MB
        dry_run: If True, only show what would be deleted without actually deleting
    """
    log_dirs = [
        LOGS_DIR,
        PROJECT_ROOT / "archive" / "logs",
        PROJECT_ROOT / "task_logs",
        PROJECT_ROOT / "logs"
    ]
    
    deleted_count = 0
    deleted_size = 0
    
    for log_dir in log_dirs:
        if not log_dir.exists():
            continue
            
        print(f"\nScanning directory: {log_dir}")
        
        for log_file in log_dir.glob("*.log*"):
            try:
                file_size = log_file.stat().st_size / (1024 * 1024)  # MB
                
                if file_size > max_size_mb:
                    if dry_run:
                        print(f"  Would delete: {log_file.name} ({file_size:.2f} MB)")
                    else:
                        # Create backup before deleting
                        backup_file = log_file.with_suffix(f".{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak")
                        shutil.move(str(log_file), str(backup_file))
                        print(f"  Archived: {log_file.name} -> {backup_file.name} ({file_size:.2f} MB)")
                        deleted_count += 1
                        deleted_size += file_size
                        
            except Exception as e:
                print(f"  Error processing {log_file.name}: {e}")
    
    print(f"\nCleanup Summary:")
    print(f"  Files scanned: {sum(1 for d in log_dirs if d.exists() for f in d.glob('*.log*'))}")
    print(f"  Files archived: {deleted_count}")
    print(f"  Space reclaimed: {deleted_size:.2f} MB")
    
    return deleted_count, deleted_size

def get_log_stats():
    """Get statistics about current log usage."""
    log_dirs = [
        LOGS_DIR,
        PROJECT_ROOT / "archive" / "logs",
        PROJECT_ROOT / "task_logs",
        PROJECT_ROOT / "logs"
    ]
    
    total_files = 0
    total_size = 0
    
    print("\nLog Statistics:")
    print("=" * 50)
    
    for log_dir in log_dirs:
        if not log_dir.exists():
            continue
            
        print(f"\nDirectory: {log_dir}")
        
        dir_files = 0
        dir_size = 0
        
        for log_file in log_dir.glob("*.log*"):
            try:
                file_size = log_file.stat().st_size / (1024 * 1024)  # MB
                file_age = datetime.now() - datetime.fromtimestamp(log_file.stat().st_mtime)
                
                print(f"  {log_file.name}: {file_size:.2f} MB, {file_age.days} days old")
                
                dir_files += 1
                dir_size += file_size
                
            except Exception as e:
                print(f"  {log_file.name}: Error - {e}")
        
        total_files += dir_files
        total_size += dir_size
        
        print(f"  Total: {dir_files} files, {dir_size:.2f} MB")
    
    print(f"\nOverall Total: {total_files} files, {total_size:.2f} MB")
    
    return total_files, total_size

def main():
    parser = argparse.ArgumentParser(description="Log Cleanup Utility")
    parser.add_argument("--days", type=int, default=30, 
                       help="Delete files older than N days (default: 30)")
    parser.add_argument("--size", type=int, default=50,
                       help="Archive files larger than N MB (default: 50)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without actually doing it")
    parser.add_argument("--stats", action="store_true",
                       help="Show log statistics only")
    parser.add_argument("--clean-old", action="store_true",
                       help="Cleanup old files")
    parser.add_argument("--clean-large", action="store_true",
                       help="Cleanup large files")
    
    args = parser.parse_args()
    
    if args.stats or not (args.clean_old or args.clean_large):
        get_log_stats()
    
    if args.clean_old:
        print("\n" + "=" * 50)
        print("Cleaning old log files...")
        cleanup_old_logs(days_threshold=args.days, dry_run=args.dry_run)
    
    if args.clean_large:
        print("\n" + "=" * 50)
        print("Cleaning large log files...")
        cleanup_large_logs(max_size_mb=args.size, dry_run=args.dry_run)

if __name__ == "__main__":
    main()