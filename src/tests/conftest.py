"""
Pytest configuration and shared fixtures.

Provides common test fixtures and configuration for the entire test suite.
"""

import os
from datetime import datetime
from unittest.mock import Mock

import pandas as pd
import pytest

# Set test environment variables
os.environ["TESTING"] = "true"


@pytest.fixture
def sample_ohlcv_data():
    """Sample OHLCV data for testing."""
    dates = pd.date_range("2024-01-01", periods=100, freq="1H")

    # Generate realistic OHLCV data
    base_price = 50000
    data = []

    for i, date in enumerate(dates):
        # Simple random walk for realistic price movement
        change = (hash(str(date)) % 200 - 100) / 10000  # -1% to +1% change
        base_price *= 1 + change

        # OHLC with realistic relationships
        open_price = base_price
        close_price = base_price * (1 + change)
        high_price = max(open_price, close_price) * (
            1 + abs(hash(str(date)) % 50) / 50000
        )
        low_price = min(open_price, close_price) * (
            1 - abs(hash(str(date)) % 50) / 50000
        )
        volume = 1000 + (hash(str(date)) % 5000)

        data.append(
            {
                "timestamp": date,
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": volume,
            }
        )

    return pd.DataFrame(data)


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "exchange": {
            "name": "binance",
            "sandbox": True,
            "enableRateLimit": True,
            "timeout": 30000,
        },
        "cache_size": 100,
        "cache_ttl_seconds": 60,
        "rate_limit_delay": 0.1,
        "validation": {
            "max_gap_minutes": 60,
            "max_price_change_pct": 20.0,
            "min_volume_threshold": 100.0,
            "max_spread_pct": 5.0,
        },
        "data_dir": "test_data",
    }


@pytest.fixture
def mock_exchange():
    """Mock exchange for testing."""
    exchange = Mock()

    # Mock markets
    exchange.markets = {
        "BTC/USDT": {
            "base": "BTC",
            "quote": "USDT",
            "active": True,
            "type": "spot",
            "spot": True,
            "future": False,
            "precision": {"amount": 8, "price": 2},
            "limits": {
                "amount": {"min": 0.001, "max": 9000},
                "price": {"min": 0.01, "max": 1000000},
            },
        },
        "ETH/USDT": {
            "base": "ETH",
            "quote": "USDT",
            "active": True,
            "type": "spot",
            "spot": True,
            "future": False,
            "precision": {"amount": 8, "price": 2},
            "limits": {
                "amount": {"min": 0.001, "max": 9000},
                "price": {"min": 0.01, "max": 1000000},
            },
        },
    }

    # Mock load_markets
    exchange.load_markets.return_value = exchange.markets

    # Mock fetch_ohlcv
    def mock_fetch_ohlcv(symbol, timeframe, since=None, limit=None):
        # Generate mock OHLCV data
        dates = pd.date_range("2024-01-01", periods=limit or 100, freq="1H")
        ohlcv = []
        base_price = 50000 if symbol == "BTC/USDT" else 3000

        for date in dates:
            timestamp = int(date.timestamp() * 1000)
            ohlcv.append(
                [
                    timestamp,
                    base_price,
                    base_price * 1.01,
                    base_price * 0.99,
                    base_price * 1.005,
                    1000 + (hash(str(date)) % 5000),
                ]
            )

        return ohlcv

    exchange.fetch_ohlcv.side_effect = mock_fetch_ohlcv

    # Mock fetch_ticker
    def mock_fetch_ticker(symbol):
        return {
            "symbol": symbol,
            "last": 50000 if symbol == "BTC/USDT" else 3000,
            "baseVolume": 1000000,
            "percentage": 2.5,
            "high": 51000 if symbol == "BTC/USDT" else 3100,
            "low": 49000 if symbol == "BTC/USDT" else 2900,
        }

    exchange.fetch_ticker.side_effect = mock_fetch_ticker

    return exchange


@pytest.fixture
def invalid_ohlcv_data():
    """Invalid OHLCV data for testing validation."""
    return pd.DataFrame(
        [
            {
                "timestamp": datetime(2024, 1, 1),
                "open": 100,
                "high": 90,  # Invalid: high < open
                "low": 105,  # Invalid: low > open
                "close": 95,
                "volume": -50,  # Invalid: negative volume
            },
            {
                "timestamp": datetime(2024, 1, 1, 1),
                "open": 0,  # Invalid: zero price
                "high": 0,
                "low": 0,
                "close": 0,
                "volume": 1000,
            },
        ]
    )


@pytest.fixture
def data_with_gaps():
    """OHLCV data with time gaps for testing."""
    data = []

    # Normal data
    dates1 = pd.date_range("2024-01-01", "2024-01-01 05:00", freq="1H")
    for date in dates1:
        data.append(
            {
                "timestamp": date,
                "open": 50000,
                "high": 50100,
                "low": 49900,
                "close": 50050,
                "volume": 1000,
            }
        )

    # Gap of 10 hours

    # More data after gap
    dates2 = pd.date_range("2024-01-01 15:00", "2024-01-01 20:00", freq="1H")
    for date in dates2:
        data.append(
            {
                "timestamp": date,
                "open": 50000,
                "high": 50100,
                "low": 49900,
                "close": 50050,
                "volume": 1000,
            }
        )

    return pd.DataFrame(data)


@pytest.fixture
def extreme_price_data():
    """Data with extreme price movements for testing."""
    return pd.DataFrame(
        [
            {
                "timestamp": datetime(2024, 1, 1),
                "open": 100,
                "high": 105,
                "low": 95,
                "close": 102,
                "volume": 1000,
            },
            {
                "timestamp": datetime(2024, 1, 1, 1),
                "open": 102,
                "high": 150,  # 47% increase
                "low": 100,
                "close": 147,  # 44% increase from previous close
                "volume": 5000,
            },
        ]
    )


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    """Create temporary directory for test data."""
    return tmp_path_factory.mktemp("test_data")


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "live: marks tests that require live data/APIs")


# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Cleanup test files after each test."""
    yield

    # Clean up any test files
    test_files = ["test_data", "test_cache.db", "test_trade_logic.db"]
    for filename in test_files:
        try:
            if os.path.exists(filename):
                if os.path.isdir(filename):
                    import shutil

                    shutil.rmtree(filename)
                else:
                    os.remove(filename)
        except Exception:
            pass  # Ignore cleanup errors
