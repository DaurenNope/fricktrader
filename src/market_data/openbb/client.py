"""
OpenBB API client and authentication module
Handles OpenBB initialization, API key configuration, and fallback sources
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import asyncio

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

# Optional imports with fallbacks
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    yf = None

try:
    from openbb import obb
    OPENBB_AVAILABLE = True
except ImportError:
    OPENBB_AVAILABLE = False
    obb = None

logger = logging.getLogger(__name__)


class OpenBBClient:
    """
    OpenBB API client with authentication and fallback capabilities
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize OpenBB client with configuration.

        Args:
            config: Configuration dictionary with API keys and settings
        """
        self.config = config or {}
        self.openbb_available = False
        self._rate_limiter = {"last_call": 0, "min_interval": 0.1}  # Rate limiting

        # Initialize OpenBB
        if OPENBB_AVAILABLE:
            try:
                self._configure_openbb()
                self.openbb_available = True
                logger.info("🚀 OpenBB Platform initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenBB: {e}", exc_info=True)
                self.openbb_available = False
        else:
            self.openbb_available = False
            logger.info("📊 OpenBB not available, using fallback sources")

        logger.info("📊 OpenBB Client initialized")

    def _configure_openbb(self) -> None:
        """Configure OpenBB with API keys from config.

        Raises:
            Exception: If OpenBB configuration fails
        """
        if not OPENBB_AVAILABLE:
            return

        try:
            # Set API keys from config if available
            api_keys = self.config.get("api_keys", {})
            configured_keys = []

            if "fmp_api_key" in api_keys:
                obb.account.credentials.fmp_api_key = api_keys["fmp_api_key"]
                configured_keys.append("FMP")

            if "polygon_api_key" in api_keys:
                obb.account.credentials.polygon_api_key = api_keys["polygon_api_key"]
                configured_keys.append("Polygon")

            if "alpha_vantage_api_key" in api_keys:
                obb.account.credentials.alpha_vantage_api_key = api_keys["alpha_vantage_api_key"]
                configured_keys.append("Alpha Vantage")

            if configured_keys:
                logger.info(f"🔑 OpenBB API keys configured for: {', '.join(configured_keys)}")
            else:
                logger.info("🔑 OpenBB initialized without API keys (using free tier)")

        except Exception as e:
            logger.warning(f"Could not configure OpenBB API keys: {e}", exc_info=True)
            raise

    async def _rate_limit(self) -> None:
        """Simple rate limiting to prevent API abuse."""
        import time
        current_time = time.time()
        time_since_last = current_time - self._rate_limiter["last_call"]
        if time_since_last < self._rate_limiter["min_interval"]:
            await asyncio.sleep(self._rate_limiter["min_interval"] - time_since_last)
        self._rate_limiter["last_call"] = time.time()

    async def get_quote_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote data from OpenBB.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')

        Returns:
            Dictionary with quote data or None if failed
        """
        if not self.openbb_available:
            logger.debug(f"OpenBB not available for quote data: {symbol}")
            return None

        if not symbol or not isinstance(symbol, str):
            logger.warning(f"Invalid symbol provided: {symbol}")
            return None

        try:
            await self._rate_limit()
            # Get quote data from OpenBB
            quote = obb.equity.price.quote(symbol=symbol.upper())

            if quote and hasattr(quote, "results") and quote.results:
                data = quote.results[0]

                return {
                    "symbol": symbol.upper(),
                    "bid": float(data.bid) if hasattr(data, "bid") and data.bid else 0.0,
                    "ask": float(data.ask) if hasattr(data, "ask") and data.ask else 0.0,
                    "bid_size": float(data.bid_size) if hasattr(data, "bid_size") and data.bid_size else 0.0,
                    "ask_size": float(data.ask_size) if hasattr(data, "ask_size") and data.ask_size else 0.0,
                    "last_price": float(data.last_price) if hasattr(data, "last_price") and data.last_price else 0.0,
                    "volume": float(data.volume) if hasattr(data, "volume") and data.volume else 0.0,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Error getting OpenBB quote data for {symbol}: {e}", exc_info=True)
            return None

    async def get_historical_data(
        self, symbol: str, timeframe: str, periods: int
    ) -> Optional[List[List[Union[int, float]]]]:
        """Get historical OHLCV data from OpenBB.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            timeframe: Time interval ('1m', '5m', '1h', '1d')
            periods: Number of periods to retrieve

        Returns:
            List of OHLCV data [timestamp_ms, open, high, low, close, volume] or None
        """
        if not self.openbb_available:
            logger.debug(f"OpenBB not available for historical data: {symbol}")
            return None

        if not symbol or not isinstance(symbol, str) or periods <= 0:
            logger.warning(f"Invalid parameters: symbol={symbol}, periods={periods}")
            return None

        try:
            await self._rate_limit()
            logger.debug(f"📊 Getting stock data for {symbol} via OpenBB")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=max(periods, 30))  # Ensure we have enough data

            data = obb.equity.price.historical(
                symbol=symbol.upper(),
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                interval=timeframe,
            )

            if data and hasattr(data, "results") and data.results:
                ohlcv = []
                for candle in data.results:
                    try:
                        timestamp = int(candle.date.timestamp() * 1000) if hasattr(candle.date, 'timestamp') else int(candle.date)
                        ohlcv.append([
                            timestamp,  # timestamp in ms
                            float(candle.open) if candle.open is not None else 0.0,
                            float(candle.high) if candle.high is not None else 0.0,
                            float(candle.low) if candle.low is not None else 0.0,
                            float(candle.close) if candle.close is not None else 0.0,
                            float(candle.volume) if hasattr(candle, "volume") and candle.volume is not None else 0.0,
                        ])
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"Skipping invalid candle data: {e}")
                        continue

                # Return only the requested number of periods (most recent)
                result = ohlcv[-periods:] if len(ohlcv) > periods else ohlcv
                logger.info(f"✅ Got {len(result)} candles for {symbol} via OpenBB")
                return result

        except Exception as e:
            logger.error(f"OpenBB historical data error for {symbol}: {e}", exc_info=True)
            return None

    async def get_institutional_ownership(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get institutional ownership data from OpenBB.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')

        Returns:
            Dictionary with institutional ownership data or None
        """
        if not self.openbb_available:
            logger.debug(f"OpenBB not available for institutional data: {symbol}")
            return None

        if not symbol or not isinstance(symbol, str):
            logger.warning(f"Invalid symbol provided: {symbol}")
            return None

        try:
            await self._rate_limit()
            ownership_data = obb.equity.ownership.institutional(symbol=symbol.upper())

            if ownership_data and hasattr(ownership_data, "results") and ownership_data.results:
                # Calculate total institutional ownership
                total_shares = 0.0
                holdings = []

                for holding in ownership_data.results[:10]:  # Top 10 holdings
                    try:
                        shares = float(holding.shares) if hasattr(holding, "shares") and holding.shares else 0.0
                        total_shares += shares

                        holdings.append({
                            "institution": str(holding.name) if hasattr(holding, "name") and holding.name else "Unknown",
                            "shares": shares,
                            "percentage": float(holding.percentage) if hasattr(holding, "percentage") and holding.percentage else 0.0,
                        })
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"Skipping invalid holding data: {e}")
                        continue

                return {
                    "symbol": symbol.upper(),
                    "total_institutional_shares": total_shares,
                    "holdings": holdings,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Error getting institutional ownership for {symbol}: {e}", exc_info=True)
            return None

    async def get_short_interest(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get short interest data from OpenBB.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')

        Returns:
            Dictionary with short interest data or None
        """
        if not self.openbb_available:
            logger.debug(f"OpenBB not available for short interest: {symbol}")
            return None

        if not symbol or not isinstance(symbol, str):
            logger.warning(f"Invalid symbol provided: {symbol}")
            return None

        try:
            await self._rate_limit()
            short_data = obb.equity.short_interest.short_interest(symbol=symbol.upper())

            if short_data and hasattr(short_data, "results") and short_data.results:
                latest_short = short_data.results[0]

                return {
                    "symbol": symbol.upper(),
                    "short_interest": float(latest_short.short_interest) if hasattr(latest_short, "short_interest") and latest_short.short_interest else 0.0,
                    "days_to_cover": float(latest_short.days_to_cover) if hasattr(latest_short, "days_to_cover") and latest_short.days_to_cover else 0.0,
                    "short_ratio": float(latest_short.short_ratio) if hasattr(latest_short, "short_ratio") and latest_short.short_ratio else 0.0,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Error getting short interest for {symbol}: {e}", exc_info=True)
            return None

    async def get_yfinance_data(
        self, symbol: str, timeframe: str, periods: int
    ) -> Optional[List[List[Union[int, float]]]]:
        """Fallback to yfinance for stock data when OpenBB is unavailable.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            timeframe: Time interval ('1m', '5m', '1h', '1d')
            periods: Number of periods to retrieve

        Returns:
            List of OHLCV data [timestamp_ms, open, high, low, close, volume] or None
        """
        if not YFINANCE_AVAILABLE:
            logger.debug("yfinance not available")
            return None

        if not symbol or not isinstance(symbol, str) or periods <= 0:
            logger.warning(f"Invalid parameters: symbol={symbol}, periods={periods}")
            return None

        try:
            logger.debug(f"📈 Trying yfinance fallback for {symbol}")
            ticker = yf.Ticker(symbol.upper())
            period_map = {"1m": "1d", "5m": "5d", "1h": "1mo", "1d": "1y"}
            period = period_map.get(timeframe, "1mo")

            hist = ticker.history(period=period, interval=timeframe)
            if not hist.empty:
                ohlcv = []
                for idx, row in hist.iterrows():
                    try:
                        # Handle NaN values
                        def safe_float(value):
                            if PANDAS_AVAILABLE and pd.isna(value):
                                return 0.0
                            try:
                                return float(value)
                            except (ValueError, TypeError):
                                return 0.0

                        ohlcv.append([
                            int(idx.timestamp() * 1000),
                            safe_float(row["Open"]),
                            safe_float(row["High"]),
                            safe_float(row["Low"]),
                            safe_float(row["Close"]),
                            safe_float(row["Volume"]),
                        ])
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping invalid yfinance data row: {e}")
                        continue

                result = ohlcv[-periods:] if len(ohlcv) > periods else ohlcv
                logger.info(f"✅ Got {len(result)} candles for {symbol} via yfinance")
                return result

        except Exception as e:
            logger.error(f"yfinance error for {symbol}: {e}", exc_info=True)
            return None

    def is_crypto_symbol(self, symbol: str) -> bool:
        """Determine if symbol is a cryptocurrency pair.

        Args:
            symbol: Symbol to check (e.g., 'BTC/USDT', 'AAPL')

        Returns:
            True if symbol appears to be a crypto pair, False otherwise
        """
        if not symbol or not isinstance(symbol, str):
            return False

        symbol_upper = symbol.upper()
        crypto_indicators = ["USDT", "USDC", "BTC", "ETH", "BUSD", "DAI"]

        return ("/" in symbol and
                any(pair in symbol_upper for pair in crypto_indicators))

    async def get_market_data(
        self, symbol: str, timeframe: str, periods: int
    ) -> Optional[List[List[Union[int, float]]]]:
        """
        Get market data using the best available source.
        First tries OpenBB for stocks, falls back to yfinance.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            timeframe: Time interval ('1m', '5m', '1h', '1d')
            periods: Number of periods to retrieve

        Returns:
            List of OHLCV data [timestamp_ms, open, high, low, close, volume] or None
        """
        # Skip crypto symbols - they should use crypto provider
        if self.is_crypto_symbol(symbol):
            logger.debug(f"Skipping crypto symbol {symbol} - use crypto provider instead")
            return None

        if not symbol or not isinstance(symbol, str) or periods <= 0:
            logger.warning(f"Invalid parameters: symbol={symbol}, periods={periods}")
            return None

        # Try OpenBB first
        logger.debug(f"Attempting to get market data for {symbol} via OpenBB")
        data = await self.get_historical_data(symbol, timeframe, periods)
        if data:
            return data

        # Fallback to yfinance
        logger.debug(f"OpenBB failed, falling back to yfinance for {symbol}")
        return await self.get_yfinance_data(symbol, timeframe, periods)
