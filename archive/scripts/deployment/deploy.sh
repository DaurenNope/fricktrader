#!/bin/bash

# FrickTrader Deployment Script
# This script deploys the system with the environment variables

echo "🚀 DEPLOYING FRICKTRADER SYSTEM"
echo "================================"

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

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error "Environment file (.env) not found!"
    print_info "Please create a .env file with your configuration."
    exit 1
fi

print_status "Environment file found"

# Load environment variables
set -a
source .env
set +a

print_status "Environment variables loaded"

# Use project-local virtual environment
if [ ! -d ".venv" ]; then
    print_warning "Virtual environment '.venv' not found. Creating and installing requirements..."
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
    print_status "Virtual environment '.venv' created and dependencies installed"
else
    print_status "Virtual environment '.venv' found"
    source .venv/bin/activate
fi

print_status "Virtual environment activated"

# Ensure logs directory exists
mkdir -p logs

# Start the system using manage_system.py
print_info "Starting the system..."
python manage_system.py start

if [ $? -eq 0 ]; then
    print_status "System deployed and started successfully!"
    print_info "Access the dashboard at: http://127.0.0.1:5001"
    print_info "Access Freqtrade at: http://127.0.0.1:8080"
else
    print_error "Failed to start the system"
    exit 1
fi