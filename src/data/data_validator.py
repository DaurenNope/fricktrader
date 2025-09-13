"""
Data Quality Validator

Provides comprehensive validation for market data to ensure
data integrity and quality for trading algorithms.
"""

import logging
import re
from datetime import timedelta
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .exceptions import DataValidationError

logger = logging.getLogger(__name__)


class DataValidator:
    """Professional data quality validation for trading data."""

    def __init__(self, config: Optional[Dict] = None) -> None:
        """Initialize data validator.

        Args:
            config: Validation configuration parameters
        """
        self.config = config or {}

        # Default validation thresholds
        self.max_gap_minutes = self.config.get("max_gap_minutes", 60)
        self.max_price_change_pct = self.config.get("max_price_change_pct", 20.0)
        self.min_volume_threshold = self.config.get("min_volume_threshold", 0.0)
        self.max_spread_pct = self.config.get("max_spread_pct", 5.0)

        logger.info("DataValidator initialized with config: %s", self.config)

    def validate_ohlcv_data(self, data: pd.DataFrame, symbol: str) -> bool:
        """Validate OHLCV data structure and quality.

        Args:
            data: DataFrame with OHLCV data
            symbol: Trading symbol for error reporting

        Returns:
            True if data passes all validation checks

        Raises:
            DataValidationError: If validation fails
        """
        try:
            logger.debug("Validating OHLCV data for %s (%d rows)", symbol, len(data))

            # Check basic structure
            self._validate_data_structure(data, symbol)

            # Check for data gaps
            self._validate_data_continuity(data, symbol)

            # Check for price anomalies
            self._validate_price_data(data, symbol)

            # Check volume data
            self._validate_volume_data(data, symbol)

            # Check OHLC consistency
            self._validate_ohlc_consistency(data, symbol)

            logger.info("✅ Data validation passed for %s", symbol)
            return True

        except Exception as e:
            logger.error("❌ Data validation failed for %s: %s", symbol, e)
            raise DataValidationError(
                f"Validation failed for {symbol}: {e}", symbol
            ) from e

    def _validate_data_structure(self, data: pd.DataFrame, symbol: str) -> None:
        """Validate basic data structure and columns."""
        if data.empty:
            raise DataValidationError(f"Empty dataset for {symbol}", symbol)

        required_columns = ["timestamp", "open", "high", "low", "close", "volume"]
        missing_columns = [col for col in required_columns if col not in data.columns]

        if missing_columns:
            raise DataValidationError(
                f"Missing required columns for {symbol}: {missing_columns}", symbol
            )

        # Check for null values
        null_counts = data[required_columns].isnull().sum()
        if null_counts.any():
            raise DataValidationError(
                f"Null values found in {symbol}: {null_counts[null_counts > 0].to_dict()}",
                symbol,
            )

        # Validate data types
        numeric_columns = ["open", "high", "low", "close", "volume"]
        for col in numeric_columns:
            if not pd.api.types.is_numeric_dtype(data[col]):
                raise DataValidationError(
                    f"Non-numeric data in column {col} for {symbol}", symbol
                )

    def _validate_data_continuity(self, data: pd.DataFrame, symbol: str) -> None:
        """Check for gaps in time series data."""
        if len(data) < 2:
            return  # Can't check continuity with less than 2 data points

        # Convert timestamp to datetime if needed
        timestamps = pd.to_datetime(data["timestamp"])
        time_diffs = timestamps.diff().dropna()

        # Detect gaps larger than expected
        expected_interval = (
            time_diffs.mode().iloc[0] if not time_diffs.empty else timedelta(minutes=1)
        )
        max_allowed_gap = expected_interval * 2  # Allow up to 2x normal interval

        large_gaps = time_diffs[time_diffs > max_allowed_gap]

        if not large_gaps.empty:
            gap_count = len(large_gaps)
            largest_gap = large_gaps.max()

            logger.warning(
                "⚠️ Data gaps detected in %s: %d gaps, largest: %s",
                symbol,
                gap_count,
                largest_gap,
            )

            # Only raise error for very large gaps
            if largest_gap > timedelta(minutes=self.max_gap_minutes):
                raise DataValidationError(
                    f"Large data gap detected in {symbol}: {largest_gap}", symbol
                )

    def _validate_price_data(self, data: pd.DataFrame, symbol: str) -> None:
        """Validate price data for anomalies and consistency."""
        # Check for negative or zero prices
        price_columns = ["open", "high", "low", "close"]

        for col in price_columns:
            invalid_prices = data[data[col] <= 0]
            if not invalid_prices.empty:
                raise DataValidationError(
                    f"Invalid prices (<=0) in {col} for {symbol}: {len(invalid_prices)} rows",
                    symbol,
                )

        # Check for extreme price movements
        close_prices = data["close"]
        price_changes = close_prices.pct_change().dropna()

        extreme_changes = price_changes[
            abs(price_changes) > self.max_price_change_pct / 100
        ]

        if not extreme_changes.empty:
            max_change = extreme_changes.abs().max() * 100
            logger.warning(
                "⚠️ Extreme price movements in %s: max change %.2f%%", symbol, max_change
            )

            # Only raise error for extremely large movements
            if max_change > self.max_price_change_pct:
                raise DataValidationError(
                    f"Extreme price movement in {symbol}: {max_change:.2f}%", symbol
                )

    def _validate_volume_data(self, data: pd.DataFrame, symbol: str) -> None:
        """Validate volume data."""
        volumes = data["volume"]

        # Check for negative volumes
        negative_volumes = volumes[volumes < 0]
        if not negative_volumes.empty:
            raise DataValidationError(
                f"Negative volumes detected in {symbol}: {len(negative_volumes)} rows",
                symbol,
            )

        # Check for suspiciously low volumes (might indicate data issues)
        if self.min_volume_threshold > 0:
            low_volume_count = (volumes < self.min_volume_threshold).sum()
            if low_volume_count > len(data) * 0.5:  # More than 50% low volume
                logger.warning(
                    "⚠️ High percentage of low volume periods in %s: %.1f%%",
                    symbol,
                    (low_volume_count / len(data)) * 100,
                )

    def _validate_ohlc_consistency(self, data: pd.DataFrame, symbol: str) -> None:
        """Validate OHLC price consistency (high >= low, etc.)."""
        # High should be >= Open, Close, Low
        invalid_high = data[
            (data["high"] < data["open"])
            | (data["high"] < data["close"])
            | (data["high"] < data["low"])
        ]

        if not invalid_high.empty:
            raise DataValidationError(
                f"Invalid high prices in {symbol}: {len(invalid_high)} rows", symbol
            )

        # Low should be <= Open, Close, High
        invalid_low = data[
            (data["low"] > data["open"])
            | (data["low"] > data["close"])
            | (data["low"] > data["high"])
        ]

        if not invalid_low.empty:
            raise DataValidationError(
                f"Invalid low prices in {symbol}: {len(invalid_low)} rows", symbol
            )

    def validate_symbol_format(self, symbol: str) -> bool:
        """Validate trading symbol format.

        Args:
            symbol: Trading symbol to validate

        Returns:
            True if symbol format is valid

        Raises:
            DataValidationError: If symbol format is invalid
        """
        if not symbol or not isinstance(symbol, str):
            raise DataValidationError("Symbol must be a non-empty string")

        # Basic symbol format validation (e.g., BTC/USDT, ETH/USD)
        symbol = symbol.upper().strip()

        # Check for valid format
        if not re.match(r"^[A-Z0-9]{2,10}[/][A-Z0-9]{2,10}$", symbol):
            raise DataValidationError(f"Invalid symbol format: {symbol}")

        return True

    def get_data_quality_report(self, data: pd.DataFrame, symbol: str) -> Dict:
        """Generate comprehensive data quality report.

        Args:
            data: DataFrame with OHLCV data
            symbol: Trading symbol

        Returns:
            Dictionary with data quality metrics
        """
        report = {
            "symbol": symbol,
            "total_rows": len(data),
            "date_range": {},
            "data_quality": {},
            "anomalies": {},
            "completeness": {},
        }

        if data.empty:
            return report

        try:
            # Date range
            timestamps = pd.to_datetime(data["timestamp"])
            report["date_range"] = {
                "start": timestamps.min().isoformat(),
                "end": timestamps.max().isoformat(),
                "duration_hours": (timestamps.max() - timestamps.min()).total_seconds()
                / 3600,
            }

            # Data completeness
            required_columns = ["open", "high", "low", "close", "volume"]
            completeness = {}
            for col in required_columns:
                null_count = data[col].isnull().sum()
                completeness[col] = {
                    "null_count": int(null_count),
                    "completeness_pct": float(
                        (len(data) - null_count) / len(data) * 100
                    ),
                }
            report["completeness"] = completeness

            # Price anomalies
            price_changes = data["close"].pct_change().dropna()
            report["anomalies"] = {
                "max_price_increase_pct": (
                    float(price_changes.max() * 100) if not price_changes.empty else 0
                ),
                "max_price_decrease_pct": (
                    float(price_changes.min() * 100) if not price_changes.empty else 0
                ),
                "extreme_movements_count": int((abs(price_changes) > 0.1).sum()),
                "zero_volume_count": int((data["volume"] == 0).sum()),
            }

            # Data quality scores
            quality_score = self._calculate_quality_score(data)
            report["data_quality"] = {
                "overall_score": quality_score,
                "completeness_score": min(
                    [comp["completeness_pct"] for comp in completeness.values()]
                ),
                "consistency_score": self._calculate_consistency_score(data),
                "continuity_score": self._calculate_continuity_score(data),
            }

        except Exception as e:
            logger.error("Error generating data quality report for %s: %s", symbol, e)
            report["error"] = str(e)

        return report

    def _calculate_quality_score(self, data: pd.DataFrame) -> float:
        """Calculate overall data quality score (0-100)."""
        if data.empty:
            return 0.0

        scores = []

        # Completeness score
        required_columns = ["open", "high", "low", "close", "volume"]
        completeness = 1.0 - (
            data[required_columns].isnull().sum().sum()
            / (len(data) * len(required_columns))
        )
        scores.append(completeness * 100)

        # Consistency score
        scores.append(self._calculate_consistency_score(data))

        # Continuity score
        scores.append(self._calculate_continuity_score(data))

        return float(np.mean(scores))

    def _calculate_consistency_score(self, data: pd.DataFrame) -> float:
        """Calculate OHLC consistency score."""
        if len(data) == 0:
            return 0.0

        # Check OHLC relationships
        valid_high = (data["high"] >= data[["open", "close", "low"]].max(axis=1)).sum()
        valid_low = (data["low"] <= data[["open", "close", "high"]].min(axis=1)).sum()

        consistency_score = (valid_high + valid_low) / (2 * len(data)) * 100
        return float(consistency_score)

    def _calculate_continuity_score(self, data: pd.DataFrame) -> float:
        """Calculate time series continuity score."""
        if len(data) < 2:
            return 100.0

        timestamps = pd.to_datetime(data["timestamp"])
        time_diffs = timestamps.diff().dropna()

        if time_diffs.empty:
            return 100.0

        # Calculate expected interval
        expected_interval = time_diffs.mode().iloc[0]

        # Count intervals within acceptable range (±50% of expected)
        acceptable_range = expected_interval * 0.5
        acceptable_intervals = time_diffs[
            (time_diffs >= expected_interval - acceptable_range)
            & (time_diffs <= expected_interval + acceptable_range)
        ]

        continuity_score = len(acceptable_intervals) / len(time_diffs) * 100
        return float(continuity_score)
