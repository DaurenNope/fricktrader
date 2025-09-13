"""
Unit tests for data infrastructure components.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.data.historical_data_manager import HistoricalDataManager
from src.data.real_time_feeds import RealTimeFeedsManager, WebSocketFeed
from src.database.data_warehouse import DataWarehouse


class TestDataInfrastructure(unittest.TestCase):
    """Test cases for data infrastructure components."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "exchange": {"name": "binance", "enableRateLimit": True},
            "rate_limit_delay": 0.01,
        }

    def test_websocket_feed_initialization(self):
        """Test WebSocketFeed initialization."""
        with patch("src.data.real_time_feeds.ccxt") as mock_ccxt:
            # Mock the exchange class
            mock_exchange_class = Mock()
            mock_exchange_instance = Mock()
            mock_exchange_class.return_value = mock_exchange_instance
            mock_ccxt.binance = mock_exchange_class

            # Create WebSocketFeed instance
            feed = WebSocketFeed(self.config)

            # Verify initialization
            self.assertIsNotNone(feed.exchange)
            mock_ccxt.binance.assert_called_once()

    def test_real_time_feeds_manager_initialization(self):
        """Test RealTimeFeedsManager initialization."""
        manager = RealTimeFeedsManager(self.config)
        self.assertEqual(manager.config, self.config)
        self.assertEqual(manager.feeds, {})

    def test_historical_data_manager_initialization(self):
        """Test HistoricalDataManager initialization."""
        with patch("src.data.historical_data_manager.ccxt") as mock_ccxt:
            # Mock the exchange class
            mock_exchange_class = Mock()
            mock_exchange_instance = Mock()
            mock_exchange_class.return_value = mock_exchange_instance
            mock_ccxt.binance = mock_exchange_class

            # Create HistoricalDataManager instance
            manager = HistoricalDataManager(self.config)

            # Verify initialization
            self.assertIsNotNone(manager.exchange)
            mock_ccxt.binance.assert_called_once()

    def test_data_warehouse_initialization(self):
        """Test DataWarehouse initialization."""
        # Use a test database path
        test_db_path = "test_warehouse.db"

        # Create DataWarehouse instance
        warehouse = DataWarehouse(test_db_path)

        # Verify initialization
        self.assertEqual(warehouse.db_path, test_db_path)

        # Clean up test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)


if __name__ == "__main__":
    unittest.main()
