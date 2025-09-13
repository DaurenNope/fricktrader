#!/usr/bin/env python3
"""
Log cleanup script for the trading system.
This script archives or removes old log files to keep the system clean and organized.
"""

import shutil
from datetime import datetime, timedelta
from pathlib import Path

def cleanup_logs():
    """Clean up old log files according to retention policy"""
    logs_dir = Path("logs")
    
    if not logs_dir.exists():
        print("Logs directory not found")
        return
    
    # Define retention periods (in days)
    retention_days = 7
    
    # Process freqtrade logs
    freqtrade_logs_dir = logs_dir / "freqtrade"
    if freqtrade_logs_dir.exists():
        cleanup_directory(freqtrade_logs_dir, retention_days)
    
    # Process web_ui logs
    web_ui_logs_dir = logs_dir / "web_ui"
    if web_ui_logs_dir.exists():
        cleanup_directory(web_ui_logs_dir, retention_days)
    
    # Process system logs
    system_logs_dir = logs_dir / "system"
    if system_logs_dir.exists():
        cleanup_directory(system_logs_dir, retention_days)
    
    print("Log cleanup completed")

def cleanup_directory(directory: Path, retention_days: int):
    """Clean up files in a directory based on retention policy"""
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    for file_path in directory.iterdir():
        if file_path.is_file():
            # Get file modification time
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            # If file is older than retention period, archive it
            if mod_time < cutoff_date:
                archive_file(file_path)

def archive_file(file_path: Path):
    """Move old log files to the archived directory"""
    archived_dir = Path("logs") / "archived"
    archived_dir.mkdir(exist_ok=True)
    
    # Create new file path in archived directory
    archived_path = archived_dir / file_path.name
    
    try:
        shutil.move(str(file_path), str(archived_path))
        print(f"Archived: {file_path.name}")
    except Exception as e:
        print(f"Failed to archive {file_path.name}: {e}")

if __name__ == "__main__":
    cleanup_logs()