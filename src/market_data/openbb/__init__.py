"""
OpenBB Platform Integration Package
Modular market data provider with comprehensive analysis capabilities
"""

from .client import OpenBBClient
from .crypto_data import CryptoDataProvider
from .market_analysis import MarketAnalyzer
from .data_formatter import (
    MarketDepthData,
    DeltaAnalysis,
    VolumeProfile,
    InstitutionalData,
    DataFormatter
)

# Main provider class that combines all modules
class OpenBBMarketDataProvider:
    """
    Main market data provider combining all OpenBB modules
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.client = OpenBBClient(config)
        self.crypto_provider = CryptoDataProvider(self.client)
        self.analyzer = MarketAnalyzer(self.client, self.crypto_provider)
        self.formatter = DataFormatter()

    async def get_market_depth(self, symbol: str, exchange: str = "binance"):
        """Get market depth data"""
        return await self.analyzer.get_market_depth(symbol, exchange)

    async def get_delta_analysis(self, symbol: str, timeframe: str = "1m", periods: int = 100):
        """Get delta analysis"""
        return await self.analyzer.get_delta_analysis(symbol, timeframe, periods)

    async def get_volume_profile(self, symbol: str, timeframe: str = "1h", periods: int = 100):
        """Get volume profile"""
        return await self.analyzer.get_volume_profile(symbol, timeframe, periods)

    async def get_institutional_data(self, symbol: str):
        """Get institutional data"""
        return await self.analyzer.get_institutional_data(symbol)

    async def get_comprehensive_analysis(self, symbol: str):
        """Get comprehensive market analysis"""
        return await self.analyzer.get_comprehensive_analysis(symbol)


# Convenience function for backward compatibility
async def get_market_analysis(symbol: str, config=None):
    """
    Convenience function to get comprehensive market analysis
    """
    provider = OpenBBMarketDataProvider(config)
    return await provider.get_comprehensive_analysis(symbol)


__all__ = [
    'OpenBBMarketDataProvider',
    'OpenBBClient',
    'CryptoDataProvider',
    'MarketAnalyzer',
    'DataFormatter',
    'MarketDepthData',
    'DeltaAnalysis',
    'VolumeProfile',
    'InstitutionalData',
    'get_market_analysis'
]
