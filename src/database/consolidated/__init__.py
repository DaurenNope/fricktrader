"""
Database Package

This package contains modules for managing the trading system's data storage.
"""

# Version of the database package
__version__ = "1.0.0"

from .data_warehouse import DataWarehouse
# Import key classes for easier access
from .trade_logic_schema import TradeLogicDBManager

__all__ = [
    "TradeLogicDBManager",
    "DataWarehouse",
]
