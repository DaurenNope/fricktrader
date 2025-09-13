#!/bin/bash

# FrickTrader - Universal Startup Script
# Handles demo mode, full trading mode, and dashboard-only mode

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Usage function
usage() {
    echo "FrickTrader Startup Script"
    echo ""
    echo "Usage: $0 [mode]"
    echo ""
    echo "Modes:"
    echo "  demo      Start dashboard with simulated trading (default)"
    echo "  full      Start Freqtrade + Dashboard (requires network)"
    echo "  dash      Start dashboard only"
    echo "  help      Show this help"
    echo ""
    echo "Examples:"
    echo "  $0          # Start integrated system (Freqtrade + Dashboard)"
    echo "  $0 full     # Start integrated system (Freqtrade + Dashboard)"
    echo "  $0 demo     # Start demo mode (Dashboard only, simulated data)"
    echo "  $0 dash     # Dashboard only"
    echo ""
}

# Set mode (default to full - Freqtrade + Dashboard integrated)
MODE="${1:-full}"

case $MODE in
    help|--help|-h)
        usage
        exit 0
        ;;
    demo|full|dash)
        ;;
    *)
        print_error "Unknown mode: $MODE"
        usage
        exit 1
        ;;
esac

echo "🚀 STARTING FRICKTRADER - MODE: $(echo $MODE | tr '[:lower:]' '[:upper:]')"
echo "=================================="

# Cleanup function
cleanup() {
    echo ""
    print_info "Shutting down FrickTrader..."
    pkill -f "freqtrade" 2>/dev/null || true
    pkill -f "app.py" 2>/dev/null || true
    pkill -f "simulate_trading.py" 2>/dev/null || true
    rm -f .*.pid 2>/dev/null || true
    print_status "All services stopped"
    exit 0
}
trap cleanup SIGINT SIGTERM

# Check virtual environment
if [ ! -d ".venv" ]; then
    print_error "Virtual environment not found. Run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

source .venv/bin/activate
print_status "Virtual environment activated"

# Clean up existing processes
print_info "Cleaning up existing processes..."
pkill -f "freqtrade" 2>/dev/null || true
pkill -f "app.py" 2>/dev/null || true
pkill -f "app_modular.py" 2>/dev/null || true
pkill -f "simulate_trading.py" 2>/dev/null || true
sleep 2

# Create logs directory
mkdir -p logs

# Start services based on mode
case $MODE in
    demo)
        print_info "Starting DEMO mode - simulated trading with real prices"

        # Start trading simulator
        print_info "Starting trading simulator..."
        python simulate_trading.py > logs/simulator.log 2>&1 &
        SIMULATOR_PID=$!
        sleep 3

        # Start comprehensive dashboard
        print_info "Starting comprehensive dashboard..."
        PORT=5003 python3 main_dashboard.py > logs/dashboard.log 2>&1 &
        DASHBOARD_PID=$!
        sleep 3

        # Check services
        if ps -p $DASHBOARD_PID > /dev/null; then
            print_status "Dashboard started on port 5001"
        else
            print_error "Dashboard failed to start"
            cleanup
            exit 1
        fi

        echo ""
        print_status "DEMO SYSTEM READY!"
        print_info "Dashboard: http://127.0.0.1:5003"
        print_warning "Demo mode - simulated trading data"
        ;;

    full)
        print_info "Starting FULL mode - Freqtrade + Dashboard"

        # Check if strategy exists
        if [ ! -f "user_data/strategies/MultiSignalStrategy.py" ]; then
            print_warning "Strategy not found, continuing anyway..."
        fi

        # Start Freqtrade
        print_info "Starting Freqtrade..."
        # First try without proxy
        freqtrade trade --config config/config.json --strategy SampleStrategy > logs/freqtrade.log 2>&1 &
        FREQTRADE_PID=$!
        echo $FREQTRADE_PID > .freqtrade.pid
        sleep 10

        # Check if Freqtrade failed due to exchange connection
        if ! ps -p $FREQTRADE_PID > /dev/null || grep -q "ExchangeNotAvailable\|Connection refused" logs/freqtrade.log; then
            print_warning "Exchange blocked, trying with proxy..."
            kill $FREQTRADE_PID 2>/dev/null || true
            sleep 2

            # Set proxy environment variables
            export HTTP_PROXY="socks5://198.8.94.174:39078"
            export HTTPS_PROXY="socks5://198.8.94.174:39078"
            export http_proxy="socks5://198.8.94.174:39078"
            export https_proxy="socks5://198.8.94.174:39078"

            freqtrade trade --config config/config.json --strategy SampleStrategy >> logs/freqtrade.log 2>&1 &
            FREQTRADE_PID=$!
            echo $FREQTRADE_PID > .freqtrade.pid
            sleep 5
        fi

        # Start comprehensive dashboard
        print_info "Starting comprehensive dashboard..."
        PORT=5003 python3 main_dashboard.py > logs/dashboard.log 2>&1 &
        DASHBOARD_PID=$!
        echo $DASHBOARD_PID > .dashboard.pid
        sleep 3

        # Check services
        if ps -p $FREQTRADE_PID > /dev/null; then
            print_status "Freqtrade started (PID: $FREQTRADE_PID)"
        else
            print_error "Freqtrade failed to start - check logs/freqtrade.log"
            print_info "Falling back to demo mode..."
            exec $0 demo
        fi

        if ps -p $DASHBOARD_PID > /dev/null; then
            print_status "Dashboard started on port 5001"
        else
            print_error "Dashboard failed to start"
            cleanup
            exit 1
        fi

        echo ""
        print_status "FULL SYSTEM READY!"
        print_info "Freqtrade API: http://127.0.0.1:8080"
        print_info "Dashboard: http://127.0.0.1:5003"
        ;;

    dash)
        print_info "Starting DASHBOARD ONLY mode"

        # Start comprehensive dashboard only
        PORT=5003 python3 main_dashboard.py > logs/dashboard.log 2>&1 &
        DASHBOARD_PID=$!
        sleep 3

        if ps -p $DASHBOARD_PID > /dev/null; then
            print_status "Dashboard started on port 5001"
        else
            print_error "Dashboard failed to start"
            exit 1
        fi

        echo ""
        print_status "DASHBOARD READY!"
        print_info "Dashboard: http://127.0.0.1:5003"
        ;;
esac

echo ""
print_info "FEATURES:"
echo "   📊 Live crypto prices & market analysis"
echo "   💰 Portfolio tracking with real P&L"
echo "   🚀 Live trading signals with confidence scores"
echo "   📈 Active positions & backtesting results"
echo "   🌾 DeFi yield optimization (22%+ APY)"
echo "   🎯 Professional trading command center"
echo "   ⚡ Real-time updates every 30 seconds"
echo ""

# Open browser
if command -v open > /dev/null; then
    print_info "Opening dashboard..."
    open "http://127.0.0.1:5003" 2>/dev/null &
fi

print_info "System running... Press Ctrl+C to stop"

# Monitor processes
while true; do
    sleep 10

    # Check dashboard
    if [ -n "$DASHBOARD_PID" ] && ! ps -p $DASHBOARD_PID > /dev/null; then
        print_error "Dashboard died! Check logs/dashboard.log"
        break
    fi

    # Check Freqtrade (if running)
    if [ -n "$FREQTRADE_PID" ] && ! ps -p $FREQTRADE_PID > /dev/null; then
        print_error "Freqtrade died! Check logs/freqtrade.log"
    fi
done

cleanup
