"""
Data models for DeFi Yield Optimization
Contains all data structures and enums used across the system
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any


class ProtocolType(Enum):
    """Types of DeFi protocols"""
    DEX = "DEX"
    LENDING = "LENDING"
    LIQUID_STAKING = "LIQUID_STAKING"
    PERPETUALS = "PERPETUALS"
    YIELD_AGGREGATOR = "YIELD_AGGREGATOR"
    SYNTHETIC = "SYNTHETIC"
    OPTIONS = "OPTIONS"


class RiskLevel(Enum):
    """Risk levels for DeFi strategies"""
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5


@dataclass
class YieldOpportunity:
    """
    Represents a DeFi yield opportunity with all relevant metrics
    """
    protocol: str
    protocol_type: ProtocolType
    pool_id: str
    pool_name: str
    asset_pair: List[str]
    base_apy: float
    boosted_apy: float  # With rewards/incentives
    total_apy: float
    tvl: float
    volume_24h: float
    risk_score: float
    risk_level: RiskLevel
    impermanent_loss_risk: float
    smart_contract_risk: float
    liquidity_risk: float
    reward_tokens: List[str]
    entry_requirements: Dict[str, Any]
    exit_conditions: Dict[str, Any]
    fees: Dict[str, float]
    lockup_period: Optional[int]  # days
    auto_compound: bool
    verified_strategy: bool
    historical_performance: Dict[str, float]
    current_utilization: float
    deposit_cap: Optional[float]
    minimum_deposit: float
    estimated_gas_cost: float

    def get_risk_adjusted_return(self) -> float:
        """Calculate risk-adjusted return"""
        return self.total_apy / (1 + self.risk_score)

    def get_efficiency_score(self) -> float:
        """Calculate overall efficiency score"""
        return (self.total_apy * 0.4 +
                (100 - self.risk_score) * 0.3 +
                min(self.tvl / 1000000, 100) * 0.2 +  # TVL factor
                min(self.volume_24h / 100000, 100) * 0.1)  # Volume factor


@dataclass
class PortfolioAllocation:
    """
    Represents an allocation recommendation for a portfolio
    """
    token: str
    opportunity: YieldOpportunity
    allocated_amount: float
    allocation_percent: float
    expected_return: float
    risk_contribution: float


@dataclass
class PortfolioMetrics:
    """
    Portfolio-level metrics for a DeFi yield strategy
    """
    total_allocated: float
    weighted_apy: float
    weighted_risk: float
    total_gas_cost: float
    diversification_score: int
    expected_annual_return: float
    risk_adjusted_return: float
    number_of_positions: int


@dataclass
class ExecutionStep:
    """
    Individual step in strategy execution
    """
    step_number: int
    description: str
    estimated_gas: Optional[float] = None
    estimated_time: Optional[str] = None
    required_approvals: Optional[List[str]] = None


@dataclass
class RiskAssessment:
    """
    Risk assessment for a yield opportunity
    """
    overall_risk_score: float
    risk_level: RiskLevel
    impermanent_loss_risk: float
    smart_contract_risk: float
    liquidity_risk: float
    counterparty_risk: float
    regulatory_risk: float
    key_risks: List[str]
    risk_mitigation: List[str]


@dataclass
class ExitStrategy:
    """
    Exit strategy for a DeFi position
    """
    profit_targets: List[Dict[str, Any]]
    risk_triggers: List[Dict[str, Any]]
    time_based_rules: Dict[str, Any]
    monitoring_frequency: str
    emergency_exit_conditions: List[str]


@dataclass
class MonitoringAlert:
    """
    Monitoring alert configuration
    """
    metric: str
    threshold: float
    comparison: str  # 'above', 'below', 'change_percent'
    alert_level: str  # 'info', 'warning', 'critical'
    action_required: str
