"""
FrickTrader - Professional Cryptocurrency Trading System

A comprehensive trading platform with multi-signal analysis,
risk management, and automated execution capabilities.

Author: FrickTrader Team
Version: 2.0.0
"""

__version__ = "2.0.0"
__author__ = "FrickTrader Team"
__description__ = "Professional Cryptocurrency Trading System"

# Core package imports
from . import (approval, database, market_data, onchain, sentiment,
               social_trading, web_ui)

__all__ = [
    "approval",
    "database",
    "market_data",
    "onchain",
    "sentiment",
    "social_trading",
    "web_ui",
]
