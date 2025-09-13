#!/usr/bin/env python3
"""
Cleanup script to remove unnecessary files from the project.
This script removes files that should not be committed to the repository.
"""

import os
import shutil
import glob
from pathlib import Path

def remove_files(pattern):
    """Remove files matching the given pattern."""
    files = glob.glob(pattern)
    for file in files:
        try:
            if os.path.isfile(file):
                os.remove(file)
                print(f"Removed file: {file}")
            elif os.path.isdir(file):
                shutil.rmtree(file)
                print(f"Removed directory: {file}")
        except Exception as e:
            print(f"Error removing {file}: {e}")

def main():
    """Main function to clean up the project."""
    project_root = Path(__file__).parent.parent
    
    print("Cleaning up project...")
    
    # Remove log files
    remove_files(str(project_root / "*.log"))
    remove_files(str(project_root / "logs"))
    
    # Remove database files
    remove_files(str(project_root / "*.db"))
    remove_files(str(project_root / "*.sqlite"))
    remove_files(str(project_root / "*.sqlite-*"))
    
    # Remove PID files
    remove_files(str(project_root / "*.pid"))
    
    # Remove temporary files
    remove_files(str(project_root / ".last_result.json"))
    
    # Remove cache directories
    remove_files(str(project_root / ".pytest_cache"))
    
    # Remove development tool directories
    remove_files(str(project_root / ".kiro"))
    
    # Remove virtual environment
    remove_files(str(project_root / "trading_env"))
    
    # Remove backtest files
    remove_files(str(project_root / "backtest*"))
    
    # Remove IDE specific directories
    remove_files(str(project_root / ".vscode"))
    
    # Remove empty .env file
    env_file = project_root / ".env"
    if env_file.exists() and env_file.stat().st_size == 0:
        try:
            env_file.unlink()
            print("Removed empty .env file")
        except Exception as e:
            print(f"Error removing .env file: {e}")
    
    print("Cleanup completed.")

if __name__ == "__main__":
    main()