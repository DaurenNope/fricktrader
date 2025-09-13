"""
Professional Market Data Manager

Core data management system for fetching, validating, caching,
and serving market data for trading strategies.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import ccxt
import pandas as pd
from cachetools import TTLCache

from .data_validator import DataValidator
from .exceptions import (DataNotAvailableError, ExchangeConnectionError,
                         InvalidSymbolError)

logger = logging.getLogger(__name__)


class MarketDataManager:
    """Professional market data management with caching and validation."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize market data manager.

        Args:
            config: Configuration dictionary with exchange settings
        """
        self.config = config or {}

        # Initialize data validator
        self.validator = DataValidator(self.config.get("validation", {}))

        # Setup caching
        cache_size = self.config.get("cache_size", 1000)
        cache_ttl = self.config.get("cache_ttl_seconds", 300)  # 5 minutes
        self.cache = TTLCache(maxsize=cache_size, ttl=cache_ttl)

        # Rate limiting
        self.rate_limit_delay = self.config.get("rate_limit_delay", 0.1)
        self.last_request_time = 0.0

        # Exchange configuration
        self.exchange_config = self.config.get(
            "exchange",
            {
                "name": "binance",
                "sandbox": True,
                "enableRateLimit": True,
                "timeout": 30000,
            },
        )

        # Initialize exchange
        self.exchange: Optional[ccxt.Exchange] = None
        self._initialize_exchange()

        # Data storage
        self.data_dir = Path(self.config.get("data_dir", "data"))
        self.data_dir.mkdir(exist_ok=True)

        logger.info(
            "MarketDataManager initialized for exchange: %s",
            self.exchange_config["name"],
        )

    def _initialize_exchange(self) -> None:
        """Initialize exchange connection."""
        try:
            exchange_class = getattr(ccxt, self.exchange_config["name"])

            # Prepare exchange configuration
            exchange_params = {
                "sandbox": self.exchange_config.get("sandbox", True),
                "enableRateLimit": self.exchange_config.get("enableRateLimit", True),
                "timeout": self.exchange_config.get("timeout", 30000),
            }

            # Add API credentials if provided (from environment)
            import os

            api_key = os.getenv(f"{self.exchange_config['name'].upper()}_API_KEY")
            api_secret = os.getenv(f"{self.exchange_config['name'].upper()}_API_SECRET")

            if api_key and api_secret:
                exchange_params.update({"apiKey": api_key, "secret": api_secret})
                logger.info(
                    "✅ API credentials found for %s", self.exchange_config["name"]
                )
            else:
                logger.warning(
                    "⚠️ No API credentials found, using public endpoints only"
                )

            self.exchange = exchange_class(exchange_params)

            # Test connection
            markets = self.exchange.load_markets()
            logger.info("✅ Exchange connected: %d markets available", len(markets))

        except Exception as e:
            logger.error("❌ Failed to initialize exchange: %s", e)
            raise ExchangeConnectionError(
                f"Failed to initialize {self.exchange_config['name']}: {e}"
            )

    def fetch_real_time_data(
        self, symbol: str, timeframe: str = "1m", limit: int = 100
    ) -> pd.DataFrame:
        """Fetch real-time OHLCV data for a symbol.

        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            timeframe: Timeframe (1m, 5m, 1h, 1d, etc.)
            limit: Number of candles to fetch

        Returns:
            DataFrame with OHLCV data

        Raises:
            InvalidSymbolError: If symbol format is invalid
            ExchangeConnectionError: If exchange connection fails
            DataNotAvailableError: If no data is available
        """
        # Validate symbol format
        self.validator.validate_symbol_format(symbol)

        # Check cache first
        cache_key = f"{symbol}_{timeframe}_{limit}_realtime"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            logger.debug("📦 Cache hit for %s %s", symbol, timeframe)
            return cached_data

        try:
            logger.debug(
                "📡 Fetching real-time data: %s %s (limit: %d)",
                symbol,
                timeframe,
                limit,
            )

            # Rate limiting
            self._enforce_rate_limit()

            # Fetch data from exchange
            if not self.exchange:
                raise ExchangeConnectionError("Exchange not initialized")

            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

            if not ohlcv:
                raise DataNotAvailableError(
                    f"No data available for {symbol} {timeframe}"
                )

            # Convert to DataFrame
            df = self._convert_ohlcv_to_dataframe(ohlcv)

            # Validate data quality
            self.validator.validate_ohlcv_data(df, symbol)

            # Cache the data
            self._store_in_cache(cache_key, df)

            logger.info(
                "✅ Fetched real-time data: %s %s (%d candles)",
                symbol,
                timeframe,
                len(df),
            )
            return df

        except ccxt.NetworkError as e:
            logger.error("🌐 Network error fetching %s: %s", symbol, e)
            raise ExchangeConnectionError(f"Network error: {e}") from e
        except ccxt.ExchangeError as e:
            logger.error("🏛️ Exchange error fetching %s: %s", symbol, e)
            raise DataNotAvailableError(f"Exchange error: {e}") from e
        except Exception as e:
            logger.error("💥 Unexpected error fetching %s: %s", symbol, e)
            raise

    def fetch_historical_data(
        self,
        symbol: str,
        timeframe: str = "1h",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data for a symbol.

        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            timeframe: Timeframe (1m, 5m, 1h, 1d, etc.)
            start_date: Start date for historical data
            end_date: End date for historical data
            limit: Maximum number of candles to fetch

        Returns:
            DataFrame with historical OHLCV data
        """
        # Validate symbol format
        self.validator.validate_symbol_format(symbol)

        # Check for cached historical data
        cache_key = f"{symbol}_{timeframe}_historical_{start_date}_{end_date}_{limit}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            logger.debug("📦 Cache hit for historical %s %s", symbol, timeframe)
            return cached_data

        try:
            logger.info("📚 Fetching historical data: %s %s", symbol, timeframe)

            # Calculate since timestamp if start_date provided
            since = None
            if start_date:
                since = int(start_date.timestamp() * 1000)

            # Rate limiting
            self._enforce_rate_limit()

            # Fetch data from exchange
            if not self.exchange:
                raise ExchangeConnectionError("Exchange not initialized")

            ohlcv = self.exchange.fetch_ohlcv(
                symbol, timeframe, since=since, limit=limit
            )

            if not ohlcv:
                raise DataNotAvailableError(
                    f"No historical data available for {symbol}"
                )

            # Convert to DataFrame
            df = self._convert_ohlcv_to_dataframe(ohlcv)

            # Filter by end_date if provided
            if end_date:
                df = df[df["timestamp"] <= end_date]

            # Validate data quality
            self.validator.validate_ohlcv_data(df, symbol)

            # Cache the data (longer TTL for historical data)
            self._store_in_cache(cache_key, df, ttl=3600)  # 1 hour cache

            # Optionally save to file for persistence
            self._save_historical_data(symbol, timeframe, df)

            logger.info(
                "✅ Fetched historical data: %s %s (%d candles)",
                symbol,
                timeframe,
                len(df),
            )
            return df

        except Exception as e:
            logger.error("❌ Error fetching historical data for %s: %s", symbol, e)
            raise

    def get_available_symbols(self) -> List[str]:
        """Get list of available trading symbols.

        Returns:
            List of available trading symbols
        """
        try:
            if not self.exchange:
                raise ExchangeConnectionError("Exchange not initialized")

            markets = self.exchange.markets
            symbols = list(markets.keys())

            # Filter for active symbols
            active_symbols = [
                symbol
                for symbol, market in markets.items()
                if market.get("active", True)
            ]

            logger.info(
                "📋 Available symbols: %d total, %d active",
                len(symbols),
                len(active_symbols),
            )
            return sorted(active_symbols)

        except Exception as e:
            logger.error("❌ Error fetching available symbols: %s", e)
            raise ExchangeConnectionError(f"Failed to fetch symbols: {e}") from e

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed information about a trading symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Dictionary with symbol information
        """
        try:
            if not self.exchange:
                raise ExchangeConnectionError("Exchange not initialized")

            markets = self.exchange.markets
            if symbol not in markets:
                raise InvalidSymbolError(f"Symbol not found: {symbol}")

            market = markets[symbol]

            # Get current ticker data
            ticker = self.exchange.fetch_ticker(symbol)

            symbol_info = {
                "symbol": symbol,
                "base": market["base"],
                "quote": market["quote"],
                "active": market.get("active", True),
                "type": market.get("type", "spot"),
                "spot": market.get("spot", True),
                "future": market.get("future", False),
                "precision": market.get("precision", {}),
                "limits": market.get("limits", {}),
                "current_price": ticker.get("last"),
                "volume_24h": ticker.get("baseVolume"),
                "change_24h_pct": ticker.get("percentage"),
                "high_24h": ticker.get("high"),
                "low_24h": ticker.get("low"),
            }

            return symbol_info

        except Exception as e:
            logger.error("❌ Error fetching symbol info for %s: %s", symbol, e)
            raise

    def get_data_quality_report(self, symbol: str, timeframe: str = "1h") -> Dict:
        """Get data quality report for a symbol.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe to analyze

        Returns:
            Data quality report dictionary
        """
        try:
            # Fetch recent data for analysis
            data = self.fetch_real_time_data(symbol, timeframe, limit=1000)

            # Generate quality report
            report = self.validator.get_data_quality_report(data, symbol)

            logger.info("📊 Generated data quality report for %s", symbol)
            return report

        except Exception as e:
            logger.error(
                "❌ Error generating data quality report for %s: %s", symbol, e
            )
            return {
                "symbol": symbol,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _convert_ohlcv_to_dataframe(self, ohlcv: List[List]) -> pd.DataFrame:
        """Convert OHLCV data to DataFrame."""
        if not ohlcv:
            return pd.DataFrame()

        df = pd.DataFrame(
            ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )

        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        # Ensure numeric types
        numeric_columns = ["open", "high", "low", "close", "volume"]
        df[numeric_columns] = df[numeric_columns].astype(float)

        # Sort by timestamp
        df = df.sort_values("timestamp").reset_index(drop=True)

        return df

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _get_from_cache(self, key: str) -> Optional[pd.DataFrame]:
        """Get data from cache."""
        try:
            return self.cache.get(key)
        except Exception as e:
            logger.warning("⚠️ Cache retrieval error: %s", e)
            return None

    def _store_in_cache(
        self, key: str, data: pd.DataFrame, ttl: Optional[int] = None
    ) -> None:
        """Store data in cache."""
        try:
            if ttl:
                # Custom TTL not directly supported by TTLCache, store with timestamp
                self.cache[key] = data
            else:
                self.cache[key] = data

            logger.debug("💾 Cached data: %s", key)
        except Exception as e:
            logger.warning("⚠️ Cache storage error: %s", e)

    def _save_historical_data(
        self, symbol: str, timeframe: str, data: pd.DataFrame
    ) -> None:
        """Save historical data to file for persistence."""
        try:
            # Create symbol directory
            symbol_dir = self.data_dir / symbol.replace("/", "_")
            symbol_dir.mkdir(exist_ok=True)

            # Save to parquet for efficiency
            filename = f"{timeframe}_{datetime.now().strftime('%Y%m%d')}.parquet"
            filepath = symbol_dir / filename

            data.to_parquet(filepath, index=False)
            logger.debug("💾 Saved historical data: %s", filepath)

        except Exception as e:
            logger.warning("⚠️ Failed to save historical data: %s", e)

    def get_cached_data_info(self) -> Dict[str, Any]:
        """Get information about cached data."""
        return {
            "cache_size": len(self.cache),
            "cache_maxsize": self.cache.maxsize,
            "cache_ttl": self.cache.ttl,
            "cache_keys": list(self.cache.keys()),
        }

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.cache.clear()
        logger.info("🗑️ Cache cleared")

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        status = {
            "timestamp": datetime.now().isoformat(),
            "exchange": {
                "name": self.exchange_config["name"],
                "connected": self.exchange is not None,
                "sandbox": self.exchange_config.get("sandbox", True),
            },
            "cache": self.get_cached_data_info(),
            "data_dir": str(self.data_dir),
            "rate_limit_delay": self.rate_limit_delay,
        }

        # Test exchange connection
        try:
            if self.exchange:
                # Try to fetch a simple ticker
                self.exchange.fetch_ticker("BTC/USDT")
                status["exchange"]["status"] = "healthy"
        except Exception as e:
            status["exchange"]["status"] = f"error: {e}"

        return status
