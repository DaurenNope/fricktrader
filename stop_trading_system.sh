#!/bin/bash

# Stop All Trading System Services

echo "🛑 STOPPING TRADING SYSTEM"
echo "=========================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Stop processes using PID files
if [ -f .freqtrade.pid ]; then
    FREQTRADE_PID=$(cat .freqtrade.pid)
    if ps -p $FREQTRADE_PID > /dev/null; then
        kill $FREQTRADE_PID
        print_status "Freqtrade stopped (PID: $FREQTRADE_PID)"
    fi
    rm -f .freqtrade.pid
fi

if [ -f .dashboard.pid ]; then
    DASHBOARD_PID=$(cat .dashboard.pid)
    if ps -p $DASHBOARD_PID > /dev/null; then
        kill $DASHBOARD_PID
        print_status "Dashboard stopped (PID: $DASHBOARD_PID)"
    fi
    rm -f .dashboard.pid
fi

# Kill any remaining processes
print_info "Cleaning up remaining processes..."
pkill -f "freqtrade" 2>/dev/null && print_status "Killed remaining Freqtrade processes"
pkill -f "app.py" 2>/dev/null && print_status "Killed remaining Flask processes"

print_status "All trading system services stopped"
echo "🎉 System shutdown complete"