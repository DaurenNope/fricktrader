"""
OpenBB Platform Integration for Advanced Market Data
Provides comprehensive market data including order flow, delta analysis, and institutional data
Similar to Tiger Trade's advanced features

This module now imports from the modular openbb package for better organization.
"""

# Import all functionality from the new modular structure
from .openbb import (
    OpenBBMarketDataProvider,
    MarketDepthData,
    DeltaAnalysis,
    VolumeProfile,
    InstitutionalData,
    get_market_analysis
)

# Re-export everything for backward compatibility
__all__ = [
    'OpenBBMarketDataProvider',
    'MarketDepthData',
    'DeltaAnalysis',
    'VolumeProfile',
    'InstitutionalData',
    'get_market_analysis'
]

# For backward compatibility - allow direct import of the main class
OpenBBProvider = OpenBBMarketDataProvider
