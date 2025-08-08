# 🏗️ Clean Project Structure

## 📁 **Core Directories**

```
automated-trading-system/
├── config/                     # Configuration files
│   └── config.json            # Freqtrade configuration
├── src/                       # Source code
│   ├── approval/              # Manual approval system
│   ├── database/              # Database schemas and managers
│   ├── market_data/           # OpenBB and market analysis
│   ├── onchain/               # Blockchain data (Etherscan)
│   ├── sentiment/             # Social sentiment analysis
│   ├── social_trading/        # Trader discovery and validation
│   └── web_ui/                # Flask dashboard
├── user_data/                 # Freqtrade user data
│   └── strategies/            # Trading strategies
├── logs/                      # System logs
└── docs/                      # Documentation
```

## 🎯 **Key Files**

### **Essential Scripts**
- `start_dashboard.py` - Start the web dashboard
- `start_trading_system.sh` - Start Freqtrade bot
- `stop_trading_system.sh` - Stop Freqtrade bot

### **Core Components**
- `src/web_ui/app.py` - Main Flask dashboard
- `src/approval/manual_approval_manager.py` - Signal approval system
- `src/social_trading/trader_validator.py` - Trader validation system
- `user_data/strategies/MultiSignalStrategy.py` - Main trading strategy

### **Databases**
- `tradesv3.sqlite` - Freqtrade trades database
- `signal_approvals.db` - Manual approval queue
- `trade_logic.db` - AI decision reasoning

## 🚫 **What We Removed**
- All test files (test_*.py)
- Backup directories
- Unnecessary documentation
- Empty directories
- Cache files
- Research integration files

## 🎯 **Current Focus**
1. **Fix the manual approval integration**
2. **Clean up the dashboard UI**
3. **Ensure signal flow works end-to-end**
4. **Make the system actually usable**