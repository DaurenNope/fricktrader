# Makefile for MVP Crypto Trading System

# Variables
PYTHON := python3
PIP := pip
VENV := .venv
ACTIVATE := source $(VENV)/bin/activate

# Default target
.PHONY: help
help:
	@echo "MVP Crypto Trading System - Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make setup              - Set up the development environment"
	@echo "  make install            - Install dependencies"
	@echo "  make test               - Run all tests"
	@echo "  make test-unit          - Run unit tests"
	@echo "  make test-integration   - Run integration tests"
	@echo "  make clean              - Clean up temporary files"
	@echo "  make dashboard          - Start the web dashboard"
	@echo "  make backtest           - Run a sample backtest"
	@echo "  make lint               - Run code linting"
	@echo "  make format             - Format code with black"
	@echo "  help                    - Show this help message"

# Set up development environment
.PHONY: setup
setup:
	$(PYTHON) -m venv $(VENV)
	$(ACTIVATE) && $(PIP) install --upgrade pip
	$(ACTIVATE) && $(PIP) install -r requirements.txt

# Install dependencies
.PHONY: install
install:
	$(PIP) install -r requirements.txt

# Run all tests
.PHONY: test
test:
	$(PYTHON) -m pytest tests/

# Run unit tests
.PHONY: test-unit
test-unit:
	$(PYTHON) -m pytest tests/unit

# Run integration tests
.PHONY: test-integration
test-integration:
	$(PYTHON) -m pytest tests/integration

# Clean up temporary files
.PHONY: clean
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

# Start the web dashboard
.PHONY: dashboard
dashboard:
	$(PYTHON) start_dashboard.py

# Run a sample backtest
.PHONY: backtest
backtest:
	$(PYTHON) -m freqtrade backtesting --config config/config.json --strategy MultiSignalStrategy

# Run code linting
.PHONY: lint
lint:
	flake8 src/ user_data/strategies/
	pylint src/ user_data/strategies/

# Format code with black
.PHONY: format
format:
	black src/ user_data/strategies/ tests/

# Initialize git repository
.PHONY: init-git
init-git:
	git init
	git add .
	git commit -m "Initial commit: MVP Crypto Trading System"