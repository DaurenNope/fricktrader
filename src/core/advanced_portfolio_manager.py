"""
Advanced Portfolio Manager with Market Regime Integration
Integrates the Market Regime Analyzer to dynamically adjust strategy allocations
based on real-time market conditions.
"""

import logging
import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np

from market_analysis.crypto_market_regime_analyzer import (
    CryptoMarketRegimeAnalyzer, 
    MarketRegimeResult,
    MarketRegime,
    VolatilityRegime,
    get_strategy_permissions
)

logger = logging.getLogger(__name__)

@dataclass
class StrategyAllocation:
    """Enhanced strategy allocation with regime-based controls"""
    strategy_name: str
    current_allocation: float
    target_allocation: float
    max_allocation: float
    min_allocation: float
    enabled: bool
    regime_suitability: float  # How suitable this strategy is for current regime
    performance_score: float   # Recent performance metric
    risk_contribution: float   # Contribution to portfolio risk

@dataclass
class PortfolioState:
    """Current portfolio state with regime information"""
    total_balance: float
    allocated_balance: float
    available_balance: float
    active_strategies: List[str]
    market_regime: MarketRegime
    regime_confidence: float
    total_risk_exposure: float
    strategy_allocations: Dict[str, StrategyAllocation]
    last_rebalance: datetime

