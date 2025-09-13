#!/usr/bin/env python3
"""Live market data provider using direct exchange APIs"""

import requests
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Import persistent cache
try:
    from .persistent_cache import market_cache
    PERSISTENT_CACHE_AVAILABLE = True
    logger.info("✅ Persistent cache available")
except ImportError:
    PERSISTENT_CACHE_AVAILABLE = False
    logger.warning("⚠️ Persistent cache not available")

class LiveMarketProvider:
    """Live market data from working exchanges"""
    
    def __init__(self):
        # Use reliable exchanges that work from most locations
        self.exchanges = {
            'cryptocompare': {
                'name': 'CryptoCompare',
                'price_url': 'https://min-api.cryptocompare.com/data/pricemultifull',
                'symbols': {
                    'BTC/USDT': 'BTC',
                    'ETH/USDT': 'ETH', 
                    'SOL/USDT': 'SOL',
                    'ADA/USDT': 'ADA',
                    'DOT/USDT': 'DOT',
                    'LINK/USDT': 'LINK',
                    'AVAX/USDT': 'AVAX',
                    'MATIC/USDT': 'MATIC',
                    'UNI/USDT': 'UNI',
                    'ATOM/USDT': 'ATOM'
                }
            },
            'coinpaprika': {
                'name': 'CoinPaprika',
                'base_url': 'https://api.coinpaprika.com/v1/tickers',
                'symbols': {
                    'BTC/USDT': 'btc-bitcoin',
                    'ETH/USDT': 'eth-ethereum',
                    'SOL/USDT': 'sol-solana', 
                    'ADA/USDT': 'ada-cardano',
                    'DOT/USDT': 'dot-polkadot',
                    'LINK/USDT': 'link-chainlink',
                    'AVAX/USDT': 'avax-avalanche',
                    'MATIC/USDT': 'matic-polygon',
                    'UNI/USDT': 'uni-uniswap',
                    'ATOM/USDT': 'atom-cosmos'
                }
            },
            'binance': {
                'name': 'Binance',
                'price_url': 'https://api.binance.com/api/v3/ticker/24hr',
                'single_price_url': 'https://api.binance.com/api/v3/ticker/price',
                'kline_url': 'https://api.binance.com/api/v3/klines',
                'symbols': {
                    'BTC/USDT': 'BTCUSDT',
                    'ETH/USDT': 'ETHUSDT', 
                    'SOL/USDT': 'SOLUSDT',
                    'ADA/USDT': 'ADAUSDT',
                    'DOT/USDT': 'DOTUSDT',
                    'LINK/USDT': 'LINKUSDT',
                    'AVAX/USDT': 'AVAXUSDT',
                    'MATIC/USDT': 'MATICUSDT',
                    'UNI/USDT': 'UNIUSDT',
                    'ATOM/USDT': 'ATOMUSDT'
                }
            },
            'coingecko': {
                'name': 'CoinGecko', 
                'price_url': 'https://api.coingecko.com/api/v3/simple/price',
                'symbols': {
                    'BTC/USDT': 'bitcoin',
                    'ETH/USDT': 'ethereum',
                    'SOL/USDT': 'solana', 
                    'ADA/USDT': 'cardano',
                    'DOT/USDT': 'polkadot',
                    'LINK/USDT': 'chainlink',
                    'AVAX/USDT': 'avalanche-2',
                    'MATIC/USDT': 'matic-network',
                    'UNI/USDT': 'uniswap',
                    'ATOM/USDT': 'cosmos'
                }
            }
        }
        
        self.cache = {}
        self.cache_timeout = 10  # 10 seconds cache
        
    def get_live_prices(self) -> Dict:
        """Get live prices for all symbols with persistent caching"""
        now = time.time()
        
        # Check memory cache first
        if 'prices' in self.cache and now - self.cache.get('prices_time', 0) < self.cache_timeout:
            return self.cache['prices']
        
        # Check persistent cache (5 minutes max age)
        if PERSISTENT_CACHE_AVAILABLE:
            cached_prices = market_cache.get_cached_prices(max_age_seconds=300)
            if cached_prices:
                self.cache['prices'] = cached_prices
                self.cache['prices_time'] = now
                logger.info(f"📦 Using {len(cached_prices)} cached prices")
                return cached_prices
        
        # Try live APIs in order of reliability
        for api_name, api_method in [
            ('CryptoCompare', self._get_cryptocompare_prices),
            ('CoinPaprika', self._get_coinpaprika_prices),
            ('Binance', self._get_binance_prices),
            ('CoinGecko', self._get_coingecko_prices)
        ]:
            try:
                prices = api_method()
                if prices:
                    # Store in both caches
                    self.cache['prices'] = prices
                    self.cache['prices_time'] = now
                    
                    # Store in persistent cache
                    if PERSISTENT_CACHE_AVAILABLE:
                        market_cache.cache_prices(prices)
                    
                    logger.info(f"✅ Got {len(prices)} prices from {api_name}")
                    return prices
            except Exception as e:
                logger.warning(f"{api_name} failed: {e}")
        
        # Last resort: try older cached data (up to 1 hour)
        if PERSISTENT_CACHE_AVAILABLE:
            old_cached_prices = market_cache.get_cached_prices(max_age_seconds=3600)
            if old_cached_prices:
                logger.warning(f"⚠️ Using stale cached data ({len(old_cached_prices)} prices)")
                return old_cached_prices
        
        logger.error("❌ All price sources failed and no cached data available")
        return {}
    
    def _get_binance_prices(self) -> Dict:
        """Get prices from Binance"""
        try:
            response = requests.get(
                self.exchanges['binance']['price_url'],
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                prices = {}
                
                for pair, symbol in self.exchanges['binance']['symbols'].items():
                    for item in data:
                        if item['symbol'] == symbol:
                            prices[pair] = {
                                'price': float(item['lastPrice']),
                                'change_24h': float(item['priceChange']),
                                'change_24h_percent': float(item['priceChangePercent']),
                                'volume_24h': float(item['volume']),
                                'high_24h': float(item['highPrice']),
                                'low_24h': float(item['lowPrice']),
                                'source': 'Binance',
                                'timestamp': datetime.now().isoformat()
                            }
                            break
                
                return prices
                
        except Exception as e:
            logger.error(f"Binance API error: {e}")
            
        return {}
    
    def _get_coingecko_prices(self) -> Dict:
        """Get prices from CoinGecko"""
        try:
            ids = ','.join(self.exchanges['coingecko']['symbols'].values())
            params = {
                'ids': ids,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true'
            }
            
            response = requests.get(
                self.exchanges['coingecko']['price_url'],
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                prices = {}
                
                for pair, coin_id in self.exchanges['coingecko']['symbols'].items():
                    if coin_id in data:
                        coin_data = data[coin_id]
                        prices[pair] = {
                            'price': coin_data.get('usd', 0),
                            'change_24h_percent': coin_data.get('usd_24h_change', 0),
                            'volume_24h': coin_data.get('usd_24h_vol', 0),
                            'source': 'CoinGecko',
                            'timestamp': datetime.now().isoformat()
                        }
                
                return prices
                
        except Exception as e:
            logger.error(f"CoinGecko API error: {e}")
            
        return {}
    
    def _get_cryptocompare_prices(self) -> Dict:
        """Get prices from CryptoCompare"""
        try:
            # Get all symbols we need
            symbols_str = ','.join(self.exchanges['cryptocompare']['symbols'].values())
            
            response = requests.get(
                self.exchanges['cryptocompare']['price_url'],
                params={
                    'fsyms': symbols_str,
                    'tsyms': 'USD'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                prices = {}
                
                # Parse the response format from CryptoCompare
                raw_data = data.get('RAW', {})
                
                for pair, cc_symbol in self.exchanges['cryptocompare']['symbols'].items():
                    if cc_symbol in raw_data and 'USD' in raw_data[cc_symbol]:
                        coin_data = raw_data[cc_symbol]['USD']
                        prices[pair] = {
                            'price': coin_data.get('PRICE', 0),
                            'change_24h': coin_data.get('CHANGE24HOUR', 0),
                            'change_24h_percent': coin_data.get('CHANGEPCT24HOUR', 0),
                            'volume_24h': coin_data.get('VOLUME24HOUR', 0),
                            'high_24h': coin_data.get('HIGH24HOUR', 0),
                            'low_24h': coin_data.get('LOW24HOUR', 0),
                            'source': 'CryptoCompare',
                            'timestamp': datetime.now().isoformat()
                        }
                
                return prices
                
        except Exception as e:
            logger.error(f"CryptoCompare API error: {e}")
            
        return {}
    
    def _get_coinpaprika_prices(self) -> Dict:
        """Get prices from CoinPaprika"""
        try:
            prices = {}
            
            # CoinPaprika requires individual calls for each symbol
            for pair, coin_id in self.exchanges['coinpaprika']['symbols'].items():
                try:
                    response = requests.get(
                        f"{self.exchanges['coinpaprika']['base_url']}/{coin_id}",
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        quotes = data.get('quotes', {})
                        usd_data = quotes.get('USD', {})
                        
                        if usd_data:
                            prices[pair] = {
                                'price': usd_data.get('price', 0),
                                'change_24h_percent': usd_data.get('percent_change_24h', 0),
                                'volume_24h': usd_data.get('volume_24h', 0),
                                'source': 'CoinPaprika',
                                'timestamp': datetime.now().isoformat()
                            }
                except Exception as e:
                    logger.warning(f"CoinPaprika error for {coin_id}: {e}")
                    continue
            
            return prices
                
        except Exception as e:
            logger.error(f"CoinPaprika API error: {e}")
            
        return {}
    
    def get_symbol_price(self, symbol: str) -> Optional[Dict]:
        """Get price for a specific symbol"""
        prices = self.get_live_prices()
        return prices.get(symbol)
    
    def get_market_summary(self) -> Dict:
        """Get market summary with totals"""
        prices = self.get_live_prices()
        
        if not prices:
            return {
                'total_symbols': 0,
                'gainers': 0,
                'losers': 0,
                'total_volume': 0,
                'data_source': 'No Data Available',
                'last_update': datetime.now().isoformat()
            }
        
        gainers = sum(1 for p in prices.values() if p.get('change_24h_percent', 0) > 0)
        losers = sum(1 for p in prices.values() if p.get('change_24h_percent', 0) < 0)
        total_volume = sum(p.get('volume_24h', 0) for p in prices.values())
        
        # Get the source from first price entry
        source = list(prices.values())[0].get('source', 'Unknown') if prices else 'Unknown'
        
        return {
            'total_symbols': len(prices),
            'gainers': gainers,
            'losers': losers,
            'total_volume': total_volume,
            'data_source': source,
            'last_update': datetime.now().isoformat(),
            'status': 'connected'
        }
    
    def get_kline_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[Dict]:
        """Get candlestick data for charts with persistent caching"""
        # Check persistent cache first
        if PERSISTENT_CACHE_AVAILABLE:
            cached_data = market_cache.get_cached_historical_data(symbol, timeframe, max_age_seconds=1800)  # 30 min
            if cached_data:
                logger.info(f"📦 Using cached chart data for {symbol} {timeframe}")
                return cached_data
        
        try:
            if symbol not in self.exchanges['binance']['symbols']:
                return []
                
            binance_symbol = self.exchanges['binance']['symbols'][symbol]
            
            # Convert timeframe
            interval_map = {
                '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1h', '4h': '4h', '1d': '1d', '1w': '1w'
            }
            interval = interval_map.get(timeframe, '1h')
            
            response = requests.get(
                self.exchanges['binance']['kline_url'],
                params={
                    'symbol': binance_symbol,
                    'interval': interval,
                    'limit': limit
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                klines = []
                
                for item in data:
                    klines.append({
                        'timestamp': int(item[0]),
                        'open': float(item[1]),
                        'high': float(item[2]), 
                        'low': float(item[3]),
                        'close': float(item[4]),
                        'volume': float(item[5])
                    })
                
                # Cache the data
                if PERSISTENT_CACHE_AVAILABLE and klines:
                    market_cache.cache_historical_data(symbol, timeframe, klines)
                
                logger.info(f"✅ Got {len(klines)} klines for {symbol} {timeframe}")
                return klines
                
        except Exception as e:
            logger.error(f"Kline data error: {e}")
            
        return []

# Global instance
live_market = LiveMarketProvider()

def get_live_market_data():
    """Get live market data - main interface"""
    return live_market.get_live_prices()

def get_market_summary():
    """Get market summary - main interface"""  
    return live_market.get_market_summary()

def get_symbol_price(symbol):
    """Get single symbol price - main interface"""
    return live_market.get_symbol_price(symbol)

def get_chart_data(symbol, timeframe='1h', limit=100):
    """Get chart data - main interface"""
    return live_market.get_kline_data(symbol, timeframe, limit)