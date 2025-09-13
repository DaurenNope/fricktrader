#!/bin/bash

# MVP Crypto Trading System - Environment Setup Script
echo "Setting up MVP Crypto Trading System environment..."

# Check if Python 3.8+ is available
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
if [[ $(echo "$python_version >= 3.8" | bc -l) -eq 0 ]]; then
    echo "Error: Python 3.8+ is required. Current version: $python_version"
    exit 1
fi

echo "✓ Python version check passed: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install TA-Lib dependencies (Ubuntu/Debian)
echo "Installing TA-Lib system dependencies..."
if command -v apt-get &> /dev/null; then
    echo "Detected Debian/Ubuntu system"
    sudo apt-get update
    sudo apt-get install -y build-essential wget
    
    # Download and install TA-Lib C library
    cd /tmp
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
    tar -xzf ta-lib-0.4.0-src.tar.gz
    cd ta-lib/
    ./configure --prefix=/usr
    make
    sudo make install
    cd -
elif command -v yum &> /dev/null; then
    echo "Detected RedHat/CentOS system"
    sudo yum groupinstall -y "Development Tools"
    sudo yum install -y wget
    
    # Download and install TA-Lib C library
    cd /tmp
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
    tar -xzf ta-lib-0.4.0-src.tar.gz
    cd ta-lib/
    ./configure --prefix=/usr
    make
    sudo make install
    cd -
else
    echo "Warning: Could not detect package manager. Please install TA-Lib manually."
    echo "Visit: https://ta-lib.org/hdr_dw.html"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Verify Freqtrade installation
echo "Verifying Freqtrade installation..."
freqtrade --version

if [ $? -eq 0 ]; then
    echo "✓ Freqtrade installed successfully"
else
    echo "✗ Freqtrade installation failed"
    exit 1
fi

# Create project directory structure
echo "Creating project directory structure..."
mkdir -p user_data/{strategies,data,logs}
mkdir -p src/{cli,approval,notifications,database}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p config
mkdir -p docs

echo "✓ Project structure created"

# Create initial configuration files
echo "Creating initial configuration files..."

# Basic Freqtrade config for paper trading
cat > config/config.json << 'EOF'
{
  "max_open_trades": 3,
  "stake_currency": "USDT",
  "stake_amount": "unlimited",
  "tradable_balance_ratio": 0.99,
  "fiat_display_currency": "USD",
  "dry_run": true,
  "dry_run_wallet": 1000,
  
  "timeframe": "1h",
  
  "exchange": {
    "name": "binance",
    "sandbox": true,
    "key": "",
    "secret": "",
    "ccxt_config": {},
    "ccxt_async_config": {},
    "pair_whitelist": [
      "BTC/USDT",
      "ETH/USDT",
      "ADA/USDT",
      "DOT/USDT",
      "LINK/USDT"
    ]
  },
  
  "entry_pricing": {
    "price_side": "same",
    "use_order_book": true,
    "order_book_top": 1
  },
  
  "exit_pricing": {
    "price_side": "same",
    "use_order_book": true,
    "order_book_top": 1
  },
  
  "pairlists": [
    {
      "method": "StaticPairList"
    }
  ],
  
  "telegram": {
    "enabled": false
  },
  
  "api_server": {
    "enabled": true,
    "listen_ip_address": "127.0.0.1",
    "listen_port": 8080,
    "verbosity": "error",
    "jwt_secret_key": "your-secret-key-change-this",
    "username": "freqtrade",
    "password": "freqtrade"
  },
  
  "bot_name": "MVP Crypto Trading Bot",
  "initial_state": "running",
  "force_entry_enable": false,
  "internals": {
    "process_throttle_secs": 5
  },
  
  "strategy": "MVPCryptoStrategy",
  "strategy_path": "user_data/strategies/",
  
  "db_url": "sqlite:///tradesv3.sqlite"
}
EOF

echo "✓ Basic Freqtrade configuration created"

# Test Freqtrade with basic configuration
echo "Testing Freqtrade configuration..."
freqtrade test-pairlist --config config/config.json

if [ $? -eq 0 ]; then
    echo "✓ Freqtrade configuration test passed"
else
    echo "✗ Freqtrade configuration test failed"
    exit 1
fi

echo ""
echo "🎉 Environment setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source .venv/bin/activate"
echo "2. Configure your exchange API keys in config/config.json (optional for paper trading)"
echo "3. Run the next task to create your custom strategy"
echo ""
echo "To verify everything is working:"
echo "  freqtrade --version"
echo "  freqtrade test-pairlist --config config/config.json"