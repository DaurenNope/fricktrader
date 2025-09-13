"""
Data formatting and processing utilities for OpenBB market data
"""

import time
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

logger = logging.getLogger(__name__)


@dataclass
class MarketDepthData:
    """Order book depth data"""

    bids: List[Tuple[float, float]]  # [(price, size), ...]
    asks: List[Tuple[float, float]]  # [(price, size), ...]
    timestamp: datetime
    spread: float
    mid_price: float
    total_bid_volume: float
    total_ask_volume: float
    imbalance_ratio: float  # bid_volume / (bid_volume + ask_volume)


@dataclass
class DeltaAnalysis:
    """Advanced delta and order flow analysis"""

    cumulative_delta: float
    delta_momentum: float
    buying_pressure: float
    selling_pressure: float
    net_delta: float
    delta_divergence: float
    order_flow_strength: float
    institutional_flow: float
    retail_flow: float
    timestamp: datetime


@dataclass
class VolumeProfile:
    """Volume profile analysis"""

    poc_price: float  # Point of Control
    value_area_high: float
    value_area_low: float
    volume_by_price: Dict[float, float]
    total_volume: float
    buying_volume: float
    selling_volume: float
    volume_imbalance: float


@dataclass
class InstitutionalData:
    """Institutional trading data"""

    dark_pool_volume: float
    block_trades: List[Dict]
    unusual_options_activity: List[Dict]
    insider_trading: List[Dict]
    institutional_ownership: float
    float_short: float
    days_to_cover: float


