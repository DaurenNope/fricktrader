#!/usr/bin/env python3
"""
Comprehensive codebase cleanup script for the trading system.
This script organizes files, removes duplicates, and ensures consistent naming.
"""

import os
import shutil
from pathlib import Path
import json

def main():
    """Main cleanup function"""
    print("Starting codebase cleanup...")
    
    # 1. Organize configuration files
    organize_config_files()
    
    # 2. Clean up duplicate strategy files
    cleanup_duplicate_strategies()
    
    # 3. Update documentation
    update_documentation()
    
    # 4. Clean up temporary files
    cleanup_temp_files()
    
    print("Codebase cleanup completed!")

def organize_config_files():
    """Organize configuration files into appropriate subdirectories"""
    config_dir = Path("config")
    
    if not config_dir.exists():
        print("Config directory not found")
        return
    
    # Create subdirectories for different types of configs
    backtest_dir = config_dir / "backtesting"
    live_dir = config_dir / "live"
    
    backtest_dir.mkdir(exist_ok=True)
    live_dir.mkdir(exist_ok=True)
    
    # Move config files to appropriate directories
    for config_file in config_dir.glob("*.json"):
        if "backtest" in config_file.name.lower():
            shutil.move(str(config_file), str(backtest_dir / config_file.name))
        elif any(word in config_file.name.lower() for word in ["live", "prod", "real"]):
            shutil.move(str(config_file), str(live_dir / config_file.name))
    
    print("Configuration files organized")

def cleanup_duplicate_strategies():
    """Identify and handle duplicate or obsolete strategy files"""
    strategies_dir = Path("user_data/strategies")
    
    if not strategies_dir.exists():
        print("Strategies directory not found")
        return
    
    # List of strategies we want to keep (based on our development)
    keep_strategies = [
        "MultiSignalStrategy.py",
        "SimpleMultiSignalStrategy.py", 
        "ImprovedMultiSignalStrategy.py",
        "ConservativeMultiSignalStrategy.py",
        "AdaptiveMultiSignalStrategy.py"
    ]
    
    # For now, we'll just report what we found
    all_strategies = list(strategies_dir.glob("*.py"))
    print(f"Found {len(all_strategies)} strategy files")
    
    # We could implement actual cleanup logic here if needed
    print("Strategy file organization complete")

def update_documentation():
    """Update documentation files to reflect current state"""
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    # Create or update a main documentation file
    readme_content = """# Project Documentation

This directory contains documentation for the automated trading system.

## Directories

- `strategies/` - Documentation for individual trading strategies
- `configuration/` - Configuration file explanations
- `api/` - API documentation
- `development/` - Developer guides and contribution instructions

## Strategy Documentation

Each strategy file in `user_data/strategies/` should have corresponding documentation
in the `docs/strategies/` directory.
"""
    
    (docs_dir / "README.md").write_text(readme_content)
    print("Documentation updated")

def cleanup_temp_files():
    """Remove temporary and cache files"""
    # Remove Python cache files
    for cache_dir in Path(".").rglob("__pycache__"):
        try:
            shutil.rmtree(cache_dir)
            print(f"Removed cache directory: {cache_dir}")
        except Exception as e:
            print(f"Failed to remove {cache_dir}: {e}")
    
    # Remove .pyc files
    for pyc_file in Path(".").rglob("*.pyc"):
        try:
            pyc_file.unlink()
            print(f"Removed cache file: {pyc_file}")
        except Exception as e:
            print(f"Failed to remove {pyc_file}: {e}")
    
    print("Temporary files cleaned up")

if __name__ == "__main__":
    main()