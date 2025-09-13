"""
Unit tests for MarketDataManager class.

Tests market data fetching, caching, validation,
and error handling functionality.
"""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.data.exceptions import (DataNotAvailableError,
                                 ExchangeConnectionError, InvalidSymbolError)
from src.data.market_data_manager import MarketDataManager


class TestMarketDataManager:
    """Test suite for MarketDataManager class."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def manager_config(self, temp_data_dir):
        """Configuration for MarketDataManager testing."""
        return {
            "exchange": {
                "name": "binance",
                "sandbox": True,
                "enableRateLimit": True,
                "timeout": 30000,
            },
            "cache_size": 100,
            "cache_ttl_seconds": 60,
            "rate_limit_delay": 0.01,  # Faster for testing
            "data_dir": str(temp_data_dir),
            "validation": {"max_gap_minutes": 60, "max_price_change_pct": 20.0},
        }

    @pytest.fixture
    def mock_manager(self, manager_config, mock_exchange):
        """Create MarketDataManager with mocked exchange."""
        with patch("src.data.market_data_manager.ccxt.binance") as mock_binance:
            mock_binance.return_value = mock_exchange
            manager = MarketDataManager(manager_config)
            return manager

    @pytest.mark.unit
    def test_manager_initialization_success(self, manager_config, mock_exchange):
        """Test successful MarketDataManager initialization."""
        with patch("src.data.market_data_manager.ccxt.binance") as mock_binance:
            mock_binance.return_value = mock_exchange

            manager = MarketDataManager(manager_config)

            assert manager.exchange is not None
            assert manager.validator is not None
            assert manager.cache is not None
            assert manager.data_dir.exists()

    @pytest.mark.unit
    def test_manager_initialization_default_config(self):
        """Test MarketDataManager initialization with default config."""
        with patch("src.data.market_data_manager.ccxt.binance") as mock_binance:
            mock_binance.return_value = Mock()
            mock_binance.return_value.load_markets.return_value = {}

            manager = MarketDataManager()

            assert manager.exchange_config["name"] == "binance"
            assert manager.exchange_config["sandbox"] is True

    @pytest.mark.unit
    def test_fetch_real_time_data_success(self, mock_manager):
        """Test successful real-time data fetching."""
        symbol = "BTC/USDT"
        timeframe = "1h"

        result = mock_manager.fetch_real_time_data(symbol, timeframe, limit=10)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 10
        assert all(
            col in result.columns
            for col in ["timestamp", "open", "high", "low", "close", "volume"]
        )

        # Verify exchange was called
        mock_manager.exchange.fetch_ohlcv.assert_called_with(
            symbol, timeframe, limit=10
        )

    @pytest.mark.unit
    def test_fetch_real_time_data_invalid_symbol(self, mock_manager):
        """Test real-time data fetching with invalid symbol."""
        invalid_symbol = "INVALID"

        with pytest.raises(InvalidSymbolError):
            mock_manager.fetch_real_time_data(invalid_symbol)

    @pytest.mark.unit
    def test_fetch_real_time_data_no_data(self, mock_manager):
        """Test real-time data fetching when no data available."""
        mock_manager.exchange.fetch_ohlcv.return_value = []

        with pytest.raises(DataNotAvailableError, match="No data available"):
            mock_manager.fetch_real_time_data("BTC/USDT")

    @pytest.mark.unit
    def test_fetch_real_time_data_caching(self, mock_manager):
        """Test that real-time data is cached properly."""
        symbol = "BTC/USDT"
        timeframe = "1h"

        # First call
        result1 = mock_manager.fetch_real_time_data(symbol, timeframe, limit=10)

        # Second call should use cache
        result2 = mock_manager.fetch_real_time_data(symbol, timeframe, limit=10)

        # Should be the same data
        pd.testing.assert_frame_equal(result1, result2)

        # Exchange should only be called once (first call)
        assert mock_manager.exchange.fetch_ohlcv.call_count == 1

    @pytest.mark.unit
    def test_fetch_historical_data_success(self, mock_manager):
        """Test successful historical data fetching."""
        symbol = "BTC/USDT"
        timeframe = "1d"
        start_date = datetime(2024, 1, 1)

        result = mock_manager.fetch_historical_data(
            symbol, timeframe, start_date=start_date, limit=30
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert all(
            col in result.columns
            for col in ["timestamp", "open", "high", "low", "close", "volume"]
        )

    @pytest.mark.unit
    def test_fetch_historical_data_with_date_filter(self, mock_manager):
        """Test historical data fetching with end date filter."""
        symbol = "BTC/USDT"
        timeframe = "1h"
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)

        result = mock_manager.fetch_historical_data(
            symbol, timeframe, start_date=start_date, end_date=end_date, limit=100
        )

        assert isinstance(result, pd.DataFrame)
        # All timestamps should be before end_date
        if not result.empty:
            assert all(result["timestamp"] <= end_date)

    @pytest.mark.unit
    def test_get_available_symbols_success(self, mock_manager):
        """Test getting available symbols."""
        symbols = mock_manager.get_available_symbols()

        assert isinstance(symbols, list)
        assert "BTC/USDT" in symbols
        assert "ETH/USDT" in symbols
        assert len(symbols) > 0

    @pytest.mark.unit
    def test_get_symbol_info_success(self, mock_manager):
        """Test getting symbol information."""
        symbol = "BTC/USDT"

        info = mock_manager.get_symbol_info(symbol)

        assert isinstance(info, dict)
        assert info["symbol"] == symbol
        assert "base" in info
        assert "quote" in info
        assert "current_price" in info
        assert "volume_24h" in info

    @pytest.mark.unit
    def test_get_symbol_info_invalid_symbol(self, mock_manager):
        """Test getting info for invalid symbol."""
        with pytest.raises(InvalidSymbolError):
            mock_manager.get_symbol_info("INVALID/SYMBOL")

    @pytest.mark.unit
    def test_data_quality_report_generation(self, mock_manager):
        """Test data quality report generation."""
        symbol = "BTC/USDT"

        report = mock_manager.get_data_quality_report(symbol)

        assert isinstance(report, dict)
        assert "symbol" in report
        assert report["symbol"] == symbol

    @pytest.mark.unit
    def test_cache_operations(self, mock_manager):
        """Test cache operations."""
        # Test cache info
        cache_info = mock_manager.get_cached_data_info()
        assert isinstance(cache_info, dict)
        assert "cache_size" in cache_info

        # Test cache clearing
        mock_manager.clear_cache()
        cache_info_after = mock_manager.get_cached_data_info()
        assert cache_info_after["cache_size"] == 0

    @pytest.mark.unit
    def test_system_status(self, mock_manager):
        """Test system status reporting."""
        status = mock_manager.get_system_status()

        assert isinstance(status, dict)
        assert "timestamp" in status
        assert "exchange" in status
        assert "cache" in status
        assert "data_dir" in status

        # Exchange should be connected
        assert status["exchange"]["connected"] is True

    @pytest.mark.unit
    def test_rate_limiting(self, mock_manager):
        """Test rate limiting functionality."""
        import time

        # Record start time
        start_time = time.time()

        # Make multiple requests
        for i in range(3):
            mock_manager._enforce_rate_limit()

        # Should have taken at least some time due to rate limiting
        elapsed = time.time() - start_time
        expected_min_time = 2 * mock_manager.rate_limit_delay  # 2 delays for 3 calls

        assert elapsed >= expected_min_time

    @pytest.mark.unit
    def test_convert_ohlcv_to_dataframe(self, mock_manager):
        """Test OHLCV data conversion to DataFrame."""
        # Mock OHLCV data from exchange
        raw_ohlcv = [
            [1640995200000, 47000.0, 47500.0, 46500.0, 47200.0, 1234.56],
            [1640998800000, 47200.0, 47800.0, 46800.0, 47600.0, 2345.67],
        ]

        df = mock_manager._convert_ohlcv_to_dataframe(raw_ohlcv)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

        # Check data types
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
        assert pd.api.types.is_numeric_dtype(df["open"])
        assert pd.api.types.is_numeric_dtype(df["volume"])

    @pytest.mark.unit
    def test_convert_empty_ohlcv(self, mock_manager):
        """Test conversion of empty OHLCV data."""
        df = mock_manager._convert_ohlcv_to_dataframe([])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    @pytest.mark.unit
    @patch.dict(
        "os.environ",
        {"BINANCE_API_KEY": "test_key", "BINANCE_API_SECRET": "test_secret"},
    )
    def test_initialization_with_api_credentials(self, manager_config):
        """Test initialization with API credentials from environment."""
        with patch("src.data.market_data_manager.ccxt.binance") as mock_binance:
            mock_exchange = Mock()
            mock_exchange.load_markets.return_value = {}
            mock_binance.return_value = mock_exchange

            manager = MarketDataManager(manager_config)

            # Verify exchange was initialized with credentials
            mock_binance.assert_called_once()
            call_args = mock_binance.call_args[0][0]
            assert "apiKey" in call_args
            assert "secret" in call_args
            assert call_args["apiKey"] == "test_key"
            assert call_args["secret"] == "test_secret"

    @pytest.mark.unit
    def test_exchange_connection_error(self, manager_config):
        """Test handling of exchange connection errors."""
        with patch("src.data.market_data_manager.ccxt.binance") as mock_binance:
            mock_binance.side_effect = Exception("Connection failed")

            with pytest.raises(ExchangeConnectionError):
                MarketDataManager(manager_config)

    @pytest.mark.unit
    def test_exchange_network_error_handling(self, mock_manager):
        """Test handling of network errors during data fetching."""
        import ccxt

        mock_manager.exchange.fetch_ohlcv.side_effect = ccxt.NetworkError(
            "Network timeout"
        )

        with pytest.raises(ExchangeConnectionError, match="Network error"):
            mock_manager.fetch_real_time_data("BTC/USDT")

    @pytest.mark.unit
    def test_exchange_error_handling(self, mock_manager):
        """Test handling of exchange errors during data fetching."""
        import ccxt

        mock_manager.exchange.fetch_ohlcv.side_effect = ccxt.ExchangeError(
            "Invalid symbol"
        )

        with pytest.raises(DataNotAvailableError, match="Exchange error"):
            mock_manager.fetch_real_time_data("BTC/USDT")

    @pytest.mark.unit
    def test_cache_error_handling(self, mock_manager):
        """Test graceful handling of cache errors."""
        # Mock cache to raise errors
        mock_manager.cache.get = Mock(side_effect=Exception("Cache error"))
        mock_manager.cache.__setitem__ = Mock(side_effect=Exception("Cache error"))

        # Should still work despite cache errors
        result = mock_manager.fetch_real_time_data("BTC/USDT", limit=5)
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.unit
    def test_data_persistence(self, mock_manager, temp_data_dir):
        """Test historical data persistence to files."""
        symbol = "BTC/USDT"
        timeframe = "1h"

        # Fetch data (should trigger file save)
        mock_manager.fetch_historical_data(symbol, timeframe, limit=10)

        # Check if data directory was created
        symbol_dir = temp_data_dir / symbol.replace("/", "_")
        assert symbol_dir.exists()

        # Check if parquet file was created
        parquet_files = list(symbol_dir.glob("*.parquet"))
        assert len(parquet_files) > 0

    @pytest.mark.unit
    def test_file_save_error_handling(self, mock_manager):
        """Test graceful handling of file save errors."""
        # Mock pathlib to raise errors
        with patch("pathlib.Path.mkdir", side_effect=Exception("Permission denied")):
            # Should not raise error, just log warning
            result = mock_manager.fetch_historical_data("BTC/USDT", limit=5)
            assert isinstance(result, pd.DataFrame)

    @pytest.mark.unit
    @patch("src.data.market_data_manager.logger")
    def test_logging_on_successful_fetch(self, mock_logger, mock_manager):
        """Test that successful data fetches are logged."""
        mock_manager.fetch_real_time_data("BTC/USDT", limit=5)

        # Check that info log was called
        mock_logger.info.assert_called()

        # Verify success message was logged
        log_calls = mock_logger.info.call_args_list
        success_logged = any("✅" in str(call) for call in log_calls)
        assert success_logged

    @pytest.mark.unit
    @patch("src.data.market_data_manager.logger")
    def test_logging_on_error(self, mock_logger, mock_manager):
        """Test that errors are properly logged."""
        mock_manager.exchange.fetch_ohlcv.side_effect = Exception("Test error")

        with pytest.raises(Exception):
            mock_manager.fetch_real_time_data("BTC/USDT")

        # Error should be logged
        mock_logger.error.assert_called()

    @pytest.mark.unit
    def test_manager_without_exchange_initialization(self, manager_config):
        """Test manager behavior when exchange fails to initialize."""
        with patch("src.data.market_data_manager.ccxt.binance") as mock_binance:
            mock_binance.side_effect = Exception("Exchange init failed")

            with pytest.raises(ExchangeConnectionError):
                MarketDataManager(manager_config)
