"""
OpenBB Platform Integration for Advanced Market Data
Provides comprehensive market data including order flow, delta analysis, and institutional data
Similar to Tiger Trade's advanced features
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
import asyncio
import time

# OpenBB imports
try:
    from openbb import obb
    OPENBB_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ OpenBB Platform loaded successfully")
except ImportError as e:
    OPENBB_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.error(f"❌ OpenBB Platform not available: {e}")

# Fallback imports
import yfinance as yf
import ccxt

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

class OpenBBMarketDataProvider:
    """
    Advanced market data provider using OpenBB Platform
    Provides Tiger Trade-like functionality with comprehensive market analysis
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.cache = {}
        self.cache_duration = 60  # 1 minute cache for real-time data
        
        # Initialize OpenBB
        if OPENBB_AVAILABLE:
            try:
                # Configure OpenBB with API keys if provided
                self._configure_openbb()
                self.openbb_available = True
                logger.info("🚀 OpenBB Platform initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenBB: {e}")
                self.openbb_available = False
        else:
            self.openbb_available = False
        
        # ALWAYS initialize CCXT for crypto data
        self._init_fallback_sources()
        
        logger.info("📊 Market Data Provider initialized")
    
    def _configure_openbb(self):
        """Configure OpenBB with API keys"""
        try:
            # Set API keys from config if available
            api_keys = self.config.get('api_keys', {})
            
            if 'fmp_api_key' in api_keys:
                obb.account.credentials.fmp_api_key = api_keys['fmp_api_key']
            
            if 'polygon_api_key' in api_keys:
                obb.account.credentials.polygon_api_key = api_keys['polygon_api_key']
            
            if 'alpha_vantage_api_key' in api_keys:
                obb.account.credentials.alpha_vantage_api_key = api_keys['alpha_vantage_api_key']
            
            logger.info("🔑 OpenBB API keys configured")
            
        except Exception as e:
            logger.warning(f"Could not configure OpenBB API keys: {e}")
    
    def _init_fallback_sources(self):
        """Initialize fallback data sources when OpenBB is not available"""
        try:
            # Initialize CCXT for crypto data (no API keys needed for public data)
            self.exchange = ccxt.binance({
                'enableRateLimit': True,
                'sandbox': False,  # Use live data for public endpoints
                'timeout': 10000,  # 10 second timeout
            })
            # Test the connection
            self.exchange.load_markets()
            logger.info("📈 Fallback data sources initialized (CCXT + yfinance)")
        except Exception as e:
            logger.error(f"Failed to initialize fallback sources: {e}")
            self.exchange = None
    
    async def get_market_depth(self, symbol: str, exchange: str = 'binance') -> Optional[MarketDepthData]:
        """
        Get real-time order book depth data
        Similar to Tiger Trade's Level 2 data
        """
        cache_key = f"depth_{symbol}_{exchange}"
        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            # Determine if this is a crypto symbol
            is_crypto = '/' in symbol and any(pair in symbol.upper() for pair in ['USDT', 'USDC', 'BTC', 'ETH'])
            
            if is_crypto and self.exchange:
                # Use CCXT for crypto market depth
                depth_data = await self._get_ccxt_depth(symbol, exchange)
            elif self.openbb_available:
                # Use OpenBB for stock market depth (quote data)
                depth_data = await self._get_openbb_depth(symbol)
            else:
                logger.warning(f"No suitable data source for market depth: {symbol}")
                return None
            
            if depth_data:
                self._cache_data(cache_key, depth_data)
                return depth_data
                
        except Exception as e:
            logger.error(f"Error getting market depth for {symbol}: {e}")
        
        return None
    
    async def _get_openbb_depth(self, symbol: str) -> Optional[MarketDepthData]:
        """Get market depth using OpenBB"""
        try:
            # Get quote data from OpenBB
            quote = obb.equity.price.quote(symbol=symbol)
            
            if quote and hasattr(quote, 'results') and quote.results:
                data = quote.results[0]
                
                # Simulate order book from quote data
                bid_price = float(data.bid) if hasattr(data, 'bid') and data.bid else 0
                ask_price = float(data.ask) if hasattr(data, 'ask') and data.ask else 0
                bid_size = float(data.bid_size) if hasattr(data, 'bid_size') and data.bid_size else 0
                ask_size = float(data.ask_size) if hasattr(data, 'ask_size') and data.ask_size else 0
                
                if bid_price > 0 and ask_price > 0:
                    # Create simplified order book
                    bids = [(bid_price, bid_size)]
                    asks = [(ask_price, ask_size)]
                    
                    spread = ask_price - bid_price
                    mid_price = (bid_price + ask_price) / 2
                    total_bid_volume = bid_size
                    total_ask_volume = ask_size
                    imbalance_ratio = bid_size / (bid_size + ask_size) if (bid_size + ask_size) > 0 else 0.5
                    
                    return MarketDepthData(
                        bids=bids,
                        asks=asks,
                        timestamp=datetime.now(),
                        spread=spread,
                        mid_price=mid_price,
                        total_bid_volume=total_bid_volume,
                        total_ask_volume=total_ask_volume,
                        imbalance_ratio=imbalance_ratio
                    )
            
        except Exception as e:
            logger.error(f"Error getting OpenBB depth data: {e}")
        
        return None
    
    async def _get_ccxt_depth(self, symbol: str, exchange_name: str) -> Optional[MarketDepthData]:
        """Get market depth using CCXT"""
        try:
            if not self.exchange:
                return None
            
            # Get order book
            orderbook = self.exchange.fetch_order_book(symbol, limit=20)
            
            bids = [(float(bid[0]), float(bid[1])) for bid in orderbook['bids'][:10]]
            asks = [(float(ask[0]), float(ask[1])) for ask in orderbook['asks'][:10]]
            
            if bids and asks:
                best_bid = bids[0][0]
                best_ask = asks[0][0]
                spread = best_ask - best_bid
                mid_price = (best_bid + best_ask) / 2
                
                total_bid_volume = sum(bid[1] for bid in bids)
                total_ask_volume = sum(ask[1] for ask in asks)
                imbalance_ratio = total_bid_volume / (total_bid_volume + total_ask_volume)
                
                return MarketDepthData(
                    bids=bids,
                    asks=asks,
                    timestamp=datetime.now(),
                    spread=spread,
                    mid_price=mid_price,
                    total_bid_volume=total_bid_volume,
                    total_ask_volume=total_ask_volume,
                    imbalance_ratio=imbalance_ratio
                )
            
        except Exception as e:
            logger.error(f"Error getting CCXT depth data: {e}")
        
        return None
    
    async def get_delta_analysis(self, symbol: str, timeframe: str = '1m', periods: int = 100) -> Optional[DeltaAnalysis]:
        """
        Advanced delta and order flow analysis
        Similar to Tiger Trade's delta analysis tools
        """
        cache_key = f"delta_{symbol}_{timeframe}_{periods}"
        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            # Get OHLCV data
            ohlcv_data = await self._get_ohlcv_data(symbol, timeframe, periods)
            if not ohlcv_data:
                return None
            
            df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Calculate delta metrics
            delta_analysis = self._calculate_delta_metrics(df)
            
            if delta_analysis:
                self._cache_data(cache_key, delta_analysis)
                return delta_analysis
                
        except Exception as e:
            logger.error(f"Error calculating delta analysis for {symbol}: {e}")
        
        return None
    
    def _calculate_delta_metrics(self, df: pd.DataFrame) -> Optional[DeltaAnalysis]:
        """Calculate comprehensive delta and order flow metrics"""
        try:
            # Price change and volume analysis
            df['price_change'] = df['close'].pct_change()
            df['price_direction'] = np.where(df['price_change'] > 0, 1, np.where(df['price_change'] < 0, -1, 0))
            
            # Volume-weighted price analysis
            df['vwap'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()
            df['price_vs_vwap'] = df['close'] / df['vwap'] - 1
            
            # Delta calculation (buying vs selling pressure)
            # Positive delta = buying pressure, Negative delta = selling pressure
            df['raw_delta'] = df['volume'] * df['price_direction']
            df['cumulative_delta'] = df['raw_delta'].cumsum()
            
            # Delta momentum (rate of change)
            df['delta_momentum'] = df['cumulative_delta'].diff(5)  # 5-period momentum
            
            # Buying and selling pressure
            df['buying_volume'] = np.where(df['price_direction'] > 0, df['volume'], 0)
            df['selling_volume'] = np.where(df['price_direction'] < 0, df['volume'], 0)
            
            buying_pressure = df['buying_volume'].rolling(20).sum().iloc[-1]
            selling_pressure = df['selling_volume'].rolling(20).sum().iloc[-1]
            
            # Net delta and divergence
            net_delta = buying_pressure - selling_pressure
            
            # Delta divergence (price vs delta momentum)
            price_momentum = df['close'].pct_change(10).iloc[-1]  # 10-period price momentum
            delta_momentum_normalized = df['delta_momentum'].iloc[-1] / df['volume'].rolling(20).mean().iloc[-1]
            
            delta_divergence = 0.0
            if price_momentum > 0 and delta_momentum_normalized < 0:
                delta_divergence = -0.5  # Bearish divergence
            elif price_momentum < 0 and delta_momentum_normalized > 0:
                delta_divergence = 0.5   # Bullish divergence
            
            # Order flow strength
            total_volume = df['volume'].rolling(20).sum().iloc[-1]
            order_flow_strength = df['cumulative_delta'].iloc[-1] / total_volume if total_volume > 0 else 0
            
            # Institutional vs retail flow estimation
            # Large volume bars likely institutional, small bars likely retail
            volume_threshold = df['volume'].quantile(0.8)  # Top 20% volume bars
            institutional_volume = df[df['volume'] > volume_threshold]['volume'].sum()
            retail_volume = df[df['volume'] <= volume_threshold]['volume'].sum()
            
            institutional_flow = institutional_volume / (institutional_volume + retail_volume)
            retail_flow = 1 - institutional_flow
            
            return DeltaAnalysis(
                cumulative_delta=df['cumulative_delta'].iloc[-1],
                delta_momentum=df['delta_momentum'].iloc[-1],
                buying_pressure=buying_pressure,
                selling_pressure=selling_pressure,
                net_delta=net_delta,
                delta_divergence=delta_divergence,
                order_flow_strength=order_flow_strength,
                institutional_flow=institutional_flow,
                retail_flow=retail_flow,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error calculating delta metrics: {e}")
            return None
    
    async def get_volume_profile(self, symbol: str, timeframe: str = '1h', periods: int = 100) -> Optional[VolumeProfile]:
        """
        Volume profile analysis
        Shows volume distribution by price levels
        """
        cache_key = f"volume_profile_{symbol}_{timeframe}_{periods}"
        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            # Get OHLCV data
            ohlcv_data = await self._get_ohlcv_data(symbol, timeframe, periods)
            if not ohlcv_data:
                return None
            
            df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Calculate volume profile
            volume_profile = self._calculate_volume_profile(df)
            
            if volume_profile:
                self._cache_data(cache_key, volume_profile)
                return volume_profile
                
        except Exception as e:
            logger.error(f"Error calculating volume profile for {symbol}: {e}")
        
        return None
    
    def _calculate_volume_profile(self, df: pd.DataFrame) -> Optional[VolumeProfile]:
        """Calculate volume profile metrics"""
        try:
            # Create price bins
            price_min = df['low'].min()
            price_max = df['high'].max()
            num_bins = 50
            price_bins = np.linspace(price_min, price_max, num_bins)
            
            # Calculate volume by price
            volume_by_price = {}
            buying_volume_total = 0
            selling_volume_total = 0
            
            for _, row in df.iterrows():
                # Distribute volume across price range for this candle
                candle_range = row['high'] - row['low']
                if candle_range > 0:
                    # Simple distribution - could be more sophisticated
                    volume_per_price = row['volume'] / candle_range
                    
                    # Determine buying vs selling volume based on close vs open
                    if row['close'] > row['open']:
                        buying_volume_total += row['volume'] * 0.6  # Assume 60% buying
                        selling_volume_total += row['volume'] * 0.4
                    else:
                        buying_volume_total += row['volume'] * 0.4
                        selling_volume_total += row['volume'] * 0.6  # Assume 60% selling
                    
                    # Add to volume profile
                    for price in price_bins:
                        if row['low'] <= price <= row['high']:
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
            sorted_prices = sorted(volume_by_price.keys(), key=lambda k: volume_by_price[k], reverse=True)
            
            value_area_volume = 0
            value_area_prices = []
            
            for price in sorted_prices:
                value_area_volume += volume_by_price[price]
                value_area_prices.append(price)
                if value_area_volume >= target_volume:
                    break
            
            value_area_high = max(value_area_prices) if value_area_prices else poc_price
            value_area_low = min(value_area_prices) if value_area_prices else poc_price
            
            volume_imbalance = (buying_volume_total - selling_volume_total) / total_volume if total_volume > 0 else 0
            
            return VolumeProfile(
                poc_price=poc_price,
                value_area_high=value_area_high,
                value_area_low=value_area_low,
                volume_by_price=volume_by_price,
                total_volume=total_volume,
                buying_volume=buying_volume_total,
                selling_volume=selling_volume_total,
                volume_imbalance=volume_imbalance
            )
            
        except Exception as e:
            logger.error(f"Error calculating volume profile: {e}")
            return None
    
    async def get_institutional_data(self, symbol: str) -> Optional[InstitutionalData]:
        """
        Get institutional trading data
        Dark pools, block trades, unusual options activity
        """
        cache_key = f"institutional_{symbol}"
        if self._is_cached(cache_key, duration=3600):  # 1 hour cache
            return self.cache[cache_key]['data']
        
        try:
            institutional_data = None
            
            if self.openbb_available:
                institutional_data = await self._get_openbb_institutional_data(symbol)
            
            if not institutional_data:
                # Fallback to estimated institutional data
                institutional_data = await self._estimate_institutional_data(symbol)
            
            if institutional_data:
                self._cache_data(cache_key, institutional_data)
                return institutional_data
                
        except Exception as e:
            logger.error(f"Error getting institutional data for {symbol}: {e}")
        
        return None
    
    async def _get_openbb_institutional_data(self, symbol: str) -> Optional[InstitutionalData]:
        """Get institutional data using OpenBB"""
        try:
            # Get institutional ownership data
            ownership_data = None
            try:
                ownership_data = obb.equity.ownership.institutional(symbol=symbol)
            except:
                pass
            
            # Get short interest data
            short_data = None
            try:
                short_data = obb.equity.short_interest.short_interest(symbol=symbol)
            except:
                pass
            
            # Compile institutional data
            institutional_ownership = 0.0
            float_short = 0.0
            days_to_cover = 0.0
            
            if ownership_data and hasattr(ownership_data, 'results') and ownership_data.results:
                # Calculate total institutional ownership
                total_shares = sum(float(holding.shares) for holding in ownership_data.results if hasattr(holding, 'shares'))
                institutional_ownership = total_shares  # This would need market cap calculation
            
            if short_data and hasattr(short_data, 'results') and short_data.results:
                latest_short = short_data.results[0]
                if hasattr(latest_short, 'short_interest'):
                    float_short = float(latest_short.short_interest)
                if hasattr(latest_short, 'days_to_cover'):
                    days_to_cover = float(latest_short.days_to_cover)
            
            return InstitutionalData(
                dark_pool_volume=0.0,  # Not available in free APIs
                block_trades=[],       # Not available in free APIs
                unusual_options_activity=[],  # Not available in free APIs
                insider_trading=[],    # Could be added with SEC data
                institutional_ownership=institutional_ownership,
                float_short=float_short,
                days_to_cover=days_to_cover
            )
            
        except Exception as e:
            logger.error(f"Error getting OpenBB institutional data: {e}")
            return None
    
    async def _estimate_institutional_data(self, symbol: str) -> Optional[InstitutionalData]:
        """Estimate institutional data using available metrics"""
        try:
            # Get basic volume data to estimate institutional activity
            ohlcv_data = await self._get_ohlcv_data(symbol, '1h', 24)
            if not ohlcv_data:
                return None
            
            df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Estimate dark pool volume (typically 30-40% of total volume)
            total_volume = df['volume'].sum()
            estimated_dark_pool = total_volume * 0.35
            
            # Identify potential block trades (large volume spikes)
            volume_threshold = df['volume'].quantile(0.95)  # Top 5% volume
            block_trades = []
            
            for _, row in df[df['volume'] > volume_threshold].iterrows():
                block_trades.append({
                    'timestamp': row['timestamp'],
                    'volume': row['volume'],
                    'price': row['close'],
                    'estimated_size': row['volume'] * row['close']
                })
            
            return InstitutionalData(
                dark_pool_volume=estimated_dark_pool,
                block_trades=block_trades,
                unusual_options_activity=[],  # Not available
                insider_trading=[],           # Not available
                institutional_ownership=0.0,  # Not available
                float_short=0.0,             # Not available
                days_to_cover=0.0            # Not available
            )
            
        except Exception as e:
            logger.error(f"Error estimating institutional data: {e}")
            return None
    
    async def _get_ohlcv_data(self, symbol: str, timeframe: str, periods: int) -> Optional[List]:
        """Get OHLCV data from available sources"""
        try:
            # Determine if this is a crypto symbol
            is_crypto = '/' in symbol and any(pair in symbol.upper() for pair in ['USDT', 'USDC', 'BTC', 'ETH'])
            
            if is_crypto and self.exchange:
                # Use CCXT for crypto symbols
                logger.info(f"📈 Getting crypto data for {symbol} via CCXT")
                try:
                    # Map timeframe for CCXT
                    ccxt_timeframe = timeframe
                    if timeframe == '4h':
                        ccxt_timeframe = '4h'
                    elif timeframe == '1h':
                        ccxt_timeframe = '1h'
                    elif timeframe == '1d':
                        ccxt_timeframe = '1d'
                    
                    ohlcv = self.exchange.fetch_ohlcv(symbol, ccxt_timeframe, limit=periods)
                    if ohlcv and len(ohlcv) > 0:
                        logger.info(f"✅ Got {len(ohlcv)} candles for {symbol}")
                        return ohlcv
                    else:
                        logger.warning(f"Empty OHLCV data for {symbol}")
                except Exception as e:
                    logger.error(f"CCXT error for {symbol}: {e}")
                    # Try alternative crypto symbols
                    try:
                        if symbol == 'BTC/USDT':
                            alt_symbol = 'BTCUSDT'
                            logger.info(f"Trying alternative symbol: {alt_symbol}")
                            ohlcv = self.exchange.fetch_ohlcv(alt_symbol, ccxt_timeframe, limit=periods)
                            if ohlcv and len(ohlcv) > 0:
                                logger.info(f"✅ Got {len(ohlcv)} candles for {alt_symbol}")
                                return ohlcv
                    except Exception as e2:
                        logger.error(f"Alternative symbol failed: {e2}")
            
            # Try OpenBB for stock data
            if self.openbb_available and not is_crypto:
                try:
                    logger.info(f"📊 Getting stock data for {symbol} via OpenBB")
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=periods)
                    
                    data = obb.equity.price.historical(
                        symbol=symbol,
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d'),
                        interval=timeframe
                    )
                    
                    if data and hasattr(data, 'results') and data.results:
                        ohlcv = []
                        for candle in data.results:
                            ohlcv.append([
                                int(candle.date.timestamp() * 1000),  # timestamp in ms
                                float(candle.open),
                                float(candle.high),
                                float(candle.low),
                                float(candle.close),
                                float(candle.volume) if hasattr(candle, 'volume') else 0
                            ])
                        logger.info(f"✅ Got {len(ohlcv)} candles for {symbol} via OpenBB")
                        return ohlcv
                except Exception as e:
                    logger.error(f"OpenBB error for {symbol}: {e}")
            
            # Fallback to yfinance for stocks only (avoid crypto symbols)
            if not is_crypto:
                try:
                    logger.info(f"📈 Trying yfinance fallback for {symbol}")
                    ticker = yf.Ticker(symbol)
                    period_map = {'1m': '1d', '5m': '5d', '1h': '1mo', '1d': '1y'}
                    period = period_map.get(timeframe, '1mo')
                    
                    hist = ticker.history(period=period, interval=timeframe)
                    if not hist.empty:
                        ohlcv = []
                        for idx, row in hist.iterrows():
                            ohlcv.append([
                                int(idx.timestamp() * 1000),
                                float(row['Open']),
                                float(row['High']),
                                float(row['Low']),
                                float(row['Close']),
                                float(row['Volume'])
                            ])
                        logger.info(f"✅ Got {len(ohlcv)} candles for {symbol} via yfinance")
                        return ohlcv[-periods:]  # Return last N periods
                except Exception as e:
                    logger.error(f"yfinance error for {symbol}: {e}")
            
            logger.warning(f"❌ No data source worked for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting OHLCV data for {symbol}: {e}")
            return None
    
    def _is_cached(self, key: str, duration: Optional[int] = None) -> bool:
        """Check if data is cached and still valid"""
        if key not in self.cache:
            return False
        
        cache_duration = duration or self.cache_duration
        cache_time = self.cache[key]['timestamp']
        return (time.time() - cache_time) < cache_duration
    
    def _cache_data(self, key: str, data: Any):
        """Cache data with timestamp"""
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    async def get_comprehensive_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive market analysis combining all data sources
        Similar to Tiger Trade's comprehensive market view
        """
        try:
            logger.info(f"🔍 Getting comprehensive analysis for {symbol}")
            
            # Gather all data concurrently
            tasks = [
                self.get_market_depth(symbol),
                self.get_delta_analysis(symbol),
                self.get_volume_profile(symbol),
                self.get_institutional_data(symbol)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            market_depth, delta_analysis, volume_profile, institutional_data = results
            
            # Compile comprehensive analysis
            analysis = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'market_depth': market_depth.__dict__ if market_depth else None,
                'delta_analysis': delta_analysis.__dict__ if delta_analysis else None,
                'volume_profile': volume_profile.__dict__ if volume_profile else None,
                'institutional_data': institutional_data.__dict__ if institutional_data else None,
                'summary': self._generate_analysis_summary(market_depth, delta_analysis, volume_profile, institutional_data)
            }
            
            logger.info(f"✅ Comprehensive analysis completed for {symbol}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting comprehensive analysis for {symbol}: {e}")
            return {'error': str(e)}
    
    def _generate_analysis_summary(self, market_depth, delta_analysis, volume_profile, institutional_data) -> Dict[str, Any]:
        """Generate a summary of the analysis"""
        summary = {
            'overall_sentiment': 'neutral',
            'key_levels': {},
            'risk_factors': [],
            'opportunities': [],
            'confidence_score': 0.5
        }
        
        try:
            # Analyze market depth
            if market_depth:
                if market_depth.imbalance_ratio > 0.6:
                    summary['overall_sentiment'] = 'bullish'
                    summary['opportunities'].append('Strong bid support')
                elif market_depth.imbalance_ratio < 0.4:
                    summary['overall_sentiment'] = 'bearish'
                    summary['risk_factors'].append('Weak bid support')
                
                summary['key_levels']['current_spread'] = market_depth.spread
                summary['key_levels']['mid_price'] = market_depth.mid_price
            
            # Analyze delta
            if delta_analysis:
                if delta_analysis.net_delta > 0:
                    summary['opportunities'].append('Positive order flow')
                else:
                    summary['risk_factors'].append('Negative order flow')
                
                if delta_analysis.delta_divergence > 0.3:
                    summary['opportunities'].append('Bullish divergence detected')
                elif delta_analysis.delta_divergence < -0.3:
                    summary['risk_factors'].append('Bearish divergence detected')
            
            # Analyze volume profile
            if volume_profile:
                summary['key_levels']['poc_price'] = volume_profile.poc_price
                summary['key_levels']['value_area_high'] = volume_profile.value_area_high
                summary['key_levels']['value_area_low'] = volume_profile.value_area_low
                
                if volume_profile.volume_imbalance > 0.2:
                    summary['opportunities'].append('Strong buying volume')
                elif volume_profile.volume_imbalance < -0.2:
                    summary['risk_factors'].append('Strong selling volume')
            
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
                summary['confidence_score'] = positive_factors / factors
            
            # Determine overall sentiment
            if summary['confidence_score'] > 0.6:
                summary['overall_sentiment'] = 'bullish'
            elif summary['confidence_score'] < 0.4:
                summary['overall_sentiment'] = 'bearish'
            else:
                summary['overall_sentiment'] = 'neutral'
            
        except Exception as e:
            logger.error(f"Error generating analysis summary: {e}")
        
        return summary


# Async helper function for easy integration
async def get_market_analysis(symbol: str, config: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Convenience function to get comprehensive market analysis
    """
    provider = OpenBBMarketDataProvider(config)
    return await provider.get_comprehensive_analysis(symbol)


# Example usage and testing
if __name__ == "__main__":
    async def test_provider():
        """Test the market data provider"""
        provider = OpenBBMarketDataProvider()
        
        # Test with BTC/USDT
        print("Testing BTC/USDT analysis...")
        btc_analysis = await provider.get_comprehensive_analysis('BTC/USDT')
        print(f"BTC Analysis: {btc_analysis}")
        
        # Test with AAPL
        print("\nTesting AAPL analysis...")
        aapl_analysis = await provider.get_comprehensive_analysis('AAPL')
        print(f"AAPL Analysis: {aapl_analysis}")
    
    # Run test
    asyncio.run(test_provider())