"""
Integration tests for data pipeline components.

Tests the interaction between MarketDataManager, DataValidator,
and DataWarehouse components in realistic scenarios.
"""

import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from src.data.data_validator import DataValidator
from src.data.exceptions import DataValidationError
from src.data.market_data_manager import MarketDataManager
from src.database.data_warehouse import DataWarehouse


class TestDataPipelineIntegration:
    """Integration tests for data pipeline workflow."""

    @pytest.fixture
    def temp_env(self):
        """Create temporary environment for integration tests."""
        temp_dir = tempfile.mkdtemp()
        temp_db = str(Path(temp_dir) / "test_warehouse.db")

        yield {
            "temp_dir": Path(temp_dir),
            "temp_db": temp_db,
        }

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def pipeline_config(self, temp_env):
        """Configuration for pipeline integration tests."""
        return {
            "exchange": {
                "name": "binance",
                "sandbox": True,
                "enableRateLimit": True,
                "timeout": 30000,
            },
            "cache_size": 50,
            "cache_ttl_seconds": 30,
            "rate_limit_delay": 0.01,
            "data_dir": str(temp_env["temp_dir"]),
            "validation": {
                "max_gap_minutes": 60,
                "max_price_change_pct": 20.0,
                "min_volume_threshold": 100.0,
                "max_spread_pct": 5.0,
            },
            "warehouse_db": temp_env["temp_db"],
        }

    @pytest.mark.integration
    def test_full_data_pipeline_flow(self, pipeline_config, mock_exchange):
        """Test complete data flow from fetching to validation to storage."""
        with patch("src.data.market_data_manager.ccxt.binance") as mock_binance:
            mock_binance.return_value = mock_exchange

            # Initialize components
            data_manager = MarketDataManager(pipeline_config)
            validator = DataValidator(pipeline_config["validation"])

            symbol = "BTC/USDT"
            timeframe = "1h"

            # Step 1: Fetch data
            raw_data = data_manager.fetch_real_time_data(symbol, timeframe, limit=50)

            # Verify data was fetched
            assert isinstance(raw_data, pd.DataFrame)
            assert len(raw_data) == 50

            # Step 2: Validate data
            is_valid = validator.validate_ohlcv_data(raw_data, symbol)
            assert is_valid is True

            # Step 3: Store validated data
            DataWarehouse(pipeline_config["warehouse_db"]).store_ohlcv_data(symbol, timeframe, raw_data)

            # Step 4: Retrieve stored data
            stored_data = DataWarehouse(pipeline_config["warehouse_db"]).get_ohlcv_data(symbol, timeframe, limit=50)

            # Verify data integrity through the pipeline
            assert len(stored_data) == len(raw_data)
            pd.testing.assert_frame_equal(
                raw_data.reset_index(drop=True), stored_data.reset_index(drop=True)
            )

    @pytest.mark.integration
    def test_pipeline_with_invalid_data_handling(self, pipeline_config, mock_exchange):
        """Test pipeline behavior when invalid data is encountered."""
        with patch("src.data.market_data_manager.ccxt.binance") as mock_binance:
            # Mock exchange to return invalid data
            invalid_ohlcv = [
                [
                    1640995200000,
                    47000.0,
                    46500.0,
                    47500.0,
                    47200.0,
                    1234.56,
                ],  # high < low (invalid)
                [
                    1640998800000,
                    47200.0,
                    47800.0,
                    46800.0,
                    47600.0,
                    -2345.67,
                ],  # negative volume (invalid)
            ]

            mock_exchange.fetch_ohlcv.return_value = invalid_ohlcv
            mock_binance.return_value = mock_exchange

            # Initialize components
            data_manager = MarketDataManager(pipeline_config)
            validator = DataValidator(pipeline_config["validation"])
            warehouse = DataWarehouse(pipeline_config["warehouse_db"])

            symbol = "BTC/USDT"
            timeframe = "1h"

            # Step 1: Fetch data (contains invalid data)
            raw_data = data_manager.fetch_real_time_data(symbol, timeframe, limit=10)

            # Step 2: Validation should catch invalid data
            with pytest.raises(DataValidationError):
                validator.validate_ohlcv_data(raw_data, symbol)

            # Data should not be stored if validation fails
            # (This test verifies the pipeline respects validation)

    @pytest.mark.integration
    def test_pipeline_cache_and_persistence_integration(
        self, pipeline_config, mock_exchange
    ):
        """Test integration of caching and file persistence."""
        with patch("src.data.market_data_manager.ccxt.binance") as mock_binance:
            mock_binance.return_value = mock_exchange

            # Initialize data manager
            data_manager = MarketDataManager(pipeline_config)

            symbol = "BTC/USDT"
            timeframe = "1h"

            # First fetch - should hit exchange and cache
            data1 = data_manager.fetch_real_time_data(symbol, timeframe, limit=25)

            # Verify exchange was called
            assert mock_exchange.fetch_ohlcv.call_count == 1

            # Second fetch - should use cache
            data2 = data_manager.fetch_real_time_data(symbol, timeframe, limit=25)

            # Exchange should not be called again (cached)
            assert mock_exchange.fetch_ohlcv.call_count == 1

            # Data should be identical
            pd.testing.assert_frame_equal(data1, data2)

            # Verify file was saved for historical data
            data_manager.fetch_historical_data(
                symbol,
                timeframe,
                start_date=datetime.now() - timedelta(days=1),
                limit=25,
            )

            # Check if file persistence worked
            symbol_dir = Path(pipeline_config["data_dir"]) / symbol.replace("/", "_")
            assert symbol_dir.exists()

            # Check for parquet files
            parquet_files = list(symbol_dir.glob("*.parquet"))
            assert len(parquet_files) > 0

    @pytest.mark.integration
    def test_multi_symbol_pipeline_workflow(self, pipeline_config, mock_exchange):
        """Test pipeline with multiple symbols simultaneously."""
        with patch("src.data.market_data_manager.ccxt.binance") as mock_binance:
            mock_binance.return_value = mock_exchange

            # Initialize components
            data_manager = MarketDataManager(pipeline_config)
            validator = DataValidator(pipeline_config["validation"])
            warehouse = DataWarehouse(pipeline_config["warehouse_db"])

            symbols = ["BTC/USDT", "ETH/USDT"]
            timeframe = "1h"

            results = {}

            # Process multiple symbols
            for symbol in symbols:
                # Fetch and validate data for each symbol
                raw_data = data_manager.fetch_real_time_data(
                    symbol, timeframe, limit=20
                )
                is_valid = validator.validate_ohlcv_data(raw_data, symbol)

                assert is_valid is True

                # Store data
                warehouse.store_ohlcv_data(symbol, timeframe, raw_data)
                results[symbol] = raw_data

            # Verify all symbols were processed
            assert len(results) == len(symbols)

            # Verify data was stored for all symbols
            for symbol in symbols:
                stored_data = warehouse.get_ohlcv_data(symbol, timeframe, limit=20)
                assert len(stored_data) == 20

                # Verify data integrity
                pd.testing.assert_frame_equal(
                    results[symbol].reset_index(drop=True),
                    stored_data.reset_index(drop=True),
                )

    @pytest.mark.integration
    def test_pipeline_error_recovery_and_logging(self, pipeline_config, mock_exchange):
        """Test pipeline error recovery and logging integration."""
        with patch("src.data.market_data_manager.ccxt.binance") as mock_binance:
            mock_binance.return_value = mock_exchange

            # Initialize components
            data_manager = MarketDataManager(pipeline_config)
            validator = DataValidator(pipeline_config["validation"])

            symbol = "BTC/USDT"

            # Test successful operation logging
            with patch("src.data.market_data_manager.logger") as mock_logger:
                data = data_manager.fetch_real_time_data(symbol, limit=10)

                # Verify success was logged
                mock_logger.info.assert_called()
                success_logged = any(
                    "✅" in str(call) for call in mock_logger.info.call_args_list
                )
                assert success_logged

            # Test validation logging
            with patch("src.data.data_validator.logger") as mock_val_logger:
                validator.validate_ohlcv_data(data, symbol)

                # Verify validation success was logged
                mock_val_logger.info.assert_called()
                success_logged = any(
                    "✅" in str(call) for call in mock_val_logger.info.call_args_list
                )
                assert success_logged

    @pytest.mark.integration
    @pytest.mark.slow
    def test_pipeline_performance_with_large_dataset(
        self, pipeline_config, mock_exchange
    ):
        """Test pipeline performance with larger datasets."""
        # Mock exchange to return larger dataset
        large_ohlcv = []
        base_time = int(datetime(2024, 1, 1).timestamp() * 1000)

        for i in range(1000):  # 1000 data points
            timestamp = base_time + (i * 3600000)  # 1 hour intervals
            large_ohlcv.append(
                [
                    timestamp,
                    50000.0 + (i % 100),  # Varying price
                    50100.0 + (i % 100),
                    49900.0 + (i % 100),
                    50050.0 + (i % 100),
                    1000 + (i % 5000),
                ]
            )

        mock_exchange.fetch_ohlcv.return_value = large_ohlcv

        with patch("src.data.market_data_manager.ccxt.binance") as mock_binance:
            mock_binance.return_value = mock_exchange

            # Initialize components
            data_manager = MarketDataManager(pipeline_config)
            validator = DataValidator(pipeline_config["validation"])
            warehouse = DataWarehouse(pipeline_config["warehouse_db"])

            symbol = "BTC/USDT"
            timeframe = "15m"

            # Measure pipeline performance
            import time

            start_time = time.time()

            # Execute full pipeline
            raw_data = data_manager.fetch_real_time_data(symbol, timeframe, limit=1000)
            validator.validate_ohlcv_data(raw_data, symbol)
            warehouse.store_ohlcv_data(symbol, timeframe, raw_data)

            elapsed_time = time.time() - start_time

            # Verify data was processed correctly
            assert len(raw_data) == 1000

            # Performance should be reasonable (less than 5 seconds for 1000 records)
            assert (
                elapsed_time < 5.0
            ), f"Pipeline took {elapsed_time:.2f}s, which is too slow"

    @pytest.mark.integration
    def test_pipeline_data_quality_reporting(self, pipeline_config, mock_exchange):
        """Test integrated data quality reporting across components."""
        with patch("src.data.market_data_manager.ccxt.binance") as mock_binance:
            mock_binance.return_value = mock_exchange

            # Initialize components
            data_manager = MarketDataManager(pipeline_config)
            validator = DataValidator(pipeline_config["validation"])

            symbol = "BTC/USDT"
            timeframe = "1h"

            # Fetch data
            data = data_manager.fetch_real_time_data(symbol, timeframe, limit=30)

            # Get quality reports from both components
            manager_report = data_manager.get_data_quality_report(symbol)
            validator_report = validator.get_data_quality_report(data, symbol)

            # Verify reports are consistent
            assert manager_report["symbol"] == validator_report["symbol"] == symbol

            # Both should report positive data quality
            assert "data_quality" in manager_report
            assert "data_quality" in validator_report

            # Quality scores should be reasonable
            assert validator_report["data_quality"]["overall_score"] > 50.0
