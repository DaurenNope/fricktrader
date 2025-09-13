#!/usr/bin/env python3
"""
Multi-Strategy Trading System Launcher
Starts the portfolio management system with multiple trading strategies
"""

import os
import sys
import argparse
import json
import logging
from datetime import datetime

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.multi_strategy_trader import MultiStrategyTrader

def setup_logging(log_level='INFO'):
    """Setup logging configuration"""
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Setup file logging
    log_filename = f"logs/multi_strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging started - Log file: {log_filename}")
    
    return logger

def check_prerequisites():
    """Check that all required files and directories exist"""
    
    required_files = [
        'user_data/config.json',
        'user_data/strategies/SimpleTrendStrategy.py',
        'user_data/strategies/ComprehensiveSmartMoneyStrategy.py'
    ]
    
    required_dirs = [
        'user_data',
        'user_data/strategies',  
        'user_data/data',
        'user_data/backtest_results'
    ]
    
    # Check directories
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
    
    # Check files
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        print("\nPlease ensure all strategies and config files are in place.")
        return False
    
    print("✅ All prerequisites satisfied")
    return True

def create_default_config():
    """Create default configuration if none exists"""
    
    config_path = 'user_data/config.json'
    
    if os.path.exists(config_path):
        return
    
    default_config = {
        "max_open_trades": 15,  # Higher for multiple strategies
        "stake_currency": "USDT",
        "stake_amount": 50,     # Lower per trade since we have multiple strategies
        "tradable_balance_ratio": 1.0,
        "fiat_display_currency": "USD",
        "dry_run": True,        # Start in dry run mode for safety
        "cancel_open_orders_on_exit": False,
        "trading_mode": "spot",
        "margin_mode": "",
        
        "unfilledtimeout": {
            "entry": 10,
            "exit": 10,
            "exit_timeout_count": 0,
            "unit": "minutes"
        },
        
        "entry_pricing": {
            "price_side": "other",
            "use_order_book": True,
            "order_book_top": 1,
            "price_last_balance": 0.0,
            "check_depth_of_market": {
                "enabled": False,
                "bids_to_ask_delta": 1
            }
        },
        
        "exit_pricing": {
            "price_side": "same",
            "use_order_book": True,
            "order_book_top": 1
        },
        
        "exchange": {
            "name": "binance",
            "key": "",
            "secret": "",
            "ccxt_config": {},
            "ccxt_async_config": {},
            "pair_whitelist": [
                "BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "ADA/USDT",
                "DOT/USDT", "LINK/USDT", "UNI/USDT", "MATIC/USDT", "LTC/USDT",
                "ATOM/USDT", "ICP/USDT", "NEAR/USDT", "ALGO/USDT", "VET/USDT"
            ],
            "pair_blacklist": []
        },
        
        "pairlists": [
            {"method": "StaticPairList"}
        ],
        
        "api_server": {
            "enabled": True,
            "listen_ip_address": "127.0.0.1",
            "listen_port": 8080,
            "verbosity": "info",
            "enable_openapi": True,
            "jwt_secret_key": "multi-strategy-system",
            "CORS_origins": ["*"],
            "username": "",
            "password": ""
        },
        
        "portfolio": {
            "total_capital": 10000,
            "max_strategies": 4,
            "rebalance_hours": 6,
            "min_confidence": 0.6
        },
        
        "bot_name": "Multi-Strategy Trader",
        "initial_state": "running",
        "force_entry_enable": False,
        
        "internals": {
            "process_throttle_secs": 5
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print(f"✅ Created default configuration: {config_path}")

def show_system_info():
    """Show system information and strategy overview"""
    
    print("\n" + "="*60)
    print("🚀 MULTI-STRATEGY TRADING SYSTEM")
    print("="*60)
    print()
    print("Available Strategies:")
    print("  📈 SimpleTrendStrategy      - Bull market trend following")
    print("  💰 ComprehensiveSmartMoney - Smart Money Concepts (SMC)")  
    print("  🚀 BreakoutMomentumStrategy - Breakout & momentum trades")
    print("  ⚡ ScalpingStrategy         - High-frequency scalping")
    print()
    print("Portfolio Management:")
    print("  🔄 Automatic rebalancing based on market conditions")
    print("  📊 Market regime detection (Bull/Bear/Sideways)")
    print("  ⚖️  Dynamic capital allocation per strategy")
    print("  🛡️  Risk management across entire portfolio")
    print()
    print("Features:")
    print("  📱 Web dashboard at http://localhost:8080")
    print("  📈 Real-time performance monitoring")
    print("  🔧 Individual strategy optimization")
    print("  💾 Comprehensive logging and analytics")
    print("="*60)

def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description='Multi-Strategy Trading System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_multi_strategy.py                    # Start with default config
  python start_multi_strategy.py --dry-run          # Force dry-run mode
  python start_multi_strategy.py --live             # Enable live trading
  python start_multi_strategy.py --log-level DEBUG  # Enable debug logging
        """
    )
    
    parser.add_argument('--config', default='user_data/config.json',
                       help='Configuration file path')
    parser.add_argument('--dry-run', action='store_true',
                       help='Force dry-run mode (paper trading)')
    parser.add_argument('--live', action='store_true', 
                       help='Enable live trading (overrides config)')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    parser.add_argument('--setup-only', action='store_true',
                       help='Only setup files and exit')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.log_level)
    
    # Show system info
    show_system_info()
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Create default config if needed
    create_default_config()
    
    # Setup only mode
    if args.setup_only:
        print("✅ Setup completed successfully!")
        print("   Run without --setup-only to start trading")
        return
    
    try:
        # Load and modify config based on args
        with open(args.config, 'r') as f:
            config = json.load(f)
        
        # Handle dry-run/live mode
        if args.dry_run:
            config['dry_run'] = True
            logger.info("🔒 Running in DRY-RUN mode (paper trading)")
        elif args.live:
            config['dry_run'] = False
            logger.warning("⚠️  LIVE TRADING MODE ENABLED!")
            
            # Safety confirmation for live trading
            response = input("\n⚠️  Are you sure you want to enable LIVE TRADING? (type 'YES' to confirm): ")
            if response != 'YES':
                logger.info("Live trading cancelled by user")
                return
        
        # Save updated config
        with open(args.config, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Create and start the multi-strategy system
        logger.info("🚀 Starting Multi-Strategy Trading System...")
        
        trader = MultiStrategyTrader(args.config)
        
        # Run the system
        import asyncio
        asyncio.run(trader.run())
        
    except KeyboardInterrupt:
        logger.info("👋 System shutdown requested by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        raise
    finally:
        logger.info("🛑 Multi-Strategy Trading System stopped")

if __name__ == "__main__":
    main()