class AdvancedPortfolioManager:
    """
    Advanced portfolio management with market regime integration
    
    Key Features:
    - Dynamic strategy allocation based on market regime
    - Risk-adjusted position sizing
    - Performance-based allocation adjustments
    - Regime transition handling
    - Portfolio heat management
    """
    
    def __init__(self,
                 initial_balance: float = 10000.0,
                 max_total_risk: float = 0.06,  # 6% max portfolio risk
                 rebalance_frequency_hours: int = 4,
                 regime_change_threshold: float = 0.7):
        
        self.initial_balance = initial_balance
        self.max_total_risk = max_total_risk
        self.rebalance_frequency_hours = rebalance_frequency_hours
        self.regime_change_threshold = regime_change_threshold
        
        # Initialize components
        self.regime_analyzer = CryptoMarketRegimeAnalyzer()
        self.current_regime_result: Optional[MarketRegimeResult] = None
        self.portfolio_state: Optional[PortfolioState] = None
        
        # Performance tracking
        self.strategy_performance_history: Dict[str, List[float]] = {}
        self.regime_history: List[MarketRegimeResult] = []
        self.allocation_history: List[Dict[str, float]] = []
        
        # Initialize default strategy configurations
        self.default_strategy_configs = {
            "MegaMomentumStrategy": {
                "max_allocation": 0.45,
                "min_allocation": 0.0,
                "risk_multiplier": 1.2,  # Higher risk tolerance
                "regime_preferences": [MarketRegime.BULL, MarketRegime.TRANSITIONAL]
            },
            "SmartLiquidityStrategy": {
                "max_allocation": 0.50,
                "min_allocation": 0.20,
                "risk_multiplier": 0.8,  # Lower risk (tight stops)
                "regime_preferences": [MarketRegime.BULL, MarketRegime.BEAR, MarketRegime.SIDEWAYS]
            },
            "short_strategies": {
                "max_allocation": 0.60,
                "min_allocation": 0.0,
                "risk_multiplier": 1.0,
                "regime_preferences": [MarketRegime.BEAR]
            },
            "mean_reversion": {
                "max_allocation": 0.40,
                "min_allocation": 0.0,
                "risk_multiplier": 0.9,
                "regime_preferences": [MarketRegime.SIDEWAYS, MarketRegime.TRANSITIONAL]
            }
        }
        
        logger.info(f"Advanced Portfolio Manager initialized with ${initial_balance:,.2f}")
    
    def analyze_and_rebalance(self, market_data: Dict[str, pd.DataFrame]) -> PortfolioState:
        """
        Main method: Analyze market regime and rebalance portfolio accordingly
        
        Args:
            market_data: Dict containing BTC, ETH, and other market data
            
        Returns:
            Updated portfolio state
        """
        try:
            # 1. Analyze current market regime
            regime_result = self.regime_analyzer.analyze_market_regime(market_data)
            self.current_regime_result = regime_result
            self.regime_history.append(regime_result)
            
            logger.info(f"Market Regime: {regime_result.market_regime.value.upper()}")
            logger.info(f"Volatility: {regime_result.volatility_regime.value}")
            logger.info(f"Risk Environment: {regime_result.risk_environment.value}")
            logger.info(f"Confidence: {regime_result.confidence_score:.2%}")
            
            # 2. Check if rebalancing is needed
            if self._should_rebalance(regime_result):
                logger.info("Portfolio rebalancing triggered")
                
                # 3. Get strategy permissions from regime analyzer
                strategy_permissions = get_strategy_permissions(regime_result)
                
                # 4. Calculate optimal allocations
                optimal_allocations = self._calculate_optimal_allocations(
                    strategy_permissions, regime_result
                )
                
                # 5. Update portfolio state
                self.portfolio_state = self._update_portfolio_state(
                    optimal_allocations, regime_result
                )
                
                # 6. Log allocation changes
                self._log_allocation_changes(optimal_allocations)
                
            else:
                # Update regime info without rebalancing
                if self.portfolio_state:
                    self.portfolio_state.market_regime = regime_result.market_regime
                    self.portfolio_state.regime_confidence = regime_result.confidence_score
            
            return self.portfolio_state or self._create_initial_portfolio_state(regime_result)
            
        except Exception as e:
            logger.error(f"Error in portfolio analysis and rebalancing: {e}")
            return self._create_emergency_portfolio_state()
    
    def get_strategy_allocation(self, strategy_name: str) -> float:
        """Get current allocation percentage for a specific strategy"""
        if not self.portfolio_state or strategy_name not in self.portfolio_state.strategy_allocations:
            return 0.0
        
        return self.portfolio_state.strategy_allocations[strategy_name].current_allocation
    
    def is_strategy_enabled(self, strategy_name: str) -> bool:
        """Check if a strategy is currently enabled"""
        if not self.portfolio_state or strategy_name not in self.portfolio_state.strategy_allocations:
            return False
        
        return self.portfolio_state.strategy_allocations[strategy_name].enabled
    
    def get_regime_info(self) -> Optional[MarketRegimeResult]:
        """Get current market regime information"""
        return self.current_regime_result
    
    def update_strategy_performance(self, strategy_name: str, performance: float):
        """Update performance tracking for a strategy"""
        if strategy_name not in self.strategy_performance_history:
            self.strategy_performance_history[strategy_name] = []
        
        self.strategy_performance_history[strategy_name].append(performance)
        
        # Keep only last 30 performance records
        if len(self.strategy_performance_history[strategy_name]) > 30:
            self.strategy_performance_history[strategy_name] = \
                self.strategy_performance_history[strategy_name][-30:]
    
    def _should_rebalance(self, regime_result: MarketRegimeResult) -> bool:
        """Determine if portfolio rebalancing is needed"""
        
        # Always rebalance on first run
        if not self.portfolio_state:
            return True
        
        # Check if regime changed significantly
        previous_regime = self.portfolio_state.market_regime
        if regime_result.market_regime != previous_regime:
            logger.info(f"Regime change detected: {previous_regime.value} -> {regime_result.market_regime.value}")
            return True
        
        # Check confidence level change
        confidence_change = abs(regime_result.confidence_score - self.portfolio_state.regime_confidence)
        if confidence_change > 0.3:
            logger.info(f"Major confidence change: {confidence_change:.2%}")
            return True
        
        # Check time-based rebalancing
        time_since_rebalance = datetime.now() - self.portfolio_state.last_rebalance
        if time_since_rebalance > timedelta(hours=self.rebalance_frequency_hours):
            logger.info("Time-based rebalancing triggered")
            return True
        
        return False
    
    def _calculate_optimal_allocations(self, 
                                    strategy_permissions: Dict[str, Dict[str, float]],
                                    regime_result: MarketRegimeResult) -> Dict[str, float]:
        """Calculate optimal strategy allocations based on regime and performance"""
        
        allocations = {}
        total_allocation = 0.0
        
        # Get base allocations from regime permissions
        for strategy_name, permissions in strategy_permissions.items():
            base_allocation = permissions.get("allocation", 0.0)
            enabled = permissions.get("enabled", True)
            
            if not enabled:
                allocations[strategy_name] = 0.0
                continue
            
            # Adjust based on recent performance
            performance_adjustment = self._get_performance_adjustment(strategy_name)
            
            # Adjust based on confidence in regime
            confidence_adjustment = regime_result.confidence_score
            
            # Adjust based on volatility regime
            volatility_adjustment = self._get_volatility_adjustment(
                strategy_name, regime_result.volatility_regime
            )
            
            # Calculate final allocation
            final_allocation = base_allocation * performance_adjustment * confidence_adjustment * volatility_adjustment
            
            # Apply strategy-specific limits
            config = self.default_strategy_configs.get(strategy_name, {})
            max_allocation = config.get("max_allocation", 1.0)
            min_allocation = config.get("min_allocation", 0.0)
            
            final_allocation = np.clip(final_allocation, min_allocation, max_allocation)
            
            allocations[strategy_name] = final_allocation
            total_allocation += final_allocation
        
        # Normalize to ensure total doesn't exceed 100%
        if total_allocation > 1.0:
            for strategy_name in allocations:
                allocations[strategy_name] = allocations[strategy_name] / total_allocation
        
        # Keep some cash reserve (5-15% based on regime uncertainty)
        cash_reserve = 0.05 + (1 - regime_result.confidence_score) * 0.10
        for strategy_name in allocations:
            allocations[strategy_name] *= (1 - cash_reserve)
        
        return allocations
    
    def _get_performance_adjustment(self, strategy_name: str) -> float:
        """Get performance-based allocation adjustment"""
        if strategy_name not in self.strategy_performance_history:
            return 1.0  # Neutral for new strategies
        
        performances = self.strategy_performance_history[strategy_name]
        if len(performances) < 5:
            return 1.0  # Need sufficient data
        
        # Calculate recent performance score
        recent_performance = np.mean(performances[-10:])  # Last 10 trades
        
        # Convert to adjustment factor (0.5x to 1.5x allocation)
        if recent_performance > 0.05:  # Strong performance
            return 1.3
        elif recent_performance > 0.02:  # Good performance
            return 1.1
        elif recent_performance > -0.02:  # Neutral performance
            return 1.0
        elif recent_performance > -0.05:  # Poor performance
            return 0.8
        else:  # Very poor performance
            return 0.5
    
    def _get_volatility_adjustment(self, strategy_name: str, volatility_regime: VolatilityRegime) -> float:
        """Adjust allocations based on volatility regime"""
        
        if volatility_regime == VolatilityRegime.EXPLOSIVE:
            # Reduce allocations in explosive volatility, except for strategies that thrive on it
            if "Momentum" in strategy_name:
                return 1.2  # Momentum strategies benefit from volatility
            else:
                return 0.7  # Reduce others
        
        elif volatility_regime == VolatilityRegime.HIGH:
            return 0.9  # Slightly reduce allocations
        
        elif volatility_regime == VolatilityRegime.LOW:
            # Increase allocations in low volatility
            if "Liquidity" in strategy_name or "mean_reversion" in strategy_name:
                return 1.1  # These strategies work well in low vol
            else:
                return 1.0
        
        return 1.0  # Normal volatility
    
    def _update_portfolio_state(self, 
                              allocations: Dict[str, float],
                              regime_result: MarketRegimeResult) -> PortfolioState:
        """Update portfolio state with new allocations"""
        
        strategy_allocations = {}
        total_risk = 0.0
        allocated_balance = 0.0
        
        for strategy_name, allocation in allocations.items():
            
            # Calculate risk contribution
            risk_contribution = allocation * self.default_strategy_configs.get(strategy_name, {}).get("risk_multiplier", 1.0) * 0.02  # Base 2% risk per strategy
            total_risk += risk_contribution
            allocated_balance += allocation * self.initial_balance
            
            strategy_allocations[strategy_name] = StrategyAllocation(
                strategy_name=strategy_name,
                current_allocation=allocation,
                target_allocation=allocation,
                max_allocation=self.default_strategy_configs.get(strategy_name, {}).get("max_allocation", 1.0),
                min_allocation=self.default_strategy_configs.get(strategy_name, {}).get("min_allocation", 0.0),
                enabled=allocation > 0.01,  # Consider enabled if >1% allocation
                regime_suitability=self._calculate_regime_suitability(strategy_name, regime_result.market_regime),
                performance_score=self._get_performance_score(strategy_name),
                risk_contribution=risk_contribution
            )
        
        return PortfolioState(
            total_balance=self.initial_balance,
            allocated_balance=allocated_balance,
            available_balance=self.initial_balance - allocated_balance,
            active_strategies=[s for s, a in allocations.items() if a > 0.01],
            market_regime=regime_result.market_regime,
            regime_confidence=regime_result.confidence_score,
            total_risk_exposure=total_risk,
            strategy_allocations=strategy_allocations,
            last_rebalance=datetime.now()
        )
    
    def _calculate_regime_suitability(self, strategy_name: str, regime: MarketRegime) -> float:
        """Calculate how suitable a strategy is for current regime"""
        preferred_regimes = self.default_strategy_configs.get(strategy_name, {}).get("regime_preferences", [])
        
        if regime in preferred_regimes:
            return 1.0 if regime == preferred_regimes[0] else 0.8
        else:
            return 0.3
    
    def _get_performance_score(self, strategy_name: str) -> float:
        """Get recent performance score for a strategy"""
        if strategy_name not in self.strategy_performance_history:
            return 0.0
        
        performances = self.strategy_performance_history[strategy_name]
        if not performances:
            return 0.0
        
        return np.mean(performances[-5:])  # Average of last 5 performances
    
    def _create_initial_portfolio_state(self, regime_result: MarketRegimeResult) -> PortfolioState:
        """Create initial portfolio state"""
        # Start with conservative allocation
        strategy_allocations = {
            "SmartLiquidityStrategy": StrategyAllocation(
                strategy_name="SmartLiquidityStrategy",
                current_allocation=0.6,
                target_allocation=0.6,
                max_allocation=0.5,
                min_allocation=0.2,
                enabled=True,
                regime_suitability=0.8,
                performance_score=0.0,
                risk_contribution=0.012
            )
        }
        
        return PortfolioState(
            total_balance=self.initial_balance,
            allocated_balance=self.initial_balance * 0.6,
            available_balance=self.initial_balance * 0.4,
            active_strategies=["SmartLiquidityStrategy"],
            market_regime=regime_result.market_regime,
            regime_confidence=regime_result.confidence_score,
            total_risk_exposure=0.012,
            strategy_allocations=strategy_allocations,
            last_rebalance=datetime.now()
        )
    
    def _create_emergency_portfolio_state(self) -> PortfolioState:
        """Create emergency conservative portfolio state on error"""
        return PortfolioState(
            total_balance=self.initial_balance,
            allocated_balance=0.0,
            available_balance=self.initial_balance,
            active_strategies=[],
            market_regime=MarketRegime.SIDEWAYS,
            regime_confidence=0.3,
            total_risk_exposure=0.0,
            strategy_allocations={},
            last_rebalance=datetime.now()
        )
    
    def _log_allocation_changes(self, allocations: Dict[str, float]):
        """Log allocation changes for monitoring"""
        logger.info("Portfolio Allocation Update:")
        for strategy_name, allocation in allocations.items():
            if allocation > 0.01:  # Only log meaningful allocations
                logger.info(f"  {strategy_name}: {allocation:.1%}")
        
        total_allocated = sum(allocations.values())
        cash_reserve = 1.0 - total_allocated
        logger.info(f"  Cash Reserve: {cash_reserve:.1%}")
        
        # Store in history
        self.allocation_history.append(allocations)
        if len(self.allocation_history) > 100:  # Keep last 100 records
            self.allocation_history = self.allocation_history[-100:]
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary"""
        if not self.portfolio_state or not self.current_regime_result:
            return {"status": "Not initialized"}
        
        return {
            "regime_info": {
                "market_regime": self.current_regime_result.market_regime.value,
                "volatility_regime": self.current_regime_result.volatility_regime.value,
                "risk_environment": self.current_regime_result.risk_environment.value,
                "confidence": f"{self.current_regime_result.confidence_score:.1%}",
                "regime_duration": f"{self.current_regime_result.regime_duration} days"
            },
            "portfolio_metrics": {
                "total_balance": f"${self.portfolio_state.total_balance:,.2f}",
                "allocated_balance": f"${self.portfolio_state.allocated_balance:,.2f}",
                "available_balance": f"${self.portfolio_state.available_balance:,.2f}",
                "total_risk_exposure": f"{self.portfolio_state.total_risk_exposure:.2%}",
                "active_strategies": len(self.portfolio_state.active_strategies)
            },
            "strategy_allocations": {
                name: {
                    "allocation": f"{alloc.current_allocation:.1%}",
                    "enabled": alloc.enabled,
                    "regime_suitability": f"{alloc.regime_suitability:.1%}",
                    "risk_contribution": f"{alloc.risk_contribution:.2%}"
                }
                for name, alloc in self.portfolio_state.strategy_allocations.items()
                if alloc.current_allocation > 0.01
            }
        }