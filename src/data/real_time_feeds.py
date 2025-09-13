"""
Real-time Market Data Feeds

Provides live market data streaming capabilities for real-time trading strategies.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional

import ccxt
from typing_extensions import Protocol

from .exceptions import ExchangeConnectionError, RateLimitExceededError

logger = logging.getLogger(__name__)


class DataFeed(Protocol):
    """Protocol for real-time data feeds."""

    async def subscribe(self, symbol: str, callback: Callable) -> None:
        """Subscribe to real-time data for a symbol."""
        ...

    async def unsubscribe(self, symbol: str) -> None:
        """Unsubscribe from real-time data for a symbol."""
        ...

    async def close(self) -> None:
        """Close the data feed connection."""
        ...


class WebSocketFeed:
    """Real-time WebSocket data feed for cryptocurrency exchanges."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize WebSocket data feed.

        Args:
            config: Configuration dictionary with exchange settings
        """
        self.config = config or {}
        self.exchange_config = self.config.get("exchange", {})
        self.rate_limit_delay = self.config.get("rate_limit_delay", 0.1)

        # Exchange connection
        self.exchange: Optional[ccxt.Exchange] = None
        self._initialize_exchange()

        # Active subscriptions
        self.subscriptions: Dict[str, Callable] = {}

        logger.info("WebSocketFeed initialized with config: %s", self.config)

    def _initialize_exchange(self) -> None:
        """Initialize exchange connection."""
        try:
            exchange_name = self.exchange_config.get("name", "binance")
            exchange_class = getattr(ccxt, exchange_name)
            self.exchange = exchange_class(
                {
                    "enableRateLimit": self.exchange_config.get(
                        "enableRateLimit", True
                    ),
                    "options": self.exchange_config.get("options", {}),
                    "apiKey": self.exchange_config.get("apiKey", ""),
                    "secret": self.exchange_config.get("secret", ""),
                }
            )

            logger.info("Exchange %s initialized successfully", exchange_name)
        except Exception as e:
            logger.error("Failed to initialize exchange: %s", e)
            raise ExchangeConnectionError(f"Failed to initialize exchange: {e}")

    async def subscribe(self, symbol: str, callback: Callable) -> None:
        """Subscribe to real-time data for a symbol.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            callback: Function to call when new data arrives
        """
        if not self.exchange:
            raise ExchangeConnectionError("Exchange not initialized")

        self.subscriptions[symbol] = callback
        logger.info("Subscribed to real-time data for %s", symbol)

    async def unsubscribe(self, symbol: str) -> None:
        """Unsubscribe from real-time data for a symbol.

        Args:
            symbol: Trading pair symbol to unsubscribe from
        """
        if symbol in self.subscriptions:
            del self.subscriptions[symbol]
            logger.info("Unsubscribed from real-time data for %s", symbol)

    async def fetch_ohlcv_stream(
        self, symbol: str, timeframe: str = "1m"
    ) -> Dict[str, Any]:
        """Fetch latest OHLCV data for a symbol.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe for OHLCV data

        Returns:
            Dictionary with OHLCV data
        """
        if not self.exchange:
            raise ExchangeConnectionError("Exchange not initialized")

        try:
            # Add rate limiting delay
            await asyncio.sleep(self.rate_limit_delay)

            # Fetch OHLCV data
            ohlcv = await asyncio.get_event_loop().run_in_executor(
                None, self.exchange.fetch_ohlcv, symbol, timeframe, None, 2
            )

            if not ohlcv or len(ohlcv) < 2:
                return {}

            # Get the latest complete candle
            latest_candle = ohlcv[-2]  # -1 is current incomplete candle

            return {
                "timestamp": latest_candle[0],
                "open": latest_candle[1],
                "high": latest_candle[2],
                "low": latest_candle[3],
                "close": latest_candle[4],
                "volume": latest_candle[5],
                "symbol": symbol,
                "timeframe": timeframe,
            }

        except ccxt.RateLimitExceeded:
            logger.warning("Rate limit exceeded for %s", symbol)
            raise RateLimitExceededError(f"Rate limit exceeded for {symbol}")
        except Exception as e:
            logger.error("Error fetching OHLCV data for %s: %s", symbol, e)
            raise ExchangeConnectionError(f"Error fetching OHLCV data: {e}")

    async def fetch_orderbook_stream(
        self, symbol: str, limit: int = 20
    ) -> Dict[str, Any]:
        """Fetch latest orderbook data for a symbol.

        Args:
            symbol: Trading pair symbol
            limit: Number of orderbook levels to fetch

        Returns:
            Dictionary with orderbook data
        """
        if not self.exchange:
            raise ExchangeConnectionError("Exchange not initialized")

        try:
            # Add rate limiting delay
            await asyncio.sleep(self.rate_limit_delay)

            # Fetch orderbook data
            orderbook = await asyncio.get_event_loop().run_in_executor(
                None, self.exchange.fetch_order_book, symbol, limit
            )

            return {
                "bids": orderbook["bids"],
                "asks": orderbook["asks"],
                "timestamp": orderbook["timestamp"],
                "symbol": symbol,
            }

        except ccxt.RateLimitExceeded:
            logger.warning("Rate limit exceeded for orderbook %s", symbol)
            raise RateLimitExceededError(f"Rate limit exceeded for orderbook {symbol}")
        except Exception as e:
            logger.error("Error fetching orderbook data for %s: %s", symbol, e)
            raise ExchangeConnectionError(f"Error fetching orderbook data: {e}")

    async def run_feeds(self) -> None:
        """Run all active data feeds."""
        if not self.exchange:
            raise ExchangeConnectionError("Exchange not initialized")

        while self.subscriptions:
            try:
                # Process each subscription
                for symbol, callback in list(self.subscriptions.items()):
                    try:
                        # Fetch latest data
                        data = await self.fetch_ohlcv_stream(symbol)
                        if data:
                            # Call the callback with the new data
                            await callback(data)
                    except RateLimitExceededError:
                        # Slow down and continue
                        await asyncio.sleep(1)
                        continue
                    except Exception as e:
                        logger.error("Error processing feed for %s: %s", symbol, e)

                # Wait before next cycle
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                logger.info("Data feeds cancelled")
                break
            except Exception as e:
                logger.error("Error in data feeds loop: %s", e)
                await asyncio.sleep(5)  # Wait before retrying

    async def close(self) -> None:
        """Close the data feed connection."""
        self.subscriptions.clear()
        if self.exchange:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.exchange.close
                )
            except Exception as e:
                logger.warning("Error closing exchange connection: %s", e)
        logger.info("WebSocketFeed closed")


class RealTimeFeedsManager:
    """Manager for multiple real-time data feeds."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize real-time feeds manager.

        Args:
            config: Configuration dictionary with feed settings
        """
        self.config = config or {}
        self.feed_config = self.config.get("feeds", {})

        # Data feed instances
        self.feeds: Dict[str, DataFeed] = {}

        logger.info("RealTimeFeedsManager initialized")

    async def add_feed(self, feed_id: str, feed: DataFeed) -> None:
        """Add a data feed to the manager.

        Args:
            feed_id: Unique identifier for the feed
            feed: Data feed instance
        """
        self.feeds[feed_id] = feed
        logger.info("Added feed %s", feed_id)

    async def remove_feed(self, feed_id: str) -> None:
        """Remove a data feed from the manager.

        Args:
            feed_id: Unique identifier for the feed
        """
        if feed_id in self.feeds:
            await self.feeds[feed_id].close()
            del self.feeds[feed_id]
            logger.info("Removed feed %s", feed_id)

    async def start_all_feeds(self) -> None:
        """Start all managed data feeds."""
        logger.info("Starting all data feeds")
        # In a more complex implementation, we would start all feeds here
        # For now, this is a placeholder for future expansion

    async def stop_all_feeds(self) -> None:
        """Stop all managed data feeds."""
        logger.info("Stopping all data feeds")
        for feed_id, feed in list(self.feeds.items()):
            await self.remove_feed(feed_id)

    async def close(self) -> None:
        """Close all data feeds."""
        await self.stop_all_feeds()
        logger.info("All data feeds closed")
