"""
Unit tests for database components.

Tests DataWarehouse, trade decision capturing, and related
database functionality.
"""

import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch

import pandas as pd
import pytest

from src.database.data_warehouse import DataWarehouse
from src.database.trade_decision_capturer import TradeDecisionCapturer


class TestDataWarehouse:
    """Test suite for DataWarehouse class."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file for testing."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_file.close()
        yield temp_file.name
        # Cleanup
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

    @pytest.fixture
    def warehouse(self, temp_db_path):
        """Create DataWarehouse instance for testing."""
        return DataWarehouse(temp_db_path)

    @pytest.mark.unit
    def test_warehouse_initialization(self, temp_db_path):
        """Test DataWarehouse initialization."""
        warehouse = DataWarehouse(temp_db_path)

        assert warehouse.db_path == temp_db_path
        assert os.path.exists(temp_db_path)

        # Check that tables were created
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = ["ohlcv_data", "symbols", "data_quality_metrics"]
        for table in expected_tables:
            assert table in tables

        conn.close()

    @pytest.mark.unit
    def test_store_ohlcv_data_success(self, warehouse, sample_ohlcv_data):
        """Test successful OHLCV data storage."""
        symbol = "BTC/USDT"
        timeframe = "1h"

        # Store data
        warehouse.store_ohlcv_data(symbol, timeframe, sample_ohlcv_data)

        # Verify data was stored
        stored_data = warehouse.get_ohlcv_data(symbol, timeframe)

        assert len(stored_data) == len(sample_ohlcv_data)
        assert list(stored_data.columns) == list(sample_ohlcv_data.columns)

    @pytest.mark.unit
    def test_store_ohlcv_data_empty_dataframe(self, warehouse):
        """Test storing empty DataFrame."""
        empty_df = pd.DataFrame()

        with pytest.raises(ValueError, match="Cannot store empty DataFrame"):
            warehouse.store_ohlcv_data("BTC/USDT", "1h", empty_df)

    @pytest.mark.unit
    def test_get_ohlcv_data_with_limit(self, warehouse, sample_ohlcv_data):
        """Test retrieving OHLCV data with limit."""
        symbol = "BTC/USDT"
        timeframe = "1h"

        # Store data
        warehouse.store_ohlcv_data(symbol, timeframe, sample_ohlcv_data)

        # Get limited data
        limited_data = warehouse.get_ohlcv_data(symbol, timeframe, limit=10)

        assert len(limited_data) == 10
        # Should return most recent data first
        assert limited_data.iloc[0]["timestamp"] >= limited_data.iloc[-1]["timestamp"]

    @pytest.mark.unit
    def test_get_ohlcv_data_with_date_range(self, warehouse, sample_ohlcv_data):
        """Test retrieving OHLCV data with date range filter."""
        symbol = "BTC/USDT"
        timeframe = "1h"

        warehouse.store_ohlcv_data(symbol, timeframe, sample_ohlcv_data)

        # Get data within specific date range
        start_date = sample_ohlcv_data["timestamp"].iloc[10]
        end_date = sample_ohlcv_data["timestamp"].iloc[20]

        filtered_data = warehouse.get_ohlcv_data(
            symbol, timeframe, start_date=start_date, end_date=end_date
        )

        # All timestamps should be within range
        assert all(filtered_data["timestamp"] >= start_date)
        assert all(filtered_data["timestamp"] <= end_date)

    @pytest.mark.unit
    def test_get_ohlcv_data_nonexistent_symbol(self, warehouse):
        """Test retrieving data for non-existent symbol."""
        result = warehouse.get_ohlcv_data("NONEXISTENT/PAIR", "1h")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @pytest.mark.unit
    def test_get_available_symbols(self, warehouse, sample_ohlcv_data):
        """Test getting list of available symbols."""
        # Initially empty
        symbols = warehouse.get_available_symbols()
        assert len(symbols) == 0

        # Store data for multiple symbols
        symbols_to_store = ["BTC/USDT", "ETH/USDT", "ADA/USDT"]
        for symbol in symbols_to_store:
            warehouse.store_ohlcv_data(symbol, "1h", sample_ohlcv_data)

        # Should return all stored symbols
        available_symbols = warehouse.get_available_symbols()
        assert len(available_symbols) == len(symbols_to_store)
        for symbol in symbols_to_store:
            assert symbol in available_symbols

    @pytest.mark.unit
    def test_get_symbol_info(self, warehouse, sample_ohlcv_data):
        """Test getting symbol information."""
        symbol = "BTC/USDT"
        timeframe = "1h"

        warehouse.store_ohlcv_data(symbol, timeframe, sample_ohlcv_data)

        info = warehouse.get_symbol_info(symbol)

        assert info["symbol"] == symbol
        assert "total_records" in info
        assert "earliest_date" in info
        assert "latest_date" in info
        assert "available_timeframes" in info

        assert info["total_records"] > 0
        assert info["available_timeframes"] == [timeframe]

    @pytest.mark.unit
    def test_store_data_quality_metrics(self, warehouse):
        """Test storing data quality metrics."""
        symbol = "BTC/USDT"
        metrics = {
            "overall_score": 85.5,
            "completeness": 95.0,
            "consistency": 88.2,
            "continuity": 92.1,
            "anomaly_count": 3,
        }

        warehouse.store_data_quality_metrics(symbol, metrics)

        # Verify metrics were stored
        stored_metrics = warehouse.get_data_quality_metrics(symbol)

        assert stored_metrics["symbol"] == symbol
        assert stored_metrics["overall_score"] == metrics["overall_score"]
        assert stored_metrics["completeness"] == metrics["completeness"]

    @pytest.mark.unit
    def test_update_existing_data(self, warehouse, sample_ohlcv_data):
        """Test updating existing OHLCV data."""
        symbol = "BTC/USDT"
        timeframe = "1h"

        # Store initial data
        warehouse.store_ohlcv_data(symbol, timeframe, sample_ohlcv_data.iloc[:50])

        initial_count = len(warehouse.get_ohlcv_data(symbol, timeframe))
        assert initial_count == 50

        # Store overlapping data (should handle duplicates)
        warehouse.store_ohlcv_data(symbol, timeframe, sample_ohlcv_data.iloc[25:75])

        updated_count = len(warehouse.get_ohlcv_data(symbol, timeframe))

        # Should have more data but not exactly 50 + 50 due to overlap handling
        assert updated_count > initial_count
        assert updated_count <= 75

    @pytest.mark.unit
    def test_database_connection_error_handling(self, warehouse):
        """Test handling of database connection errors."""
        # Corrupt the database path to cause connection errors
        warehouse.db_path = "/invalid/path/database.db"

        # Should handle connection errors gracefully
        with pytest.raises((sqlite3.Error, FileNotFoundError)):
            warehouse.get_ohlcv_data("BTC/USDT", "1h")

    @pytest.mark.unit
    def test_get_database_info(self, warehouse, sample_ohlcv_data):
        """Test getting database information."""
        # Store some data first
        warehouse.store_ohlcv_data("BTC/USDT", "1h", sample_ohlcv_data)
        warehouse.store_ohlcv_data("ETH/USDT", "1h", sample_ohlcv_data)

        db_info = warehouse.get_database_info()

        assert "total_symbols" in db_info
        assert "total_records" in db_info
        assert "database_size_mb" in db_info
        assert "oldest_record" in db_info
        assert "newest_record" in db_info

        assert db_info["total_symbols"] == 2
        assert db_info["total_records"] > 0


class TestTradeDecisionCapturer:
    """Test suite for TradeDecisionCapturer class."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file for testing."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_file.close()
        yield temp_file.name
        # Cleanup
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

    @pytest.fixture
    def capturer(self, temp_db_path):
        """Create TradeDecisionCapturer instance for testing."""
        return TradeDecisionCapturer(temp_db_path)

    @pytest.mark.unit
    def test_capturer_initialization(self, temp_db_path):
        """Test TradeDecisionCapturer initialization."""
        capturer = TradeDecisionCapturer(temp_db_path)

        assert capturer.db_path == temp_db_path
        assert os.path.exists(temp_db_path)

        # Check that trade decisions table was created
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='trade_decisions';"
        )
        result = cursor.fetchone()

        assert result is not None
        conn.close()

    @pytest.mark.unit
    def test_capture_trade_decision_buy(self, capturer):
        """Test capturing a buy trade decision."""
        decision_data = {
            "symbol": "BTC/USDT",
            "action": "BUY",
            "price": 45000.0,
            "quantity": 0.1,
            "confidence_score": 0.85,
            "strategy_name": "TestStrategy",
            "reasoning": {
                "technical_indicators": {"rsi": 25, "macd_signal": "bullish"},
                "market_conditions": "oversold",
                "risk_factors": ["high_volatility"],
            },
        }

        decision_id = capturer.capture_decision(decision_data)

        assert decision_id is not None
        assert isinstance(decision_id, int)

        # Verify decision was stored
        stored_decision = capturer.get_decision(decision_id)
        assert stored_decision["symbol"] == decision_data["symbol"]
        assert stored_decision["action"] == decision_data["action"]
        assert stored_decision["price"] == decision_data["price"]

    @pytest.mark.unit
    def test_capture_trade_decision_sell(self, capturer):
        """Test capturing a sell trade decision."""
        decision_data = {
            "symbol": "ETH/USDT",
            "action": "SELL",
            "price": 3200.0,
            "quantity": 2.5,
            "confidence_score": 0.92,
            "strategy_name": "MomentumStrategy",
            "reasoning": {
                "technical_indicators": {"rsi": 78, "macd_signal": "bearish"},
                "market_conditions": "overbought",
                "profit_target_reached": True,
            },
        }

        decision_id = capturer.capture_decision(decision_data)

        # Verify decision was stored correctly
        stored_decision = capturer.get_decision(decision_id)
        assert stored_decision["action"] == "SELL"
        assert stored_decision["confidence_score"] == 0.92

    @pytest.mark.unit
    def test_get_decisions_by_symbol(self, capturer):
        """Test retrieving decisions by symbol."""
        # Capture decisions for different symbols
        btc_decision = {
            "symbol": "BTC/USDT",
            "action": "BUY",
            "price": 45000.0,
            "quantity": 0.1,
            "confidence_score": 0.8,
            "strategy_name": "TestStrategy",
            "reasoning": {},
        }

        eth_decision = {
            "symbol": "ETH/USDT",
            "action": "SELL",
            "price": 3200.0,
            "quantity": 1.0,
            "confidence_score": 0.9,
            "strategy_name": "TestStrategy",
            "reasoning": {},
        }

        capturer.capture_decision(btc_decision)
        capturer.capture_decision(eth_decision)
        capturer.capture_decision(btc_decision)  # Another BTC decision

        # Get BTC decisions only
        btc_decisions = capturer.get_decisions_by_symbol("BTC/USDT")
        assert len(btc_decisions) == 2
        for decision in btc_decisions:
            assert decision["symbol"] == "BTC/USDT"

        # Get ETH decisions only
        eth_decisions = capturer.get_decisions_by_symbol("ETH/USDT")
        assert len(eth_decisions) == 1
        assert eth_decisions[0]["symbol"] == "ETH/USDT"

    @pytest.mark.unit
    def test_get_decisions_by_date_range(self, capturer):
        """Test retrieving decisions within date range."""
        decision_data = {
            "symbol": "BTC/USDT",
            "action": "BUY",
            "price": 45000.0,
            "quantity": 0.1,
            "confidence_score": 0.8,
            "strategy_name": "TestStrategy",
            "reasoning": {},
        }

        # Capture some decisions
        for i in range(5):
            capturer.capture_decision(decision_data)

        # Get decisions from last hour
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)

        recent_decisions = capturer.get_decisions_by_date_range(start_time, end_time)
        assert len(recent_decisions) == 5

    @pytest.mark.unit
    def test_update_decision_status(self, capturer):
        """Test updating decision status (e.g., after execution)."""
        decision_data = {
            "symbol": "BTC/USDT",
            "action": "BUY",
            "price": 45000.0,
            "quantity": 0.1,
            "confidence_score": 0.8,
            "strategy_name": "TestStrategy",
            "reasoning": {},
        }

        decision_id = capturer.capture_decision(decision_data)

        # Update status to executed
        update_data = {
            "status": "EXECUTED",
            "executed_price": 44950.0,
            "executed_quantity": 0.1,
            "execution_time": datetime.now(),
            "fees": 2.25,
        }

        success = capturer.update_decision_status(decision_id, update_data)
        assert success is True

        # Verify update
        updated_decision = capturer.get_decision(decision_id)
        assert updated_decision["status"] == "EXECUTED"
        assert updated_decision["executed_price"] == 44950.0

    @pytest.mark.unit
    def test_get_decision_statistics(self, capturer):
        """Test getting decision statistics."""
        # Capture various decisions
        decisions = [
            {
                "symbol": "BTC/USDT",
                "action": "BUY",
                "price": 45000,
                "quantity": 0.1,
                "confidence_score": 0.8,
                "strategy_name": "Strategy1",
                "reasoning": {},
            },
            {
                "symbol": "BTC/USDT",
                "action": "SELL",
                "price": 46000,
                "quantity": 0.1,
                "confidence_score": 0.9,
                "strategy_name": "Strategy1",
                "reasoning": {},
            },
            {
                "symbol": "ETH/USDT",
                "action": "BUY",
                "price": 3200,
                "quantity": 1.0,
                "confidence_score": 0.7,
                "strategy_name": "Strategy2",
                "reasoning": {},
            },
        ]

        for decision in decisions:
            capturer.capture_decision(decision)

        stats = capturer.get_decision_statistics()

        assert "total_decisions" in stats
        assert "buy_count" in stats
        assert "sell_count" in stats
        assert "avg_confidence_score" in stats
        assert "symbols_traded" in stats
        assert "strategies_used" in stats

        assert stats["total_decisions"] == 3
        assert stats["buy_count"] == 2
        assert stats["sell_count"] == 1

    @pytest.mark.unit
    def test_invalid_decision_data(self, capturer):
        """Test handling of invalid decision data."""
        invalid_decision = {
            "symbol": "",  # Empty symbol
            "action": "INVALID_ACTION",
            "price": -100,  # Negative price
            "quantity": 0,  # Zero quantity
            "confidence_score": 1.5,  # Invalid confidence score
        }

        with pytest.raises(ValueError):
            capturer.capture_decision(invalid_decision)

    @pytest.mark.unit
    def test_get_nonexistent_decision(self, capturer):
        """Test getting a decision that doesn't exist."""
        result = capturer.get_decision(99999)  # Non-existent ID
        assert result is None

    @pytest.mark.unit
    @patch("src.database.trade_decision_capturer.logger")
    def test_logging_on_successful_capture(self, mock_logger, capturer):
        """Test that successful decision captures are logged."""
        decision_data = {
            "symbol": "BTC/USDT",
            "action": "BUY",
            "price": 45000.0,
            "quantity": 0.1,
            "confidence_score": 0.8,
            "strategy_name": "TestStrategy",
            "reasoning": {},
        }

        capturer.capture_decision(decision_data)

        # Verify info log was called
        mock_logger.info.assert_called()

        # Verify success message was logged
        log_calls = mock_logger.info.call_args_list
        success_logged = any("captured" in str(call).lower() for call in log_calls)
        assert success_logged
