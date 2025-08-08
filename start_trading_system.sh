#!/bin/bash

# Advanced Trading System Launcher
# Starts Freqrade + OpenBB Dashboard + All Services

echo "🚀 STARTING ADVANCED TRADING SYSTEM"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if virtual environment exists
if [ ! -d "trading_env" ]; then
    print_error "Virtual environment not found. Creating one..."
    python3 -m venv trading_env
    source trading_env/bin/activate
    pip install freqtrade[all] openbb yfinance ccxt pandas numpy ta-lib flask
else
    print_status "Virtual environment found"
fi

# Activate virtual environment
source trading_env/bin/activate
print_status "Virtual environment activated"

# Kill any existing processes
print_info "Cleaning up existing processes..."
pkill -f "freqtrade" 2>/dev/null || true
pkill -f "app.py" 2>/dev/null || true
sleep 2

# Create config if it doesn't exist
if [ ! -f "config/config.json" ]; then
    print_warning "Creating default Freqtrade config..."
    mkdir -p config
    cat > config/config.json << 'EOF'
{
    "max_open_trades": 3,
    "stake_currency": "USDT",
    "stake_amount": 100,
    "tradable_balance_ratio": 0.99,
    "fiat_display_currency": "USD",
    "dry_run": true,
    "dry_run_wallet": 1000,
    "cancel_open_orders_on_exit": false,
    "trading_mode": "spot",
    "margin_mode": "",
    "unfilledtimeout": {
        "entry": 10,
        "exit": 10,
        "exit_timeout_count": 0,
        "unit": "minutes"
    },
    "entry_pricing": {
        "price_side": "same",
        "use_order_book": true,
        "order_book_top": 1,
        "price_last_balance": 0.0,
        "check_depth_of_market": {
            "enabled": false,
            "bids_to_ask_delta": 1
        }
    },
    "exit_pricing": {
        "price_side": "same",
        "use_order_book": true,
        "order_book_top": 1
    },
    "exchange": {
        "name": "binance",
        "key": "",
        "secret": "",
        "ccxt_config": {},
        "ccxt_async_config": {},
        "pair_whitelist": [
            "BTC/USDT",
            "ETH/USDT",
            "ADA/USDT",
            "DOT/USDT",
            "LTC/USDT"
        ],
        "pair_blacklist": []
    },
    "pairlists": [
        {"method": "StaticPairList"}
    ],
    "edge": {
        "enabled": false,
        "process_throttle_secs": 3600,
        "calculate_since_number_of_days": 7,
        "allowed_risk": 0.01,
        "stoploss_range_min": -0.01,
        "stoploss_range_max": -0.1,
        "stoploss_range_step": -0.01,
        "minimum_winrate": 0.60,
        "minimum_expectancy": 0.20,
        "min_trade_number": 10,
        "max_trade_duration_minute": 1440,
        "remove_pumps": false
    },
    "telegram": {
        "enabled": false
    },
    "api_server": {
        "enabled": true,
        "listen_ip_address": "127.0.0.1",
        "listen_port": 8080,
        "verbosity": "error",
        "enable_openapi": false,
        "jwt_secret_key": "somethingrandom",
        "ws_token": "samplews",
        "CORS_origins": [],
        "username": "freqtrade",
        "password": "freqtrade"
    },
    "bot_name": "freqtrade",
    "initial_state": "running",
    "force_entry_enable": false,
    "internals": {
        "process_throttle_secs": 5
    }
}
EOF
    print_status "Default config created"
fi

# Start Freqtrade in background
print_info "Starting Freqtrade with MultiSignalStrategy..."
freqtrade trade --config config/config.json --strategy MultiSignalStrategy > logs/freqtrade.log 2>&1 &
FREQTRADE_PID=$!
sleep 5

# Check if Freqtrade started successfully
if ps -p $FREQTRADE_PID > /dev/null; then
    print_status "Freqtrade started successfully (PID: $FREQTRADE_PID)"
