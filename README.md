# fricktrader

> **Algorithmic crypto trading bot with real-time dashboard.** Strategy execution, portfolio tracking, and live P&L — automated.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black)
![Freqtrade](https://img.shields.io/badge/Freqtrade-Compatible-blue?style=flat)
![Status](https://img.shields.io/badge/Status-Active_Development-orange?style=flat)

---

## What it does

fricktrader is an algorithmic trading system built for crypto markets. It runs automated trading strategies with a real-time web dashboard for monitoring positions, P&L, and execution history.

Because manually watching charts is a great way to lose money and sleep simultaneously.

---

## Architecture

```mermaid
graph TB
    subgraph Exchange["Exchange Layer"]
        EX[Exchange API]
        WS[WebSocket Feed]
    end

    subgraph Core["Trading Engine"]
        ST[Strategy Runner]
        RM[Risk Manager]
        OM[Order Manager]
    end

    subgraph Data["Data Layer"]
        DB[(Local DB)]
        CONF[Config Files]
    end

    subgraph Dashboard["Dashboard"]
        UI[Web UI]
        API[REST API]
    end

    WS --> ST
    ST --> RM
    RM --> OM
    OM --> EX
    EX --> DB
    DB --> API
    API --> UI
    CONF --> ST
```

---

## Features

- **Strategy execution** — Configurable trading strategies with Freqtrade-compatible architecture
- **Real-time dashboard** — Live P&L, open positions, trade history
- **Risk management** — Position sizing, stop-loss, take-profit controls
- **Multi-strategy** — Run and compare multiple strategies simultaneously
- **Local state** — Full trade history stored locally, no third-party dependency

---

## Quick Start

```bash
git clone https://github.com/DaurenNope/fricktrader
cd fricktrader
pip install -r requirements.txt

# Configure your exchange and strategy
cp config/config.example.json config/config.json
# Add your API keys and strategy parameters

# Start the dashboard
python main_dashboard.py

# Or use the start script
bash start.sh
```

Dashboard runs at: http://localhost:8080

---

## Project Structure

```
src/                  # Core trading engine
config/               # Strategy configs and exchange settings
user_data/strategies/ # Trading strategy implementations
scripts/              # Utility and setup scripts
archive/              # Previous strategy versions
main_dashboard.py     # Dashboard entry point
```

---

## Stack

- **Python** — Trading engine and data processing
- **JavaScript/HTML** — Real-time dashboard UI
- **Freqtrade** — Strategy framework compatibility
- **REST API** — Dashboard data layer

---

> ⚠️ This is personal trading software. Use at your own risk. Past performance does not guarantee future results.

---

Built by [@DaurenNope](https://github.com/DaurenNope) · [rahmetlabs.com](https://rahmetlabs.com)