class DataFormatter:
    """
    Handles data formatting, caching, and processing utilities for market data analysis.
    Provides caching mechanisms and complex calculations for delta analysis and volume profiles.
    """

    def __init__(self):
        """Initialize data formatter with cache settings."""
        self.cache = {}
        self.cache_duration = 60  # 1 minute cache for real-time data
        self.max_cache_size = 1000  # Prevent memory issues

        # Check dependencies
        if not PANDAS_AVAILABLE:
            logger.warning("Pandas not available - some data formatting features may be limited")
        if not NUMPY_AVAILABLE:
            logger.warning("NumPy not available - some calculations may be slower")

    def _is_cached(self, key: str, duration: Optional[int] = None) -> bool:
        """Check if data is cached and still valid.

        Args:
            key: Cache key to check
            duration: Optional cache duration override (seconds)

        Returns:
            True if data is cached and still valid, False otherwise
        """
        if not key or key not in self.cache:
            return False

        try:
            cache_duration = duration or self.cache_duration
            cache_time = self.cache[key]["timestamp"]
            is_valid = (time.time() - cache_time) < cache_duration

            if not is_valid:
                # Clean up expired entry
                del self.cache[key]

            return is_valid
        except (KeyError, TypeError) as e:
            logger.debug(f"Cache check error for key {key}: {e}")
            return False

    def _cache_data(self, key: str, data: Any) -> None:
        """Cache data with timestamp and manage cache size.

        Args:
            key: Cache key
            data: Data to cache
        """
        if not key:
            return

        try:
            # Manage cache size
            if len(self.cache) >= self.max_cache_size:
                # Remove oldest entries
                oldest_keys = sorted(
                    self.cache.keys(),
                    key=lambda k: self.cache[k]["timestamp"]
                )[:len(self.cache) // 4]  # Remove 25% of oldest entries

                for old_key in oldest_keys:
                    try:
                        del self.cache[old_key]
                    except KeyError:
                        pass

            self.cache[key] = {"data": data, "timestamp": time.time()}

        except Exception as e:
            logger.warning(f"Error caching data for key {key}: {e}")

    def get_cached_data(self, key: str, duration: Optional[int] = None) -> Optional[Any]:
        """Get cached data if still valid.

        Args:
            key: Cache key to retrieve
            duration: Optional cache duration override (seconds)

        Returns:
            Cached data if valid, None otherwise
        """
        if self._is_cached(key, duration):
            try:
                return self.cache[key]["data"]
            except KeyError:
                return None
        return None

    def cache_data(self, key: str, data: Any) -> None:
        """Cache data with timestamp.

        Args:
            key: Cache key
            data: Data to cache
        """
        self._cache_data(key, data)

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.cache.clear()
        logger.debug("Cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        current_time = time.time()
        valid_entries = sum(
            1 for entry in self.cache.values()
            if (current_time - entry["timestamp"]) < self.cache_duration
        )

        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.cache) - valid_entries,
            "cache_duration_seconds": self.cache_duration,
            "max_cache_size": self.max_cache_size
        }

    def calculate_delta_metrics(self, df) -> Optional[DeltaAnalysis]:
        """Calculate comprehensive delta and order flow metrics.

        Args:
            df: DataFrame with OHLCV data columns ['timestamp', 'open', 'high', 'low', 'close', 'volume']

        Returns:
            DeltaAnalysis object with calculated metrics or None if calculation fails
        """
        if not PANDAS_AVAILABLE or not NUMPY_AVAILABLE:
            logger.warning("Pandas or NumPy not available for delta analysis")
            return None

        if df is None or df.empty:
            logger.warning("Empty DataFrame provided for delta analysis")
            return None

        try:
            # Validate required columns
            required_columns = ['close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.warning(f"Missing required columns for delta analysis: {missing_columns}")
                return None
            # Make a copy to avoid modifying the original DataFrame
            df = df.copy()

            # Price change and volume analysis
            df["price_change"] = df["close"].pct_change().fillna(0)
            df["price_direction"] = np.where(
                df["price_change"] > 0, 1, np.where(df["price_change"] < 0, -1, 0)
            ).astype(int)

            # Volume-weighted price analysis with safe division
            typical_price = (df["high"] + df["low"] + df["close"]) / 3
            volume_price = (df["volume"] * typical_price).cumsum()
            volume_sum = df["volume"].cumsum()

            # Avoid division by zero
            df["vwap"] = np.where(volume_sum > 0, volume_price / volume_sum, df["close"])
            df["price_vs_vwap"] = np.where(
                df["vwap"] > 0, (df["close"] / df["vwap"]) - 1, 0
            )

            # Delta calculation (buying vs selling pressure)
            # Positive delta = buying pressure, Negative delta = selling pressure
            df["raw_delta"] = (df["volume"] * df["price_direction"]).fillna(0)
            df["cumulative_delta"] = df["raw_delta"].cumsum()

            # Delta momentum (rate of change) with safe lookback
            lookback = min(5, len(df) // 2) if len(df) > 5 else 1
            df["delta_momentum"] = df["cumulative_delta"].diff(lookback).fillna(0)

            # Buying and selling pressure
            df["buying_volume"] = np.where(df["price_direction"] > 0, df["volume"], 0)
            df["selling_volume"] = np.where(df["price_direction"] < 0, df["volume"], 0)

            # Use adaptive rolling window
            rolling_window = min(20, len(df) // 2) if len(df) > 20 else len(df)
            buying_pressure = df["buying_volume"].rolling(rolling_window, min_periods=1).sum().iloc[-1]
            selling_pressure = df["selling_volume"].rolling(rolling_window, min_periods=1).sum().iloc[-1]

            # Net delta and divergence
            net_delta = float(buying_pressure - selling_pressure)

            # Delta divergence (price vs delta momentum)
            price_lookback = min(10, len(df) // 2) if len(df) > 10 else 1
            price_momentum = df["close"].pct_change(price_lookback).iloc[-1]

            # Safe normalization
            avg_volume = df["volume"].rolling(rolling_window, min_periods=1).mean().iloc[-1]
            delta_momentum_normalized = (
                df["delta_momentum"].iloc[-1] / avg_volume
                if avg_volume > 0 else 0
            )

            # Calculate divergence with null checks
            delta_divergence = 0.0
            if not (pd.isna(price_momentum) or pd.isna(delta_momentum_normalized)):
                if price_momentum > 0 and delta_momentum_normalized < 0:
                    delta_divergence = -0.5  # Bearish divergence
                elif price_momentum < 0 and delta_momentum_normalized > 0:
                    delta_divergence = 0.5  # Bullish divergence

            # Order flow strength
            total_volume = df["volume"].rolling(rolling_window, min_periods=1).sum().iloc[-1]
            order_flow_strength = (
                float(df["cumulative_delta"].iloc[-1]) / total_volume
                if total_volume > 0
                else 0.0
            )

            # Institutional vs retail flow estimation
            # Large volume bars likely institutional, small bars likely retail
            volume_threshold = df["volume"].quantile(0.8)  # Top 20% volume bars
            institutional_volume = float(df[df["volume"] > volume_threshold]["volume"].sum())
            retail_volume = float(df[df["volume"] <= volume_threshold]["volume"].sum())

            total_flow = institutional_volume + retail_volume
            institutional_flow = (
                institutional_volume / total_flow
                if total_flow > 0 else 0.5
            )
            retail_flow = 1.0 - institutional_flow

            return DeltaAnalysis(
                cumulative_delta=float(df["cumulative_delta"].iloc[-1]),
                delta_momentum=float(df["delta_momentum"].iloc[-1]),
                buying_pressure=float(buying_pressure),
                selling_pressure=float(selling_pressure),
                net_delta=net_delta,
                delta_divergence=float(delta_divergence),
                order_flow_strength=order_flow_strength,
                institutional_flow=institutional_flow,
                retail_flow=retail_flow,
                timestamp=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Error calculating delta metrics: {e}", exc_info=True)
            return None

    def calculate_volume_profile(self, df: pd.DataFrame) -> Optional[VolumeProfile]:
        """Calculate volume profile metrics"""
        try:
            # Create price bins
            price_min = df["low"].min()
            price_max = df["high"].max()
            num_bins = 50
            price_bins = np.linspace(price_min, price_max, num_bins)

            # Calculate volume by price
            volume_by_price = {}
            buying_volume_total = 0
            selling_volume_total = 0

            for _, row in df.iterrows():
                # Distribute volume across price range for this candle
                candle_range = row["high"] - row["low"]
                if candle_range > 0:
                    # Simple distribution - could be more sophisticated
                    volume_per_price = row["volume"] / candle_range

                    # Determine buying vs selling volume based on close vs open
                    if row["close"] > row["open"]:
                        buying_volume_total += row["volume"] * 0.6  # Assume 60% buying
                        selling_volume_total += row["volume"] * 0.4
                    else:
                        buying_volume_total += row["volume"] * 0.4
                        selling_volume_total += row["volume"] * 0.6  # Assume 60% selling

                    # Add to volume profile
                    for price in price_bins:
                        if row["low"] <= price <= row["high"]:
                            if price not in volume_by_price:
                                volume_by_price[price] = 0
                            volume_by_price[price] += volume_per_price

            if not volume_by_price:
                return None

            # Find Point of Control (POC) - price with highest volume
            poc_price = max(volume_by_price.keys(), key=lambda k: volume_by_price[k])

            # Calculate Value Area (70% of volume)
            total_volume = sum(volume_by_price.values())
            target_volume = total_volume * 0.7

            # Sort prices by volume
            sorted_prices = sorted(
                volume_by_price.keys(), key=lambda k: volume_by_price[k], reverse=True
            )

            value_area_volume = 0
            value_area_prices = []

            for price in sorted_prices:
                value_area_volume += volume_by_price[price]
                value_area_prices.append(price)
                if value_area_volume >= target_volume:
                    break

            value_area_high = max(value_area_prices) if value_area_prices else poc_price
            value_area_low = min(value_area_prices) if value_area_prices else poc_price

            volume_imbalance = (
                (buying_volume_total - selling_volume_total) / total_volume
                if total_volume > 0
                else 0
            )

            return VolumeProfile(
                poc_price=poc_price,
                value_area_high=value_area_high,
                value_area_low=value_area_low,
                volume_by_price=volume_by_price,
                total_volume=total_volume,
                buying_volume=buying_volume_total,
                selling_volume=selling_volume_total,
                volume_imbalance=volume_imbalance,
            )

        except Exception as e:
            logger.error(f"Error calculating volume profile: {e}")
            return None

    def generate_analysis_summary(
        self, market_depth, delta_analysis, volume_profile, institutional_data
    ) -> Dict[str, Any]:
        """Generate a summary of the analysis"""
        summary = {
            "overall_sentiment": "neutral",
            "key_levels": {},
            "risk_factors": [],
            "opportunities": [],
            "confidence_score": 0.5,
        }

        try:
            # Analyze market depth
            if market_depth:
                if market_depth.imbalance_ratio > 0.6:
                    summary["overall_sentiment"] = "bullish"
                    summary["opportunities"].append("Strong bid support")
                elif market_depth.imbalance_ratio < 0.4:
                    summary["overall_sentiment"] = "bearish"
                    summary["risk_factors"].append("Weak bid support")

                summary["key_levels"]["current_spread"] = market_depth.spread
                summary["key_levels"]["mid_price"] = market_depth.mid_price

            # Analyze delta
            if delta_analysis:
                if delta_analysis.net_delta > 0:
                    summary["opportunities"].append("Positive order flow")
                else:
                    summary["risk_factors"].append("Negative order flow")

                if delta_analysis.delta_divergence > 0.3:
                    summary["opportunities"].append("Bullish divergence detected")
                elif delta_analysis.delta_divergence < -0.3:
                    summary["risk_factors"].append("Bearish divergence detected")

            # Analyze volume profile
            if volume_profile:
                summary["key_levels"]["poc_price"] = volume_profile.poc_price
                summary["key_levels"]["value_area_high"] = volume_profile.value_area_high
                summary["key_levels"]["value_area_low"] = volume_profile.value_area_low

                if volume_profile.volume_imbalance > 0.2:
                    summary["opportunities"].append("Strong buying volume")
                elif volume_profile.volume_imbalance < -0.2:
                    summary["risk_factors"].append("Strong selling volume")

            # Calculate confidence score
            factors = 0
            positive_factors = 0

            if market_depth:
                factors += 1
                if market_depth.imbalance_ratio > 0.5:
                    positive_factors += 1

            if delta_analysis:
                factors += 1
                if delta_analysis.net_delta > 0:
                    positive_factors += 1

            if volume_profile:
                factors += 1
                if volume_profile.volume_imbalance > 0:
                    positive_factors += 1

            if factors > 0:
                summary["confidence_score"] = positive_factors / factors

            # Determine overall sentiment
            if summary["confidence_score"] > 0.6:
                summary["overall_sentiment"] = "bullish"
            elif summary["confidence_score"] < 0.4:
                summary["overall_sentiment"] = "bearish"
            else:
                summary["overall_sentiment"] = "neutral"

        except Exception as e:
            logger.error(f"Error generating analysis summary: {e}")

        # Add timestamp to summary
        summary["timestamp"] = datetime.now().isoformat()
        summary["total_signals"] = len(summary.get("opportunities", [])) + len(summary.get("risk_factors", []))

        return summary
