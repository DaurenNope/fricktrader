#!/usr/bin/env python3
"""
API Configuration and Management for Market Data
"""
import os
from typing import List
import logging

logger = logging.getLogger(__name__)

class APIConfig:
    """Centralized API configuration and management"""
    
    def __init__(self):
        self.api_configs = {
            'cryptocompare': {
                'name': 'CryptoCompare',
                'reliability_score': 95,  # Out of 100
                'rate_limit': 100,        # Requests per second
                'requires_key': False,
                'endpoints': {
                    'price': 'https://min-api.cryptocompare.com/data/pricemultifull',
                    'historical': 'https://min-api.cryptocompare.com/data/v2/histoday'
                }
            },
            'coinpaprika': {
                'name': 'CoinPaprika', 
                'reliability_score': 85,
                'rate_limit': 25,
                'requires_key': False,
                'endpoints': {
                    'price': 'https://api.coinpaprika.com/v1/tickers',
                    'historical': 'https://api.coinpaprika.com/v1/coins/{coin_id}/ohlcv/historical'
                }
            },
            'binance': {
                'name': 'Binance',
                'reliability_score': 90,
                'rate_limit': 1200,
                'requires_key': False,
                'endpoints': {
                    'price': 'https://api.binance.com/api/v3/ticker/24hr',
                    'klines': 'https://api.binance.com/api/v3/klines'
                }
            },
            'coingecko': {
                'name': 'CoinGecko',
                'reliability_score': 80,
                'rate_limit': 30,  # Free tier
                'requires_key': False,
                'endpoints': {
                    'price': 'https://api.coingecko.com/api/v3/simple/price',
                    'historical': 'https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart'
                }
            }
        }
        
        # Load API keys from environment
        self.api_keys = {
            'cryptocompare': os.getenv('CRYPTOCOMPARE_API_KEY'),
            'coingecko': os.getenv('COINGECKO_API_KEY'),
            'binance': os.getenv('BINANCE_API_KEY')
        }
        
        # Cache configuration
        self.cache_config = {
            'memory_timeout': 10,      # 10 seconds
            'disk_timeout': 300,       # 5 minutes for fresh data
            'stale_timeout': 3600,     # 1 hour for stale data
            'max_cache_size': 1000     # Max cached entries
        }
    
    def get_ordered_apis(self) -> List[str]:
        """Get APIs ordered by reliability score"""
        return sorted(
            self.api_configs.keys(),
            key=lambda x: self.api_configs[x]['reliability_score'],
            reverse=True
        )
    
    def is_api_available(self, api_name: str) -> bool:
        """Check if API is available (has key if required)"""
        config = self.api_configs.get(api_name, {})
        if config.get('requires_key', False):
            return self.api_keys.get(api_name) is not None
        return True
    
    def get_api_endpoint(self, api_name: str, endpoint_type: str) -> str:
        """Get API endpoint URL"""
        return self.api_configs.get(api_name, {}).get('endpoints', {}).get(endpoint_type, '')
    
    def get_api_key(self, api_name: str) -> str:
        """Get API key for service"""
        return self.api_keys.get(api_name, '')
    
    def get_rate_limit(self, api_name: str) -> int:
        """Get rate limit for API"""
        return self.api_configs.get(api_name, {}).get('rate_limit', 10)

# Global configuration instance
api_config = APIConfig()

# Environment setup instructions
SETUP_INSTRUCTIONS = """
🔧 API SETUP (Optional - improves reliability):

Set these environment variables for better API access:

export CRYPTOCOMPARE_API_KEY="your_key_here"
export COINGECKO_API_KEY="your_key_here" 
export BINANCE_API_KEY="your_key_here"

Or add to your .env file:
CRYPTOCOMPARE_API_KEY=your_key_here
COINGECKO_API_KEY=your_key_here
BINANCE_API_KEY=your_key_here

Benefits:
- Higher rate limits
- More reliable access
- Premium features
- Reduced blocking
"""