else
    print_error "Failed to start Freqtrade"
    exit 1
fi

# Start the advanced dashboard
print_info "Starting Advanced Trading Dashboard..."
cd src/web_ui
python app.py > ../../logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
cd ../..
sleep 3

# Check if dashboard started successfully
if ps -p $DASHBOARD_PID > /dev/null; then
    print_status "Dashboard started successfully (PID: $DASHBOARD_PID)"
else
    print_error "Failed to start Dashboard"
fi

# Display system status
echo ""
echo "🎉 TRADING SYSTEM STARTED SUCCESSFULLY!"
echo "======================================"
print_status "Freqtrade API: http://127.0.0.1:8080"
print_status "Freqtrade UI: http://127.0.0.1:8080"
print_status "Advanced Dashboard: http://127.0.0.1:5001"
echo ""
print_info "FEATURES AVAILABLE:"
echo "   🔥 Multi-Signal Strategy (Technical + On-Chain + Sentiment)"
echo "   📊 OpenBB Platform Integration"
echo "   🔄 Advanced Delta Analysis"
echo "   📈 Volume Profile Analysis"
echo "   🏦 Institutional Activity Tracking"
echo "   💹 Real-time Market Depth"
echo "   🎯 Tiger Trade-like Interface"
echo ""
print_info "QUICK ACCESS:"
echo "   📱 Freqtrade Web UI: http://127.0.0.1:8080"
echo "   🚀 Advanced Dashboard: http://127.0.0.1:5001"
echo ""
print_warning "DEMO MODE ACTIVE - No real money at risk"
echo ""

# Save PIDs for cleanup
echo $FREQTRADE_PID > .freqtrade.pid
echo $DASHBOARD_PID > .dashboard.pid

# Open browsers
if command -v xdg-open > /dev/null; then
    print_info "Opening Freqtrade UI..."
    xdg-open "http://127.0.0.1:8080" 2>/dev/null &
    sleep 2
    print_info "Opening Advanced Dashboard..."
    xdg-open "http://127.0.0.1:5001" 2>/dev/null &
elif command -v open > /dev/null; then
    print_info "Opening Freqtrade UI..."
    open "http://127.0.0.1:8080" 2>/dev/null &
    sleep 2
    print_info "Opening Advanced Dashboard..."
    open "http://127.0.0.1:5001" 2>/dev/null &
fi

# Wait and monitor
print_info "System running... Press Ctrl+C to stop all services"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    print_info "Shutting down trading system..."
    
    if [ -f .freqtrade.pid ]; then
        FREQTRADE_PID=$(cat .freqtrade.pid)
        if ps -p $FREQTRADE_PID > /dev/null; then
            kill $FREQTRADE_PID
            print_status "Freqtrade stopped"
        fi
        rm -f .freqtrade.pid
    fi
    
    if [ -f .dashboard.pid ]; then
        DASHBOARD_PID=$(cat .dashboard.pid)
        if ps -p $DASHBOARD_PID > /dev/null; then
            kill $DASHBOARD_PID
            print_status "Dashboard stopped"
        fi
        rm -f .dashboard.pid
    fi
    
    # Kill any remaining processes
    pkill -f "freqtrade" 2>/dev/null || true
    pkill -f "app.py" 2>/dev/null || true
    
    print_status "All services stopped"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Monitor processes
while true; do
    sleep 10
    
    # Check Freqtrade
    if [ -f .freqtrade.pid ]; then
        FREQTRADE_PID=$(cat .freqtrade.pid)
        if ! ps -p $FREQTRADE_PID > /dev/null; then
            print_error "Freqtrade process died! Check logs/freqtrade.log"
        fi
    fi
    
    # Check Dashboard
    if [ -f .dashboard.pid ]; then
        DASHBOARD_PID=$(cat .dashboard.pid)
        if ! ps -p $DASHBOARD_PID > /dev/null; then
            print_error "Dashboard process died! Check logs/dashboard.log"
        fi
    fi
done