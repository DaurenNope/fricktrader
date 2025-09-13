"""
Unified Data Pipeline
Integrates OpenBB, Phase 1 infrastructure, and strategy framework
Clean, high-performance data access for all strategies
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd

from src.data.historical_data_manager import HistoricalDataManager
from src.data.real_time_feeds import RealTimeFeedsManager
from src.database.data_warehouse import DataWarehouse
from src.market_data.openbb_provider import OpenBBMarketDataProvider
from src.strategy_framework import DataProvider, MarketData, TimeFrame

logger = logging.getLogger(__name__)


class UnifiedDataPipeline(DataProvider):
    """
    Unified data pipeline combining all data sources:
    - Phase 1 Infrastructure (Real-time feeds, Historical data, Data warehouse)
    - OpenBB Platform (Advanced analytics, Fundamentals, Sentiment)
    - Strategy Framework (Clean, standardized interface)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize Phase 1 infrastructure
        self.historical_manager = HistoricalDataManager()
        self.realtime_manager = RealTimeFeedsManager(self.config)
        self.data_warehouse = DataWarehouse()
        
        # Initialize OpenBB provider
        self.openbb_provider = OpenBBMarketDataProvider(config)
        
        # Performance caching
        self.cache = {}
        self.cache_duration = {
            "ohlcv": 30,      # 30 seconds for OHLCV
            "depth": 5,       # 5 seconds for market depth
            "sentiment": 300,  # 5 minutes for sentiment
            "fundamentals": 3600,  # 1 hour for fundamentals
        }
        
        self.logger.info("🚀 Unified Data Pipeline initialized")
    
    async def get_market_data(
        self, 
        symbol: str, 
        timeframe: TimeFrame, 
        periods: int = 100
    ) -> MarketData:
        """
        Get comprehensive market data from all sources
        Combines Phase 1 infrastructure + OpenBB analytics
        """
        try:
            self.logger.info(f"📊 Getting unified market data for {symbol}")
            
            # Get OHLCV data (fastest source first)
            ohlcv_data = await self._get_ohlcv_optimized(symbol, timeframe, periods)
            
            # Get advanced analytics in parallel
            tasks = [
                self._get_market_depth_cached(symbol),
                self._get_delta_analysis_cached(symbol, timeframe),
                self._get_volume_profile_cached(symbol, timeframe),
                self._get_sentiment_data_cached(symbol),
                self._get_fundamentals_cached(symbol),
                self._get_macro_data_cached()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            market_depth, delta_analysis, volume_profile, sentiment, fundamentals, macro_data = results
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.warning(f"Task {i} failed: {result}")
            
            # Create comprehensive market data object
            market_data = MarketData(
                symbol=symbol,
                ohlcv=ohlcv_data,
                orderbook=None,  # Real-time only
                market_depth=market_depth.__dict__ if hasattr(market_depth, '__dict__') else market_depth,
                delta_analysis=delta_analysis.__dict__ if hasattr(delta_analysis, '__dict__') else delta_analysis,
                volume_profile=volume_profile.__dict__ if hasattr(volume_profile, '__dict__') else volume_profile,
                sentiment=sentiment,
                fundamentals=fundamentals,
                macro_data=macro_data
            )
            
            self.logger.info(f"✅ Unified market data ready for {symbol}")
            return market_data
            
        except Exception as e:
            self.logger.error(f"Error getting unified market data: {e}")
            # Return minimal data to prevent strategy failures
            return MarketData(
                symbol=symbol,
                ohlcv=pd.DataFrame(),
                sentiment={"error": str(e)}
            )
    
    async def get_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """Get real-time market data"""
        try:
            # Try real-time feeds first (Phase 1)
            if self.realtime_manager.is_running:
                feed_data = self.realtime_manager.get_latest_data(symbol)
                if feed_data:
                    return feed_data
            
            # Fallback to OpenBB real-time
            return await self.openbb_provider.get_market_depth(symbol)
            
        except Exception as e:
            self.logger.error(f"Error getting real-time data: {e}")
            return {"error": str(e)}
    
    async def _get_ohlcv_optimized(
        self, 
        symbol: str, 
        timeframe: TimeFrame, 
        periods: int
    ) -> pd.DataFrame:
        """Get OHLCV data with optimized source selection"""
        
        cache_key = f"ohlcv_{symbol}_{timeframe.value}_{periods}"
        
        # Check cache first
        if self._is_cached(cache_key, "ohlcv"):
            self.logger.debug(f"📋 Using cached OHLCV for {symbol}")
            return self.cache[cache_key]["data"]
        
        try:
            # 1. Try Historical Data Manager first (Phase 1 - fastest)
            try:
                df = await self._get_from_historical_manager(symbol, timeframe, periods)
                if not df.empty and len(df) >= periods * 0.8:  # At least 80% of requested data
                    self._cache_data(cache_key, df)
                    self.logger.info(f"📈 OHLCV from Historical Manager: {len(df)} candles")
                    return df
            except Exception as e:
                self.logger.debug(f"Historical manager failed: {e}")
            
            # 2. Try Data Warehouse (Phase 1 - local database)
            try:
                df = await self._get_from_data_warehouse(symbol, timeframe, periods)
                if not df.empty:
                    self._cache_data(cache_key, df)
                    self.logger.info(f"🗄️ OHLCV from Data Warehouse: {len(df)} candles")
                    return df
            except Exception as e:
                self.logger.debug(f"Data warehouse failed: {e}")
            
            # 3. Fallback to OpenBB (external API)
            try:
                ohlcv_list = await self.openbb_provider._get_ohlcv_data(
                    symbol, timeframe.value, periods
                )
                if ohlcv_list:
                    df = pd.DataFrame(
                        ohlcv_list,
                        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    )
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    
                    # Store in data warehouse for next time
                    await self._store_in_warehouse(symbol, df)
                    
                    self._cache_data(cache_key, df)
                    self.logger.info(f"🌐 OHLCV from OpenBB: {len(df)} candles")
                    return df
            except Exception as e:
                self.logger.debug(f"OpenBB OHLCV failed: {e}")
            
            # If all fail, return empty DataFrame
            self.logger.warning(f"❌ No OHLCV data available for {symbol}")
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
            
        except Exception as e:
            self.logger.error(f"Error getting optimized OHLCV: {e}")
            return pd.DataFrame()
    
    async def _get_from_historical_manager(
        self, 
        symbol: str, 
        timeframe: TimeFrame, 
        periods: int
    ) -> pd.DataFrame:
        """Get data from Historical Data Manager (Phase 1)"""
        
        # Calculate date range
        end_date = datetime.now()
        
        # Map timeframe to timedelta
        timeframe_map = {
            TimeFrame.M1: timedelta(minutes=periods),
            TimeFrame.M5: timedelta(minutes=periods * 5),
            TimeFrame.M15: timedelta(minutes=periods * 15),
            TimeFrame.M30: timedelta(minutes=periods * 30),
            TimeFrame.H1: timedelta(hours=periods),
            TimeFrame.H4: timedelta(hours=periods * 4),
            TimeFrame.D1: timedelta(days=periods)
        }
        
        start_date = end_date - timeframe_map.get(timeframe, timedelta(hours=periods))
        
        # Fetch from historical manager
        df = self.historical_manager.get_historical_data(
            symbol=symbol,
            timeframe=timeframe.value,
            start_date=start_date,
            end_date=end_date
        )
        
        return df if df is not None else pd.DataFrame()
    
    async def _get_from_data_warehouse(
        self, 
        symbol: str, 
        timeframe: TimeFrame, 
        periods: int
    ) -> pd.DataFrame:
        """Get data from Data Warehouse (Phase 1)"""
        
        try:
            # Use data warehouse query
            df = self.data_warehouse.get_ohlcv_data(
                symbol=symbol,
                timeframe=timeframe.value,
                limit=periods
            )
            
            return df if df is not None else pd.DataFrame()
            
        except Exception as e:
            self.logger.debug(f"Data warehouse query failed: {e}")
            return pd.DataFrame()
    
    async def _store_in_warehouse(self, symbol: str, df: pd.DataFrame):
        """Store OHLCV data in warehouse for future use"""
        try:
            # Convert DataFrame to format expected by warehouse
            ohlcv_data = []
            for timestamp, row in df.iterrows():
                ohlcv_data.append([
                    int(timestamp.timestamp() * 1000),  # timestamp in ms
                    float(row['open']),
                    float(row['high']),
                    float(row['low']),
                    float(row['close']),
                    float(row['volume'])
                ])
            
            self.data_warehouse.store_ohlcv_data(symbol, ohlcv_data)
            self.logger.debug(f"📝 Stored {len(ohlcv_data)} candles in warehouse")
            
        except Exception as e:
            self.logger.debug(f"Failed to store in warehouse: {e}")
    
    async def _get_market_depth_cached(self, symbol: str):
        """Get market depth with caching"""
        cache_key = f"depth_{symbol}"
        
        if self._is_cached(cache_key, "depth"):
            return self.cache[cache_key]["data"]
        
        try:
            depth = await self.openbb_provider.get_market_depth(symbol)
            if depth:
                self._cache_data(cache_key, depth)
            return depth
        except Exception as e:
            self.logger.debug(f"Market depth failed: {e}")
            return None
    
    async def _get_delta_analysis_cached(self, symbol: str, timeframe: TimeFrame):
        """Get delta analysis with caching"""
        cache_key = f"delta_{symbol}_{timeframe.value}"
        
        if self._is_cached(cache_key, "depth"):
            return self.cache[cache_key]["data"]
        
        try:
            delta = await self.openbb_provider.get_delta_analysis(
                symbol, timeframe.value
            )
            if delta:
                self._cache_data(cache_key, delta)
            return delta
        except Exception as e:
            self.logger.debug(f"Delta analysis failed: {e}")
            return None
    
    async def _get_volume_profile_cached(self, symbol: str, timeframe: TimeFrame):
        """Get volume profile with caching"""
        cache_key = f"volume_profile_{symbol}_{timeframe.value}"
        
        if self._is_cached(cache_key, "depth"):
            return self.cache[cache_key]["data"]
        
        try:
            volume_profile = await self.openbb_provider.get_volume_profile(
                symbol, timeframe.value
            )
            if volume_profile:
                self._cache_data(cache_key, volume_profile)
            return volume_profile
        except Exception as e:
            self.logger.debug(f"Volume profile failed: {e}")
            return None
    
    async def _get_sentiment_data_cached(self, symbol: str):
        """Get sentiment data with caching"""
        cache_key = f"sentiment_{symbol}"
        
        if self._is_cached(cache_key, "sentiment"):
            return self.cache[cache_key]["data"]
        
        try:
            # Get crypto-specific sentiment if available
            if "/" in symbol:  # Crypto pair
                from src.market_data.enhanced_openbb_capabilities import EnhancedOpenBBCapabilities
                enhanced = EnhancedOpenBBCapabilities()
                sentiment = await enhanced.get_crypto_analysis(symbol)
            else:
                # Stock sentiment (placeholder)
                sentiment = {"social_score": 0.5, "news_sentiment": 0.5}
            
            if sentiment:
                self._cache_data(cache_key, sentiment)
            return sentiment
            
        except Exception as e:
            self.logger.debug(f"Sentiment analysis failed: {e}")
            return {"social_score": 0.5}  # Neutral default
    
    async def _get_fundamentals_cached(self, symbol: str):
        """Get fundamentals with caching"""
        cache_key = f"fundamentals_{symbol}"
        
        if self._is_cached(cache_key, "fundamentals"):
            return self.cache[cache_key]["data"]
        
        try:
            # Only get fundamentals for stocks (not crypto pairs)
            if "/" not in symbol:
                from src.market_data.enhanced_openbb_capabilities import EnhancedOpenBBCapabilities
                enhanced = EnhancedOpenBBCapabilities()
                fundamentals = await enhanced.get_fundamental_analysis(symbol)
                
                if fundamentals and "error" not in fundamentals:
                    self._cache_data(cache_key, fundamentals)
                    return fundamentals
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Fundamentals failed: {e}")
            return None
    
    async def _get_macro_data_cached(self):
        """Get macro economic data with caching"""
        cache_key = "macro_data"
        
        if self._is_cached(cache_key, "fundamentals"):  # Same cache duration
            return self.cache[cache_key]["data"]
        
        try:
            from src.market_data.enhanced_openbb_capabilities import EnhancedOpenBBCapabilities
            enhanced = EnhancedOpenBBCapabilities()
            macro_data = await enhanced.get_economic_indicators()
            
            if macro_data and "error" not in macro_data:
                self._cache_data(cache_key, macro_data)
                return macro_data
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Macro data failed: {e}")
            return None
    
    def _is_cached(self, key: str, data_type: str) -> bool:
        """Check if data is cached and still valid"""
        if key not in self.cache:
            return False
        
        cache_age = datetime.now().timestamp() - self.cache[key]["timestamp"]
        max_age = self.cache_duration.get(data_type, 300)  # 5 min default
        
        return cache_age < max_age
    
    def _cache_data(self, key: str, data: Any):
        """Cache data with timestamp"""
        self.cache[key] = {
            "data": data,
            "timestamp": datetime.now().timestamp()
        }
    
    def get_data_status(self) -> Dict[str, Any]:
        """Get status of all data sources"""
        return {
            "historical_manager": {
                "available": self.historical_manager is not None,
                "status": "active"
            },
            "realtime_manager": {
                "available": self.realtime_manager is not None,
                "running": self.realtime_manager.is_running if self.realtime_manager else False,
                "feeds": len(self.realtime_manager.feeds) if self.realtime_manager else 0
            },
            "data_warehouse": {
                "available": self.data_warehouse is not None,
                "status": "active"
            },
            "openbb_provider": {
                "available": self.openbb_provider.openbb_available,
                "fallback_available": self.openbb_provider.exchange is not None
            },
            "cache": {
                "entries": len(self.cache),
                "types": list(set(
                    key.split("_")[0] for key in self.cache.keys()
                ))
            }
        }
    
    async def start_real_time_feeds(self, symbols: List[str] = None):
        """Start real-time data feeds"""
        if symbols:
            self.realtime_manager.symbols = symbols
        
        await self.realtime_manager.start_feeds()
        self.logger.info("📡 Real-time feeds started")
    
    async def stop_real_time_feeds(self):
        """Stop real-time data feeds"""
        await self.realtime_manager.stop_feeds()
        self.logger.info("⏹️ Real-time feeds stopped")
    
    def clear_cache(self, data_type: str = None):
        """Clear cache (optionally by data type)"""
        if data_type:
            keys_to_remove = [k for k in self.cache.keys() if k.startswith(data_type)]
            for key in keys_to_remove:
                del self.cache[key]
            self.logger.info(f"🗑️ Cleared {data_type} cache ({len(keys_to_remove)} entries)")
        else:
            self.cache.clear()
            self.logger.info("🗑️ Cleared all cache")


# Factory function for easy integration
def create_unified_pipeline(config: Dict[str, Any] = None) -> UnifiedDataPipeline:
    """Create and initialize unified data pipeline"""
    return UnifiedDataPipeline(config)


# Example usage for testing
async def test_pipeline():
    """Test the unified data pipeline"""
    
    config = {
        "symbols": ["BTC/USDT", "ETH/USDT"],
        "api_keys": {
            # Add your API keys here
        }
    }
    
    pipeline = create_unified_pipeline(config)
    
    # Test getting market data
    print("Testing BTC/USDT market data...")
    btc_data = await pipeline.get_market_data("BTC/USDT", TimeFrame.H1, 50)
    print(f"OHLCV data: {len(btc_data.ohlcv)} candles")
    print(f"Market depth: {btc_data.market_depth is not None}")
    print(f"Delta analysis: {btc_data.delta_analysis is not None}")
    print(f"Sentiment: {btc_data.sentiment is not None}")
    
    # Test data status
    status = pipeline.get_data_status()
    print(f"Data sources status: {status}")


if __name__ == "__main__":
    asyncio.run(test_pipeline())