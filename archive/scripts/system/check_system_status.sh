#!/bin/bash

# Advanced Crypto Trading System Status Checker
# This script checks the status of all system components

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📊 Advanced Crypto Trading System Status${NC}"
echo "=================================================="

# Function to check if a service is running by PID file
check_service_by_pid() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${GREEN}✅ $service_name: Running (PID: $pid)${NC}"
            return 0
        else
            echo -e "${RED}❌ $service_name: Not running (stale PID file)${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ $service_name: No PID file found${NC}"
        return 1
    fi
}

# Function to check if a URL is responding
check_url() {
    local url=$1
    local service_name=$2
    local auth=$3
    
    if [ ! -z "$auth" ]; then
        if curl -s -u "$auth" "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name API: Responding${NC}"
            return 0
        else
            echo -e "${RED}❌ $service_name API: Not responding${NC}"
            return 1
        fi
    else
        if curl -s "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name API: Responding${NC}"
            return 0
        else
            echo -e "${RED}❌ $service_name API: Not responding${NC}"
            return 1
        fi
    fi
}

# Check services by PID files
echo -e "${BLUE}🔍 Checking services by PID files...${NC}"
check_service_by_pid "freqtrade_trade.pid" "Freqtrade Trading Bot"
freqtrade_trade_running=$?
check_service_by_pid "freqtrade_webserver.pid" "Freqtrade Web Server"
freqtrade_web_running=$?
check_service_by_pid "web_ui.pid" "Custom Web UI"
web_ui_running=$?

echo ""

# Check API endpoints
echo -e "${BLUE}🌐 Checking API endpoints...${NC}"
check_url "http://localhost:8080/api/v1/ping" "Freqtrade" "freqtrade:freqtrade"
freqtrade_api_ok=$?
check_url "http://localhost:5000/api/status" "Custom Web UI" ""
web_ui_api_ok=$?

echo ""

# Get system information
echo -e "${BLUE}📊 System Information...${NC}"

# Get Freqtrade status
if [ $freqtrade_api_ok -eq 0 ]; then
    echo -e "${GREEN}🤖 Freqtrade Status:${NC}"
    freqtrade_status=$(curl -s -u freqtrade:freqtrade "http://localhost:8080/api/v1/show_config" 2>/dev/null)
    if [ ! -z "$freqtrade_status" ]; then
        strategy=$(echo "$freqtrade_status" | grep -o '"strategy":"[^"]*"' | cut -d'"' -f4)
        dry_run=$(echo "$freqtrade_status" | grep -o '"dry_run":[^,]*' | cut -d':' -f2)
        exchange=$(echo "$freqtrade_status" | grep -o '"exchange":"[^"]*"' | cut -d'"' -f4)
        
        echo "  • Strategy: $strategy"
        echo "  • Mode: $([ "$dry_run" = "true" ] && echo "Demo (Dry Run)" || echo "Live Trading")"
        echo "  • Exchange: $exchange"
    fi
fi

# Get Web UI status
if [ $web_ui_api_ok -eq 0 ]; then
    echo -e "${GREEN}🎨 Web UI Status:${NC}"
    web_ui_status=$(curl -s "http://localhost:5000/api/status" 2>/dev/null)
    if [ ! -z "$web_ui_status" ]; then
        mode=$(echo "$web_ui_status" | grep -o '"mode":"[^"]*"' | cut -d'"' -f4)
        open_trades=$(echo "$web_ui_status" | grep -o '"open_trades":[^,]*' | cut -d':' -f2)
        
        echo "  • Mode: $mode"
        echo "  • Open Trades: $open_trades"
    fi
fi

echo ""

# Overall system status
echo -e "${BLUE}🎯 Overall System Status:${NC}"
if [ $freqtrade_trade_running -eq 0 ] && [ $freqtrade_web_running -eq 0 ] && [ $web_ui_running -eq 0 ] && [ $freqtrade_api_ok -eq 0 ] && [ $web_ui_api_ok -eq 0 ]; then
    echo -e "${GREEN}✅ ALL SYSTEMS OPERATIONAL${NC}"
    echo ""
    echo -e "${BLUE}🌐 Access URLs:${NC}"
    echo "  • Custom Dashboard: http://localhost:5000"
    echo "  • Freqtrade Dashboard: http://localhost:8080"
    echo "    (Username: freqtrade, Password: freqtrade)"
else
    echo -e "${RED}❌ SYSTEM ISSUES DETECTED${NC}"
    echo ""
    echo -e "${YELLOW}💡 Troubleshooting:${NC}"
    echo "  • To restart the system: ./start_trading_system.sh"
    echo "  • To stop the system: ./stop_trading_system.sh"
    echo "  • Check log files: logs/freqtrade/, logs/web_ui/, logs/system/"
fi

echo ""

# Show recent log entries if there are issues
if [ $freqtrade_trade_running -ne 0 ] || [ $freqtrade_web_running -ne 0 ] || [ $web_ui_running -ne 0 ]; then
    echo -e "${YELLOW}📄 Recent log entries:${NC}"
    
    # Check for most recent Freqtrade trading log
    latest_trade_log=$(ls -t logs/freqtrade/freqtrade-trade_*.log 2>/dev/null | head -1)
    if [ ! -z "$latest_trade_log" ]; then
        echo -e "${BLUE}Freqtrade Trading (last 3 lines):${NC}"
        tail -3 "$latest_trade_log"
        echo ""
    elif [ -f "freqtrade_trade.log" ]; then
        echo -e "${BLUE}Freqtrade Trading (last 3 lines):${NC}"
        tail -3 freqtrade_trade.log
        echo ""
    fi
    
    # Check for most recent Freqtrade webserver log
    latest_webserver_log=$(ls -t logs/freqtrade/freqtrade-webserver_*.log 2>/dev/null | head -1)
    if [ ! -z "$latest_webserver_log" ]; then
        echo -e "${BLUE}Freqtrade Web Server (last 3 lines):${NC}"
        tail -3 "$latest_webserver_log"
        echo ""
    elif [ -f "freqtrade_webserver.log" ]; then
        echo -e "${BLUE}Freqtrade Web Server (last 3 lines):${NC}"
        tail -3 freqtrade_webserver.log
        echo ""
    fi
    
    # Check for most recent Web UI log
    latest_webui_log=$(ls -t logs/web_ui/web-ui_*.log 2>/dev/null | head -1)
    if [ ! -z "$latest_webui_log" ]; then
        echo -e "${BLUE}Web UI (last 3 lines):${NC}"
        tail -3 "$latest_webui_log"
        echo ""
    elif [ -f "web_ui.log" ]; then
        echo -e "${BLUE}Web UI (last 3 lines):${NC}"
        tail -3 web_ui.log
        echo ""
    fi
fi