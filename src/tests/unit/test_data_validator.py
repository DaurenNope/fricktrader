"""
Unit tests for DataValidator class.

Tests data quality validation, anomaly detection,
and error handling for market data.
"""

from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

from src.data.data_validator import DataValidator
from src.data.exceptions import DataValidationError


class TestDataValidator:
    """Test suite for DataValidator class."""

    @pytest.fixture
    def validator(self, sample_config):
        """Create DataValidator instance for testing."""
        return DataValidator(sample_config["validation"])

    @pytest.mark.unit
    def test_validator_initialization(self, sample_config):
        """Test DataValidator initialization with config."""
        validator = DataValidator(sample_config["validation"])

        assert validator.max_gap_minutes == 60
        assert validator.max_price_change_pct == 20.0
        assert validator.min_volume_threshold == 100.0
        assert validator.max_spread_pct == 5.0

    @pytest.mark.unit
    def test_validator_default_config(self):
        """Test DataValidator with default configuration."""
        validator = DataValidator()

        assert validator.max_gap_minutes == 60
        assert validator.max_price_change_pct == 20.0
        assert validator.min_volume_threshold == 0.0
        assert validator.max_spread_pct == 5.0

    @pytest.mark.unit
    def test_validate_ohlcv_data_success(self, validator, sample_ohlcv_data):
        """Test successful OHLCV data validation."""
        result = validator.validate_ohlcv_data(sample_ohlcv_data, "BTC/USDT")
        assert result is True

    @pytest.mark.unit
    def test_validate_empty_data(self, validator):
        """Test validation with empty DataFrame."""
        empty_df = pd.DataFrame()

        with pytest.raises(DataValidationError, match="Empty dataset"):
            validator.validate_ohlcv_data(empty_df, "BTC/USDT")

    @pytest.mark.unit
    def test_validate_missing_columns(self, validator):
        """Test validation with missing required columns."""
        incomplete_df = pd.DataFrame(
            {
                "timestamp": [datetime.now()],
                "open": [100],
                "close": [102],
                # Missing high, low, volume
            }
        )

        with pytest.raises(DataValidationError, match="Missing required columns"):
            validator.validate_ohlcv_data(incomplete_df, "BTC/USDT")

    @pytest.mark.unit
    def test_validate_null_values(self, validator):
        """Test validation with null values."""
        null_df = pd.DataFrame(
            {
                "timestamp": [datetime.now(), datetime.now()],
                "open": [100, None],  # Null value
                "high": [105, 110],
                "low": [95, 105],
                "close": [102, 108],
                "volume": [1000, 1500],
            }
        )

        with pytest.raises(DataValidationError, match="Null values found"):
            validator.validate_ohlcv_data(null_df, "BTC/USDT")

    @pytest.mark.unit
    def test_validate_invalid_ohlc_relationships(self, validator, invalid_ohlcv_data):
        """Test validation with invalid OHLC relationships."""
        with pytest.raises(DataValidationError, match="Invalid"):
            validator.validate_ohlcv_data(invalid_ohlcv_data, "BTC/USDT")

    @pytest.mark.unit
    def test_validate_negative_prices(self, validator):
        """Test validation with negative prices."""
        negative_price_df = pd.DataFrame(
            {
                "timestamp": [datetime.now()],
                "open": [-100],  # Negative price
                "high": [105],
                "low": [95],
                "close": [102],
                "volume": [1000],
            }
        )

        with pytest.raises(DataValidationError, match="Invalid prices"):
            validator.validate_ohlcv_data(negative_price_df, "BTC/USDT")

    @pytest.mark.unit
    def test_validate_negative_volume(self, validator):
        """Test validation with negative volume."""
        negative_volume_df = pd.DataFrame(
            {
                "timestamp": [datetime.now()],
                "open": [100],
                "high": [105],
                "low": [95],
                "close": [102],
                "volume": [-1000],  # Negative volume
            }
        )

        with pytest.raises(DataValidationError, match="Negative volumes"):
            validator.validate_ohlcv_data(negative_volume_df, "BTC/USDT")

    @pytest.mark.unit
    def test_validate_data_gaps(self, validator, data_with_gaps):
        """Test validation with time gaps in data."""
        # Should not raise error for moderate gaps
        result = validator.validate_ohlcv_data(data_with_gaps, "BTC/USDT")
        assert result is True

    @pytest.mark.unit
    def test_validate_extreme_price_movements(self, validator, extreme_price_data):
        """Test validation with extreme price movements."""
        # Should handle extreme movements without error (just warnings)
        result = validator.validate_ohlcv_data(extreme_price_data, "BTC/USDT")
        assert result is True

    @pytest.mark.unit
    def test_symbol_format_validation_success(self, validator):
        """Test successful symbol format validation."""
        valid_symbols = ["BTC/USDT", "ETH/USD", "ADA/BTC", "DOT/EUR"]

        for symbol in valid_symbols:
            result = validator.validate_symbol_format(symbol)
            assert result is True

    @pytest.mark.unit
    def test_symbol_format_validation_failure(self, validator):
        """Test symbol format validation with invalid formats."""
        invalid_symbols = ["", "BTC", "BTC-USDT", "BTC/USDT/EUR", "123", "btc/usdt"]

        for symbol in invalid_symbols:
            with pytest.raises(DataValidationError):
                validator.validate_symbol_format(symbol)

    @pytest.mark.unit
    def test_symbol_format_validation_none(self, validator):
        """Test symbol format validation with None input."""
        with pytest.raises(DataValidationError):
            validator.validate_symbol_format(None)

    @pytest.mark.unit
    def test_data_quality_report_generation(self, validator, sample_ohlcv_data):
        """Test data quality report generation."""
        report = validator.get_data_quality_report(sample_ohlcv_data, "BTC/USDT")

        assert "symbol" in report
        assert "total_rows" in report
        assert "date_range" in report
        assert "data_quality" in report
        assert "anomalies" in report
        assert "completeness" in report

        assert report["symbol"] == "BTC/USDT"
        assert report["total_rows"] == len(sample_ohlcv_data)
        assert report["data_quality"]["overall_score"] > 0

    @pytest.mark.unit
    def test_data_quality_report_empty_data(self, validator):
        """Test data quality report with empty data."""
        empty_df = pd.DataFrame()
        report = validator.get_data_quality_report(empty_df, "BTC/USDT")

        assert report["symbol"] == "BTC/USDT"
        assert report["total_rows"] == 0

    @pytest.mark.unit
    def test_calculate_quality_score(self, validator, sample_ohlcv_data):
        """Test quality score calculation."""
        score = validator._calculate_quality_score(sample_ohlcv_data)

        assert isinstance(score, float)
        assert 0 <= score <= 100

    @pytest.mark.unit
    def test_calculate_consistency_score(self, validator, sample_ohlcv_data):
        """Test consistency score calculation."""
        score = validator._calculate_consistency_score(sample_ohlcv_data)

        assert isinstance(score, float)
        assert 0 <= score <= 100

    @pytest.mark.unit
    def test_calculate_continuity_score(self, validator, sample_ohlcv_data):
        """Test continuity score calculation."""
        score = validator._calculate_continuity_score(sample_ohlcv_data)

        assert isinstance(score, float)
        assert 0 <= score <= 100

    @pytest.mark.unit
    def test_validate_data_structure_non_numeric(self, validator):
        """Test validation with non-numeric data."""
        non_numeric_df = pd.DataFrame(
            {
                "timestamp": [datetime.now()],
                "open": ["not_a_number"],  # Non-numeric
                "high": [105],
                "low": [95],
                "close": [102],
                "volume": [1000],
            }
        )

        with pytest.raises(DataValidationError, match="Non-numeric data"):
            validator.validate_ohlcv_data(non_numeric_df, "BTC/USDT")

    @pytest.mark.unit
    @patch("src.data.data_validator.logger")
    def test_logging_on_validation_success(
        self, mock_logger, validator, sample_ohlcv_data
    ):
        """Test that successful validation logs appropriate messages."""
        validator.validate_ohlcv_data(sample_ohlcv_data, "BTC/USDT")

        # Check that info log was called for successful validation
        mock_logger.info.assert_called()

        # Verify the log message contains success indicator
        log_calls = mock_logger.info.call_args_list
        success_logged = any("✅" in str(call) for call in log_calls)
        assert success_logged

    @pytest.mark.unit
    @patch("src.data.data_validator.logger")
    def test_logging_on_validation_failure(self, mock_logger, validator):
        """Test that validation failures log appropriate messages."""
        empty_df = pd.DataFrame()

        with pytest.raises(DataValidationError):
            validator.validate_ohlcv_data(empty_df, "BTC/USDT")

        # Check that error log was called
        mock_logger.error.assert_called()

    @pytest.mark.unit
    def test_validate_continuity_single_datapoint(self, validator):
        """Test continuity validation with single data point."""
        single_point_df = pd.DataFrame(
            {
                "timestamp": [datetime.now()],
                "open": [100],
                "high": [105],
                "low": [95],
                "close": [102],
                "volume": [1000],
            }
        )

        # Should not raise error with single data point
        result = validator.validate_ohlcv_data(single_point_df, "BTC/USDT")
        assert result is True

    @pytest.mark.unit
    def test_error_handling_in_quality_report(self, validator):
        """Test error handling in quality report generation."""
        # Create problematic data that might cause errors during report generation
        problematic_df = pd.DataFrame(
            {
                "timestamp": [datetime.now()],
                "open": [float("inf")],  # Infinity value
                "high": [105],
                "low": [95],
                "close": [102],
                "volume": [1000],
            }
        )

        # Should handle errors gracefully and include error in report
        report = validator.get_data_quality_report(problematic_df, "BTC/USDT")

        # Report should be generated despite errors
        assert "symbol" in report
        assert report["symbol"] == "BTC/USDT"
