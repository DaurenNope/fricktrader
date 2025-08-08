# MVP Crypto Trading System

An automated cryptocurrency trading system built on Freqtrade with manual approval workflows and simplified user interaction.

## 🎯 Overview

This project is a comprehensive cryptocurrency trading system that combines algorithmic trading strategies with manual oversight. Built on top of Freqtrade, it includes multiple trading strategies, risk management features, and a web-based dashboard for monitoring and approval workflows.

## 🚀 Key Features

- **Multiple Trading Strategies**: Various strategies from simple to complex with different risk profiles
- **Manual Approval Workflow**: Safety mechanism requiring human approval for trades
- **Web Dashboard**: Real-time monitoring and control interface
- **Risk Management**: Built-in position sizing and stop-loss mechanisms
- **Backtesting Capabilities**: Test strategies against historical data
- **Market Analysis Tools**: Technical indicators and pattern recognition
- **Social Sentiment Analysis**: Integration with Twitter and Reddit for market sentiment
- **On-Chain Data Analysis**: Ethereum blockchain data integration

## 📁 Project Structure

```
trading_master/
├── config/                     # Configuration files for different strategies
├── src/                        # Source code
│   ├── approval/               # Manual approval system
│   ├── backtesting/            # Enhanced backtesting capabilities
│   ├── database/               # Database schemas and managers
│   ├── hedging/                # Advanced hedging mechanisms
│   ├── market_data/            # Market analysis tools
│   ├── onchain/                # Blockchain data analysis
│   ├── sentiment/              # Social sentiment analysis
│   ├── social_trading/         # Trader discovery and validation
│   └── web_ui/                 # Flask dashboard
├── user_data/                  # Freqtrade user data
│   └── strategies/             # Multiple trading strategies
├── scripts/                    # Utility scripts
├── tests/                      # Test suite
└── logs/                       # System logs
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Ubuntu/Debian Linux (recommended for TA-Lib installation)
- Internet connection for package downloads

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd trading_master
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv trading_env
   source trading_env/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install TA-Lib C library (Ubuntu/Debian):**
   ```bash
   sudo apt-get update
   sudo apt-get install build-essential wget
   wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
   tar -xzf ta-lib-0.4.0-src.tar.gz
   cd ta-lib/
   ./configure --prefix=/usr
   make
   sudo make install
   cd ../
   pip install TA-Lib
   ```

## ▶️ Quick Start

1. **Run a backtest with one of the strategies:**
   ```bash
   freqtrade backtesting --config config/config.json --strategy MultiSignalStrategy
   ```

2. **Start the web dashboard:**
   ```bash
   python start_dashboard.py
   ```

3. **Start the trading system:**
   ```bash
   ./start_trading_system.sh
   ```

## 📊 Available Strategies

- `MultiSignalStrategy` - Comprehensive strategy with multiple indicators
- `SimpleMultiSignalStrategy` - Simplified version of the main strategy
- `ConservativeMultiSignalStrategy` - Conservative approach with strict risk management
- `AdaptiveMultiSignalStrategy` - Market regime adaptive strategy
- `EnhancedOnChainStrategy` - Strategy incorporating on-chain data
- Several other specialized strategies

## 🧪 Testing

Run unit tests:
```bash
python -m pytest tests/unit
```

Run integration tests:
```bash
python -m pytest tests/integration
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

## 📧 Contact

Project Link: [https://github.com/yourusername/trading_master](https://github.com/yourusername/trading_master)