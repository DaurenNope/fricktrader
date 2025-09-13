"""
Market analysis and indicators module
Handles delta analysis, volume profile, institutional data, and comprehensive analysis
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

from .data_formatter import (
    DataFormatter,
    MarketDepthData,
    DeltaAnalysis,
    VolumeProfile,
    InstitutionalData,
)

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """
    Advanced market analysis combining order flow, delta analysis, and institutional data
    """

    def __init__(self, openbb_client, crypto_provider):
        """Initialize market analyzer with data providers.

        Args:
            openbb_client: OpenBB client for stock data
            crypto_provider: Crypto data provider for crypto markets
        """
        self.openbb_client = openbb_client
        self.crypto_provider = crypto_provider
        self.formatter = DataFormatter()

        # Validate pandas availability for analysis
        if not PANDAS_AVAILABLE:
            logger.warning("Pandas not available - some analysis features may be limited")

    async def get_market_depth(
        self, symbol: str, exchange: str = "binance"
    ) -> Optional[MarketDepthData]:
        """
        Get real-time order book depth data.
        Similar to Tiger Trade's Level 2 data.

        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT' or 'AAPL')
            exchange: Exchange name for crypto symbols (default: 'binance')

        Returns:
            MarketDepthData object with order book information or None
        """
        if not symbol or not isinstance(symbol, str):
            logger.warning(f"Invalid symbol provided: {symbol}")
            return None

        cache_key = f"depth_{symbol.upper()}_{exchange}"
        cached_data = self.formatter.get_cached_data(cache_key)
        if cached_data:
            logger.debug(f"Returning cached market depth for {symbol}")
            return cached_data

        try:
            # Determine if this is a crypto symbol
            is_crypto = self.crypto_provider.is_crypto_symbol(symbol)
            depth_data = None

            if is_crypto and self.crypto_provider.exchange:
                logger.debug(f"Getting crypto market depth for {symbol}")
                # Use CCXT for crypto market depth
                depth_data = await self.crypto_provider.get_order_book(symbol, exchange)
            elif not is_crypto and self.openbb_client.openbb_available:
                logger.debug(f"Getting stock market depth for {symbol}")
                # Use OpenBB for stock market depth (quote data)
                depth_data = await self._get_openbb_depth(symbol)
            else:
                logger.warning(f"No suitable data source for market depth: {symbol} (crypto: {is_crypto})")
                return None

            if depth_data:
                self.formatter.cache_data(cache_key, depth_data)
                logger.debug(f"Successfully retrieved market depth for {symbol}")
                return depth_data
            else:
                logger.debug(f"No market depth data available for {symbol}")

        except Exception as e:
            logger.error(f"Error getting market depth for {symbol}: {e}", exc_info=True)

        return None

    async def _get_openbb_depth(self, symbol: str) -> Optional[MarketDepthData]:
        """Get market depth using OpenBB quote data.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')

        Returns:
            MarketDepthData object with simplified order book or None
        """
        try:
            quote_data = await self.openbb_client.get_quote_data(symbol)

            if quote_data and isinstance(quote_data, dict):
                bid_price = float(quote_data.get("bid", 0))
                ask_price = float(quote_data.get("ask", 0))
                bid_size = float(quote_data.get("bid_size", 0))
                ask_size = float(quote_data.get("ask_size", 0))

                if bid_price > 0 and ask_price > 0 and ask_price > bid_price:
                    # Create simplified order book
                    bids = [(bid_price, max(bid_size, 1.0))]  # Ensure minimum size
                    asks = [(ask_price, max(ask_size, 1.0))]

                    spread = ask_price - bid_price
                    mid_price = (bid_price + ask_price) / 2.0
                    total_bid_volume = max(bid_size, 1.0)
                    total_ask_volume = max(ask_size, 1.0)
                    imbalance_ratio = (
                        total_bid_volume / (total_bid_volume + total_ask_volume)
                        if (total_bid_volume + total_ask_volume) > 0
                        else 0.5
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
                else:
                    logger.warning(f"Invalid quote data for {symbol}: bid={bid_price}, ask={ask_price}")
            else:
                logger.debug(f"No quote data available for {symbol}")

        except Exception as e:
            logger.error(f"Error getting OpenBB depth data for {symbol}: {e}", exc_info=True)

        return None

    async def get_delta_analysis(
        self, symbol: str, timeframe: str = "1m", periods: int = 100
    ) -> Optional[DeltaAnalysis]:
        """
        Advanced delta and order flow analysis.
        Similar to Tiger Trade's delta analysis tools.

        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT' or 'AAPL')
            timeframe: Time interval ('1m', '5m', '1h', '1d')
            periods: Number of periods to analyze

        Returns:
            DeltaAnalysis object with order flow metrics or None
        """
        if not symbol or not isinstance(symbol, str) or periods <= 0:
            logger.warning(f"Invalid parameters: symbol={symbol}, periods={periods}")
            return None

        if not PANDAS_AVAILABLE:
            logger.warning(f"Pandas not available - cannot perform delta analysis for {symbol}")
            return None

        cache_key = f"delta_{symbol.upper()}_{timeframe}_{periods}"
        cached_data = self.formatter.get_cached_data(cache_key)
        if cached_data:
            logger.debug(f"Returning cached delta analysis for {symbol}")
            return cached_data

        try:
            # Get OHLCV data
            logger.debug(f"Getting OHLCV data for delta analysis: {symbol}")
            ohlcv_data = await self._get_ohlcv_data(symbol, timeframe, periods)
            if not ohlcv_data or len(ohlcv_data) < 10:  # Need minimum data for analysis
                logger.warning(f"Insufficient OHLCV data for delta analysis: {symbol} (got {len(ohlcv_data) if ohlcv_data else 0} candles)")
                return None

            # Create DataFrame with proper error handling
            try:
                df = pd.DataFrame(
                    ohlcv_data,
                    columns=["timestamp", "open", "high", "low", "close", "volume"],
                )
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

                # Validate data quality
                if df.empty or df["close"].isna().all():
                    logger.warning(f"Invalid OHLCV data for {symbol}")
                    return None

            except Exception as e:
                logger.error(f"Error creating DataFrame for {symbol}: {e}")
                return None

            # Calculate delta metrics
            logger.debug(f"Calculating delta metrics for {symbol}")
            delta_analysis = self.formatter.calculate_delta_metrics(df)

            if delta_analysis:
                self.formatter.cache_data(cache_key, delta_analysis)
                logger.debug(f"Successfully calculated delta analysis for {symbol}")
                return delta_analysis
            else:
                logger.warning(f"Failed to calculate delta metrics for {symbol}")

        except Exception as e:
            logger.error(f"Error calculating delta analysis for {symbol}: {e}", exc_info=True)

        return None

    async def get_volume_profile(
        self, symbol: str, timeframe: str = "1h", periods: int = 100
    ) -> Optional[VolumeProfile]:
        """
        Volume profile analysis showing volume distribution by price levels.

        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT' or 'AAPL')
            timeframe: Time interval ('1m', '5m', '1h', '1d')
            periods: Number of periods to analyze

        Returns:
            VolumeProfile object with volume distribution metrics or None
        """
        if not symbol or not isinstance(symbol, str) or periods <= 0:
            logger.warning(f"Invalid parameters: symbol={symbol}, periods={periods}")
            return None

        if not PANDAS_AVAILABLE:
            logger.warning(f"Pandas not available - cannot perform volume profile analysis for {symbol}")
            return None

        cache_key = f"volume_profile_{symbol.upper()}_{timeframe}_{periods}"
        cached_data = self.formatter.get_cached_data(cache_key)
        if cached_data:
            logger.debug(f"Returning cached volume profile for {symbol}")
            return cached_data

        try:
            # Get OHLCV data
            logger.debug(f"Getting OHLCV data for volume profile: {symbol}")
            ohlcv_data = await self._get_ohlcv_data(symbol, timeframe, periods)
            if not ohlcv_data or len(ohlcv_data) < 5:  # Need minimum data
                logger.warning(f"Insufficient OHLCV data for volume profile: {symbol} (got {len(ohlcv_data) if ohlcv_data else 0} candles)")
                return None

            # Create DataFrame with proper error handling
            try:
                df = pd.DataFrame(
                    ohlcv_data,
                    columns=["timestamp", "open", "high", "low", "close", "volume"],
                )

                # Validate data quality
                if df.empty or df[["close", "volume"]].isna().all().any():
                    logger.warning(f"Invalid OHLCV data for volume profile: {symbol}")
                    return None

            except Exception as e:
                logger.error(f"Error creating DataFrame for volume profile {symbol}: {e}")
                return None

            # Calculate volume profile
            logger.debug(f"Calculating volume profile for {symbol}")
            volume_profile = self.formatter.calculate_volume_profile(df)

            if volume_profile:
                self.formatter.cache_data(cache_key, volume_profile)
                logger.debug(f"Successfully calculated volume profile for {symbol}")
                return volume_profile
            else:
                logger.warning(f"Failed to calculate volume profile for {symbol}")

        except Exception as e:
            logger.error(f"Error calculating volume profile for {symbol}: {e}", exc_info=True)

        return None

    async def get_institutional_data(self, symbol: str) -> Optional[InstitutionalData]:
        """
        Get institutional trading data including dark pools, block trades, and ownership data.

        Args:
            symbol: Trading symbol (typically stocks, crypto symbols return limited data)

        Returns:
            InstitutionalData object with institutional metrics or None
        """
        if not symbol or not isinstance(symbol, str):
            logger.warning(f"Invalid symbol provided: {symbol}")
            return None

        cache_key = f"institutional_{symbol.upper()}"
        cached_data = self.formatter.get_cached_data(cache_key, duration=3600)  # 1 hour cache
        if cached_data:
            logger.debug(f"Returning cached institutional data for {symbol}")
            return cached_data

        try:
            institutional_data = None

            # Skip institutional data for crypto symbols (not typically available)
            is_crypto = self.crypto_provider.is_crypto_symbol(symbol)
            if not is_crypto and self.openbb_client.openbb_available:
                logger.debug(f"Getting OpenBB institutional data for {symbol}")
                institutional_data = await self._get_openbb_institutional_data(symbol)
            elif is_crypto:
                logger.debug(f"Skipping institutional data for crypto symbol: {symbol}")

            if not institutional_data:
                # Fallback to estimated institutional data based on volume patterns
                logger.debug(f"Falling back to estimated institutional data for {symbol}")
                institutional_data = await self._estimate_institutional_data(symbol)

            if institutional_data:
                self.formatter.cache_data(cache_key, institutional_data)
                logger.debug(f"Successfully retrieved institutional data for {symbol}")
                return institutional_data
            else:
                logger.debug(f"No institutional data available for {symbol}")

        except Exception as e:
            logger.error(f"Error getting institutional data for {symbol}: {e}", exc_info=True)

        return None

    async def _get_openbb_institutional_data(
        self, symbol: str
    ) -> Optional[InstitutionalData]:
        """Get institutional data using OpenBB APIs.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')

        Returns:
            InstitutionalData object with available institutional metrics or None
        """
        try:
            # Get institutional ownership and short interest data concurrently
            logger.debug(f"Fetching institutional ownership and short interest for {symbol}")

            tasks = [
                self.openbb_client.get_institutional_ownership(symbol),
                self.openbb_client.get_short_interest(symbol)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)
            ownership_data, short_data = results

            # Handle exceptions in results
            if isinstance(ownership_data, Exception):
                logger.warning(f"Failed to get ownership data: {ownership_data}")
                ownership_data = None

            if isinstance(short_data, Exception):
                logger.warning(f"Failed to get short interest data: {short_data}")
                short_data = None

            # Compile institutional data with safe defaults
            institutional_ownership = 0.0
            float_short = 0.0
            days_to_cover = 0.0

            if ownership_data and isinstance(ownership_data, dict):
                institutional_ownership = float(ownership_data.get("total_institutional_shares", 0.0))

            if short_data and isinstance(short_data, dict):
                float_short = float(short_data.get("short_interest", 0.0))
                days_to_cover = float(short_data.get("days_to_cover", 0.0))

            return InstitutionalData(
                dark_pool_volume=0.0,  # Not available in free APIs
                block_trades=[],  # Not available in free APIs
                unusual_options_activity=[],  # Not available in free APIs
                insider_trading=[],  # Could be added with SEC data in the future
                institutional_ownership=institutional_ownership,
                float_short=float_short,
                days_to_cover=days_to_cover,
            )

        except Exception as e:
            logger.error(f"Error getting OpenBB institutional data for {symbol}: {e}", exc_info=True)
            return None

    async def _estimate_institutional_data(
        self, symbol: str
    ) -> Optional[InstitutionalData]:
        """Estimate institutional data using volume pattern analysis.

        Args:
            symbol: Trading symbol to analyze

        Returns:
            InstitutionalData object with estimated metrics or None
        """
        if not PANDAS_AVAILABLE:
            logger.warning(f"Pandas not available - cannot estimate institutional data for {symbol}")
            return None

        try:
            # Get basic volume data to estimate institutional activity
            logger.debug(f"Getting volume data for institutional estimation: {symbol}")
            ohlcv_data = await self._get_ohlcv_data(symbol, "1h", 24)
            if not ohlcv_data or len(ohlcv_data) < 5:
                logger.debug(f"Insufficient volume data for institutional estimation: {symbol}")
                return None

            try:
                df = pd.DataFrame(
                    ohlcv_data,
                    columns=["timestamp", "open", "high", "low", "close", "volume"],
                )

                # Validate data
                if df.empty or df["volume"].isna().all():
                    logger.warning(f"Invalid volume data for {symbol}")
                    return None

            except Exception as e:
                logger.error(f"Error creating DataFrame for institutional estimation {symbol}: {e}")
                return None

            # Calculate volume-based metrics
            total_volume = df["volume"].sum()
            if total_volume <= 0:
                logger.debug(f"No volume data available for {symbol}")
                return None

            # Estimate dark pool volume (typically 30-40% of total volume)
            estimated_dark_pool = float(total_volume * 0.35)

            # Identify potential block trades (large volume spikes)
            volume_threshold = df["volume"].quantile(0.95)  # Top 5% volume
            block_trades = []

            try:
                high_volume_bars = df[df["volume"] > volume_threshold]
                for _, row in high_volume_bars.iterrows():
                    block_trades.append({
                        "timestamp": str(row["timestamp"]) if "timestamp" in row else datetime.now().isoformat(),
                        "volume": float(row["volume"]),
                        "price": float(row["close"]),
                        "estimated_size": float(row["volume"] * row["close"]),
                        "type": "estimated_block_trade"
                    })
            except Exception as e:
                logger.warning(f"Error identifying block trades for {symbol}: {e}")
                block_trades = []

            return InstitutionalData(
                dark_pool_volume=estimated_dark_pool,
                block_trades=block_trades,
                unusual_options_activity=[],  # Not available for estimation
                insider_trading=[],  # Not available for estimation
                institutional_ownership=0.0,  # Not available for estimation
                float_short=0.0,  # Not available for estimation
                days_to_cover=0.0,  # Not available for estimation
            )

        except Exception as e:
            logger.error(f"Error estimating institutional data for {symbol}: {e}", exc_info=True)
            return None

    async def _get_ohlcv_data(
        self, symbol: str, timeframe: str, periods: int
    ) -> Optional[List[List[Union[int, float]]]]:
        """Get OHLCV data from the best available source.

        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT' or 'AAPL')
            timeframe: Time interval ('1m', '5m', '1h', '1d')
            periods: Number of periods to retrieve

        Returns:
            List of OHLCV data [timestamp_ms, open, high, low, close, volume] or None
        """
        if not symbol or not isinstance(symbol, str) or periods <= 0:
            logger.warning(f"Invalid parameters for OHLCV data: symbol={symbol}, periods={periods}")
            return None

        try:
            # Determine if this is a crypto symbol
            is_crypto = self.crypto_provider.is_crypto_symbol(symbol)
            logger.debug(f"Getting OHLCV data for {symbol} (crypto: {is_crypto})")

            if is_crypto and self.crypto_provider.exchange:
                # Use crypto provider for crypto symbols
                logger.debug(f"Using crypto provider for {symbol}")
                data = await self.crypto_provider.get_ohlcv_data(symbol, timeframe, periods)
            elif not is_crypto and self.openbb_client.openbb_available:
                # Use OpenBB client for stock symbols
                logger.debug(f"Using OpenBB client for {symbol}")
                data = await self.openbb_client.get_market_data(symbol, timeframe, periods)
            else:
                logger.warning(f"No suitable data source for OHLCV: {symbol} (crypto: {is_crypto})")
                return None

            if data:
                logger.debug(f"Successfully retrieved {len(data)} OHLCV records for {symbol}")
            else:
                logger.debug(f"No OHLCV data available for {symbol}")

            return data

        except Exception as e:
            logger.error(f"Error getting OHLCV data for {symbol}: {e}", exc_info=True)
            return None

    async def get_comprehensive_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive market analysis combining all data sources.
        Similar to Tiger Trade's comprehensive market view.

        Args:
            symbol: Trading symbol to analyze (e.g., 'BTC/USDT' or 'AAPL')

        Returns:
            Dictionary with comprehensive market analysis data
        """
        if not symbol or not isinstance(symbol, str):
            return {"error": "Invalid symbol provided", "symbol": symbol}

        try:
            logger.info(f"🔍 Getting comprehensive analysis for {symbol}")

            # Gather all data concurrently with timeout
            tasks = [
                self.get_market_depth(symbol),
                self.get_delta_analysis(symbol),
                self.get_volume_profile(symbol),
                self.get_institutional_data(symbol),
            ]

            # Use timeout to prevent hanging
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=30.0  # 30 second timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Comprehensive analysis timeout for {symbol}")
                results = [None, None, None, None]

            market_depth, delta_analysis, volume_profile, institutional_data = results

            # Handle exceptions in results
            def safe_extract(result, result_name):
                if isinstance(result, Exception):
                    logger.warning(f"Error in {result_name} for {symbol}: {result}")
                    return None
                return result

            market_depth = safe_extract(market_depth, "market_depth")
            delta_analysis = safe_extract(delta_analysis, "delta_analysis")
            volume_profile = safe_extract(volume_profile, "volume_profile")
            institutional_data = safe_extract(institutional_data, "institutional_data")

            # Compile comprehensive analysis with safe serialization
            def safe_dict(obj):
                if obj and hasattr(obj, '__dict__'):
                    try:
                        return obj.__dict__
                    except Exception as e:
                        logger.warning(f"Error serializing object: {e}")
                        return {"error": f"Serialization failed: {str(e)}"}
                return None

            analysis = {
                "symbol": symbol.upper(),
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "data_sources": {
                    "market_depth_available": market_depth is not None,
                    "delta_analysis_available": delta_analysis is not None,
                    "volume_profile_available": volume_profile is not None,
                    "institutional_data_available": institutional_data is not None,
                },
                "market_depth": safe_dict(market_depth),
                "delta_analysis": safe_dict(delta_analysis),
                "volume_profile": safe_dict(volume_profile),
                "institutional_data": safe_dict(institutional_data),
            }

            # Generate summary
            try:
                analysis["summary"] = self.formatter.generate_analysis_summary(
                    market_depth, delta_analysis, volume_profile, institutional_data
                )
            except Exception as e:
                logger.warning(f"Error generating analysis summary for {symbol}: {e}")
                analysis["summary"] = {"error": f"Summary generation failed: {str(e)}"}

            logger.info(f"✅ Comprehensive analysis completed for {symbol}")
            return analysis

        except Exception as e:
            logger.error(f"Error getting comprehensive analysis for {symbol}: {e}", exc_info=True)
            return {
                "symbol": symbol.upper() if symbol else "unknown",
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }
