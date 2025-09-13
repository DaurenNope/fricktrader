"""
Data Package

This package contains modules for managing market data in the trading system.
"""

# Version of the data package
__version__ = "1.0.0"

from .data_validator import DataValidator
from .historical_data_manager import HistoricalDataManager
# Import key classes for easier access
from .market_data_manager import MarketDataManager
from .real_time_feeds import RealTimeFeedsManager, WebSocketFeed

__all__ = [
    "MarketDataManager",
    "DataValidator",
    "RealTimeFeedsManager",
    "WebSocketFeed",
    "HistoricalDataManager",
]
