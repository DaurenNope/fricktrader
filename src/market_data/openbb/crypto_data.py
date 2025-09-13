"""
Cryptocurrency data provider using CCXT
Handles crypto market data, order books, and exchange integration
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    ccxt = None

from .data_formatter import MarketDepthData

logger = logging.getLogger(__name__)


class CryptoDataProvider:
    """
    Cryptocurrency data provider using CCXT
    Provides order book data and market information for crypto pairs
    """

    def __init__(self, openbb_client=None):
        """Initialize crypto data provider with CCXT integration.

        Args:
            openbb_client: Optional OpenBB client for integration
        """
        self.openbb_client = openbb_client
        self.exchange = None
        self._rate_limiter = {"last_call": 0, "min_interval": 0.1}  # Rate limiting
        self._init_ccxt_exchange()

    def _init_ccxt_exchange(self) -> None:
        """Initialize CCXT exchange for crypto data.

        Raises:
            Exception: If CCXT exchange initialization fails
        """
        if not CCXT_AVAILABLE:
            logger.warning("CCXT not available - crypto data will not be accessible")
            self.exchange = None
            return

        try:
            # Initialize CCXT for crypto data (no API keys needed for public data)
            self.exchange = ccxt.binance({
                "enableRateLimit": True,
                "sandbox": False,  # Use live data for public endpoints
                "timeout": 15000,  # 15 second timeout
                "rateLimit": 1200,  # 1.2 seconds between requests
                "verbose": False,  # Reduce logging noise
            })

            # Test the connection
            self.exchange.load_markets()
            logger.info("📈 CCXT exchange initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize CCXT exchange: {e}", exc_info=True)
            self.exchange = None

    def is_crypto_symbol(self, symbol: str) -> bool:
        """Check if symbol is a cryptocurrency pair.

        Args:
            symbol: Symbol to check (e.g., 'BTC/USDT', 'AAPL')

        Returns:
            True if symbol appears to be a crypto pair, False otherwise
        """
        if not symbol or not isinstance(symbol, str):
            return False

        symbol_upper = symbol.upper()
        crypto_indicators = ["USDT", "USDC", "BTC", "ETH", "BUSD", "DAI", "USDC"]

        return ("/" in symbol and
                any(pair in symbol_upper for pair in crypto_indicators))

    async def _rate_limit(self) -> None:
        """Simple rate limiting to prevent API abuse."""
        import time
        current_time = time.time()
        time_since_last = current_time - self._rate_limiter["last_call"]
        if time_since_last < self._rate_limiter["min_interval"]:
            await asyncio.sleep(self._rate_limiter["min_interval"] - time_since_last)
        self._rate_limiter["last_call"] = time.time()

    async def get_order_book(
        self, symbol: str, exchange_name: str = "binance"
    ) -> Optional[MarketDepthData]:
        """Get order book data for crypto symbol.

        Args:
            symbol: Crypto trading pair (e.g., 'BTC/USDT')
            exchange_name: Exchange name (default: 'binance')

        Returns:
            MarketDepthData object with order book information or None
        """
        if not self.exchange:
            logger.debug(f"CCXT exchange not available for order book: {symbol}")
            return None

        if not symbol or not isinstance(symbol, str):
            logger.warning(f"Invalid symbol provided: {symbol}")
            return None

        try:
            await self._rate_limit()
            # Get order book
            orderbook = self.exchange.fetch_order_book(symbol.upper(), limit=20)

            # Process bids and asks safely
            bids = []
            asks = []

            for bid in orderbook.get("bids", [])[:10]:
                try:
                    bids.append((float(bid[0]), float(bid[1])))
                except (ValueError, IndexError, TypeError) as e:
                    logger.warning(f"Skipping invalid bid data: {e}")
                    continue

            for ask in orderbook.get("asks", [])[:10]:
                try:
                    asks.append((float(ask[0]), float(ask[1])))
                except (ValueError, IndexError, TypeError) as e:
                    logger.warning(f"Skipping invalid ask data: {e}")
                    continue

            if bids and asks:
                best_bid = bids[0][0]
                best_ask = asks[0][0]
                spread = best_ask - best_bid
                mid_price = (best_bid + best_ask) / 2.0

                total_bid_volume = sum(bid[1] for bid in bids)
                total_ask_volume = sum(ask[1] for ask in asks)
                imbalance_ratio = (
                    total_bid_volume / (total_bid_volume + total_ask_volume)
                    if (total_bid_volume + total_ask_volume) > 0 else 0.5
                )

                return MarketDepthData(
                    bids=bids,
                    asks=asks,
                    timestamp=datetime.now(),
                    spread=spread,
                    mid_price=mid_price,
                    total_bid_volume=total_bid_volume,
                    total_ask_volume=total_ask_volume,
                    imbalance_ratio=imbalance_ratio,
                )

        except Exception as e:
            logger.error(f"Error getting CCXT order book data for {symbol}: {e}", exc_info=True)
            return None

    async def get_ohlcv_data(
        self, symbol: str, timeframe: str, periods: int
    ) -> Optional[List[List[Union[int, float]]]]:
        """Get OHLCV data for crypto symbol.

        Args:
            symbol: Crypto trading pair (e.g., 'BTC/USDT')
            timeframe: Time interval ('1m', '5m', '1h', '1d', '4h')
            periods: Number of periods to retrieve

        Returns:
            List of OHLCV data [timestamp_ms, open, high, low, close, volume] or None
        """
        if not self.exchange:
            logger.debug(f"CCXT exchange not available for OHLCV: {symbol}")
            return None

        if not symbol or not isinstance(symbol, str) or periods <= 0:
            logger.warning(f"Invalid parameters: symbol={symbol}, periods={periods}")
            return None

        try:
            await self._rate_limit()
            logger.debug(f"📈 Getting crypto data for {symbol} via CCXT")

            # Map timeframe for CCXT (ensure compatibility)
            timeframe_map = {
                "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
                "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h",
                "8h": "8h", "12h": "12h", "1d": "1d", "3d": "3d", "1w": "1w"
            }
            ccxt_timeframe = timeframe_map.get(timeframe, timeframe)

            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(
                symbol.upper(),
                ccxt_timeframe,
                limit=min(periods, 1000)  # Limit to prevent excessive requests
            )

            if ohlcv and len(ohlcv) > 0:
                # Validate and clean data
                cleaned_ohlcv = []
                for candle in ohlcv:
                    try:
                        if len(candle) >= 6:  # [timestamp, o, h, l, c, v]
                            cleaned_candle = [
                                int(candle[0]),  # timestamp
                                float(candle[1]) if candle[1] is not None else 0.0,  # open
                                float(candle[2]) if candle[2] is not None else 0.0,  # high
                                float(candle[3]) if candle[3] is not None else 0.0,  # low
                                float(candle[4]) if candle[4] is not None else 0.0,  # close
                                float(candle[5]) if candle[5] is not None else 0.0,  # volume
                            ]
                            cleaned_ohlcv.append(cleaned_candle)
                    except (ValueError, TypeError, IndexError) as e:
                        logger.warning(f"Skipping invalid candle data: {e}")
                        continue

                result = cleaned_ohlcv[-periods:] if len(cleaned_ohlcv) > periods else cleaned_ohlcv
                logger.info(f"✅ Got {len(result)} candles for {symbol}")
                return result
            else:
                logger.warning(f"Empty OHLCV data for {symbol}")
                return None

        except Exception as e:
            logger.error(f"CCXT error for {symbol}: {e}", exc_info=True)

            # Try alternative symbol format if original failed
            if "/" in symbol:
                try:
                    alt_symbol = symbol.replace("/", "")
                    logger.debug(f"Trying alternative symbol format: {alt_symbol}")
                    await self._rate_limit()
                    ohlcv = self.exchange.fetch_ohlcv(alt_symbol, ccxt_timeframe, limit=min(periods, 1000))
                    if ohlcv and len(ohlcv) > 0:
                        logger.info(f"✅ Got {len(ohlcv)} candles for {alt_symbol}")
                        return ohlcv
                except Exception as e2:
                    logger.debug(f"Alternative symbol format failed: {e2}")

            return None

    async def get_ticker_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get ticker data for crypto symbol.

        Args:
            symbol: Crypto trading pair (e.g., 'BTC/USDT')

        Returns:
            Dictionary with ticker data or None
        """
        if not self.exchange:
            logger.debug(f"CCXT exchange not available for ticker: {symbol}")
            return None

        if not symbol or not isinstance(symbol, str):
            logger.warning(f"Invalid symbol provided: {symbol}")
            return None

        try:
            await self._rate_limit()
            ticker = self.exchange.fetch_ticker(symbol.upper())
            if ticker:
                def safe_float(value, default=0.0):
                    try:
                        return float(value) if value is not None else default
                    except (ValueError, TypeError):
                        return default

                return {
                    "symbol": symbol.upper(),
                    "last_price": safe_float(ticker.get("last")),
                    "bid": safe_float(ticker.get("bid")),
                    "ask": safe_float(ticker.get("ask")),
                    "volume": safe_float(ticker.get("baseVolume")),
                    "quote_volume": safe_float(ticker.get("quoteVolume")),
                    "change_24h": safe_float(ticker.get("change")),
                    "change_percent_24h": safe_float(ticker.get("percentage")),
                    "high_24h": safe_float(ticker.get("high")),
                    "low_24h": safe_float(ticker.get("low")),
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Error getting ticker data for {symbol}: {e}", exc_info=True)
            return None

    async def get_supported_symbols(self) -> List[str]:
        """Get list of supported crypto symbols.

        Returns:
            List of supported trading pairs (e.g., ['BTC/USDT', 'ETH/USDT', ...])
        """
        if not self.exchange:
            logger.debug("CCXT exchange not available for supported symbols")
            return []

        try:
            await self._rate_limit()
            markets = self.exchange.load_markets()
            if not markets:
                logger.warning("No markets loaded from exchange")
                return []

            symbols = list(markets.keys())
            logger.debug(f"Loaded {len(symbols)} symbols from exchange")

            # Filter for major stablecoin pairs and sort by popularity
            stable_pairs = []
            major_pairs = []

            for symbol in symbols:
                symbol_upper = symbol.upper()
                if "/USDT" in symbol_upper:
                    # Prioritize major cryptocurrencies
                    base_currency = symbol_upper.split("/")[0]
                    if base_currency in ["BTC", "ETH", "BNB", "ADA", "SOL", "XRP", "DOGE", "MATIC", "DOT", "AVAX"]:
                        major_pairs.append(symbol)
                    else:
                        stable_pairs.append(symbol)
                elif any(stable in symbol_upper for stable in ["/USDC", "/BUSD", "/DAI"]):
                    stable_pairs.append(symbol)

            # Return major pairs first, then others, limited to reasonable number
            result = major_pairs[:20] + stable_pairs[:30]
            logger.info(f"Returning {len(result)} supported symbols")
            return result

        except Exception as e:
            logger.error(f"Error getting supported symbols: {e}", exc_info=True)
            return []

    async def get_market_status(self) -> Dict[str, Any]:
        """Get exchange market status.

        Returns:
            Dictionary with market status information
        """
        if not self.exchange:
            return {
                "status": "unavailable",
                "message": "Exchange not initialized",
                "timestamp": datetime.now().isoformat()
            }

        try:
            await self._rate_limit()
            status = self.exchange.fetch_status()

            result = {
                "status": status.get("status", "unknown"),
                "updated": status.get("updated"),
                "eta": status.get("eta"),
                "url": status.get("url"),
                "exchange": self.exchange.name,
                "timestamp": datetime.now().isoformat(),
            }

            # Add additional health check
            if result["status"] == "unknown":
                # Try a simple market check to verify connectivity
                try:
                    markets = self.exchange.load_markets()
                    result["status"] = "ok" if markets else "degraded"
                    result["markets_count"] = len(markets) if markets else 0
                except Exception:
                    result["status"] = "error"

            return result

        except Exception as e:
            logger.error(f"Error getting market status: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_exchange_info(self) -> Dict[str, Any]:
        """Get detailed exchange information and capabilities.

        Returns:
            Dictionary with exchange information and supported features
        """
        if not self.exchange:
            return {
                "name": "unavailable",
                "available": False,
                "timestamp": datetime.now().isoformat()
            }

        try:
            # Get basic exchange info
            info = {
                "name": getattr(self.exchange, "name", "Unknown"),
                "id": getattr(self.exchange, "id", "unknown"),
                "countries": getattr(self.exchange, "countries", []),
                "rateLimit": getattr(self.exchange, "rateLimit", 0),
                "timeout": getattr(self.exchange, "timeout", 0),
                "available": True,
                "timestamp": datetime.now().isoformat()
            }

            # Get supported features
            has_features = getattr(self.exchange, "has", {})
            if isinstance(has_features, dict):
                # Filter to relevant features
                relevant_features = [
                    "fetchOrderBook", "fetchTicker", "fetchTickers",
                    "fetchOHLCV", "fetchTrades", "fetchMyTrades",
                    "createOrder", "cancelOrder", "fetchBalance"
                ]
                info["features"] = {
                    feature: has_features.get(feature, False)
                    for feature in relevant_features
                    if feature in has_features
                }
            else:
                info["features"] = {}

            # Get API endpoints info if available
            if hasattr(self.exchange, "urls") and isinstance(self.exchange.urls, dict):
                info["urls"] = {
                    "api": self.exchange.urls.get("api", {}),
                    "www": self.exchange.urls.get("www", ""),
                    "doc": self.exchange.urls.get("doc", "")
                }

            return info

        except Exception as e:
            logger.error(f"Error getting exchange info: {e}", exc_info=True)
            return {
                "name": "error",
                "available": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
