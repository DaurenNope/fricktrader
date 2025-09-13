import requests
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class MarketDataProvider:
    """Live market data with advanced analysis"""
    
    @staticmethod
    def get_crypto_prices() -> Dict:
        """Get real crypto prices with enhanced data"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': 'bitcoin,ethereum,solana,cardano,polkadot,chainlink,avalanche-2,matic-network,uniswap,cosmos',
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Enhanced market data mapping
            market_data = {}
            crypto_mapping = {
                'BTC/USDT': ('bitcoin', 'Bitcoin'),
                'ETH/USDT': ('ethereum', 'Ethereum'),
                'SOL/USDT': ('solana', 'Solana'),
                'ADA/USDT': ('cardano', 'Cardano'),
                'DOT/USDT': ('polkadot', 'Polkadot'),
                'LINK/USDT': ('chainlink', 'Chainlink'),
                'AVAX/USDT': ('avalanche-2', 'Avalanche'),
                'MATIC/USDT': ('matic-network', 'Polygon'),
                'UNI/USDT': ('uniswap', 'Uniswap'),
                'ATOM/USDT': ('cosmos', 'Cosmos')
            }
            
            for pair, (coin_id, name) in crypto_mapping.items():
                coin_data = data.get(coin_id, {})
                market_data[pair] = {
                    'name': name,
                    'price': coin_data.get('usd', 0),
                    'change_24h': coin_data.get('usd_24h_change', 0),
                    'volume_24h': coin_data.get('usd_24h_vol', 0),
                    'market_cap': coin_data.get('usd_market_cap', 0)
                }
            
            return market_data
            
        except Exception as e:
            logger.error(f"Failed to get live prices: {e}")
            return {}
    
    @staticmethod
    def get_fear_greed_index() -> Dict:
        """Get Fear & Greed Index"""
        try:
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data['data']:
                return {
                    'value': int(data['data'][0]['value']),
                    'classification': data['data'][0]['value_classification'],
                    'timestamp': data['data'][0]['timestamp']
                }
        except Exception as e:
            logger.error(f"Failed to get Fear & Greed: {e}")
            
        return {'value': 50, 'classification': 'Neutral', 'timestamp': ''}
    
    @staticmethod
    def get_market_overview() -> Dict:
        """Get comprehensive market overview"""
        try:
            # Get global market data
            url = "https://api.coingecko.com/api/v3/global"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            global_data = response.json()['data']
            
            return {
                'total_market_cap': global_data.get('total_market_cap', {}).get('usd', 0),
                'total_volume': global_data.get('total_volume', {}).get('usd', 0),
                'market_cap_change_24h': global_data.get('market_cap_change_percentage_24h_usd', 0),
                'active_cryptocurrencies': global_data.get('active_cryptocurrencies', 0),
                'bitcoin_dominance': global_data.get('market_cap_percentage', {}).get('btc', 0),
                'ethereum_dominance': global_data.get('market_cap_percentage', {}).get('eth', 0),
                'fear_greed': MarketDataProvider.get_fear_greed_index()
            }
            
        except Exception as e:
            logger.error(f"Failed to get market overview: {e}")
            return {}
