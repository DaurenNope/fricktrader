"""
DeFi Yield Optimization Module
Advanced yield optimization across major DeFi protocols
"""

from .core_engine import DeFiYieldOptimizer
from .models import (
    YieldOpportunity,
    ProtocolType,
    RiskLevel,
    PortfolioAllocation,
    PortfolioMetrics,
    ExecutionStep,
    RiskAssessment,
    ExitStrategy,
    MonitoringAlert
)
from .opportunity_analyzer import OpportunityAnalyzer
from .protocol_analyzers import (
    BaseProtocolAnalyzer,
    ProtocolAnalyzerRegistry,
    UniswapAnalyzer,
    EthenaAnalyzer,
    PendleAnalyzer,
    ResolvAnalyzer,
    AaveAnalyzer
)
from .portfolio_optimizer import PortfolioOptimizer

__all__ = [
    # Main engine
    'DeFiYieldOptimizer',

    # Data models
    'YieldOpportunity',
    'ProtocolType',
    'RiskLevel',
    'PortfolioAllocation',
    'PortfolioMetrics',
    'ExecutionStep',
    'RiskAssessment',
    'ExitStrategy',
    'MonitoringAlert',

    # Core components
    'OpportunityAnalyzer',
    'PortfolioOptimizer',

    # Protocol analyzers
    'BaseProtocolAnalyzer',
    'ProtocolAnalyzerRegistry',
    'UniswapAnalyzer',
    'EthenaAnalyzer',
    'PendleAnalyzer',
    'ResolvAnalyzer',
    'AaveAnalyzer'
]

# Version info
__version__ = '1.0.0'
__author__ = 'FrickTrader Development Team'
