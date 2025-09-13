"""
Advanced Portfolio Management System
Handles multiple strategies, market regime detection, and capital allocation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    BULL_STRONG = "bull_strong"      # Strong uptrend, use momentum strategies
    BULL_MODERATE = "bull_moderate"   # Moderate uptrend, use trend following
    SIDEWAYS = "sideways"            # Range-bound, use mean reversion
    BEAR_MODERATE = "bear_moderate"   # Moderate downtrend, use defensive
    BEAR_STRONG = "bear_strong"      # Strong downtrend, cash/short strategies
    ACCUMULATION = "accumulation"    # Building base, use breakout strategies
    DISTRIBUTION = "distribution"    # Topping out, use defensive strategies

class StrategyType(Enum):
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"  
    MOMENTUM_BREAKOUT = "momentum_breakout"
    SMART_MONEY = "smart_money"
    DEFENSIVE = "defensive"
    SCALPING = "scalping"

@dataclass
class StrategyAllocation:
    strategy_name: str
    strategy_type: StrategyType
    allocation_pct: float  # 0-100
    active: bool
    min_allocation: float = 5.0  # Minimum 5%
    max_allocation: float = 50.0  # Maximum 50% 
    
@dataclass
class MarketCondition:
    regime: MarketRegime
    trend_strength: float  # -1 to 1
    volatility_percentile: float  # 0-100
    volume_trend: float  # -1 to 1
    confidence: float  # 0-1
    last_updated: datetime

class PortfolioManager:
    """
    Advanced Portfolio Manager that:
    1. Detects market regimes automatically
    2. Allocates capital across multiple strategies
    3. Rebalances based on performance and market conditions
    4. Manages risk across the entire portfolio
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.total_capital = config.get('total_capital', 10000)
        self.max_strategies = config.get('max_strategies', 5)
        self.rebalance_frequency = config.get('rebalance_hours', 24)
        
        # Strategy configurations
        self.strategies: Dict[str, StrategyAllocation] = {}
        self.strategy_performance: Dict[str, Dict] = {}
        
        # Market analysis
        self.current_market_condition: Optional[MarketCondition] = None
        self.market_history: List[MarketCondition] = []
        
        # Performance tracking
        self.portfolio_value_history: List[Tuple[datetime, float]] = []
        self.last_rebalance: Optional[datetime] = None
        
        self._initialize_strategies()
        
    def _initialize_strategies(self):
        """Initialize available strategies with default allocations"""
        
        default_strategies = [
            StrategyAllocation(
                strategy_name="MegaMomentumStrategy",
                strategy_type=StrategyType.MOMENTUM_BREAKOUT,
                allocation_pct=35.0,
                active=True,
                max_allocation=45.0
            ),
            StrategyAllocation(
                strategy_name="SmartLiquidityStrategy", 
                strategy_type=StrategyType.SMART_MONEY,
                allocation_pct=30.0,
                active=True,
                max_allocation=40.0
            ),
            StrategyAllocation(
                strategy_name="SimpleTrendStrategy",
                strategy_type=StrategyType.TREND_FOLLOWING,
                allocation_pct=20.0,
                active=True,
                max_allocation=30.0
            ),
            StrategyAllocation(
                strategy_name="ExplosiveMomentumStrategy",
                strategy_type=StrategyType.MOMENTUM_BREAKOUT,
                allocation_pct=15.0,
                active=False,  # Backup strategy
                min_allocation=0.0,
                max_allocation=25.0
            )
        ]
        
        for strategy in default_strategies:
            self.strategies[strategy.strategy_name] = strategy
            self.strategy_performance[strategy.strategy_name] = {
                'total_return': 0.0,
                'win_rate': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'trades_count': 0,
                'last_updated': datetime.now()
            }
    
    def analyze_market_regime(self, market_data: Dict) -> MarketCondition:
        """
        Analyze current market conditions and determine regime
        Uses multiple timeframes and indicators
        """
        try:
            # Get price data for major pairs
            btc_data = market_data.get('BTC/USDT', {})
            eth_data = market_data.get('ETH/USDT', {})
            
            if not btc_data or not eth_data:
                logger.warning("Insufficient market data for regime analysis")
                return MarketCondition(
                    regime=MarketRegime.SIDEWAYS,
                    trend_strength=0.0,
                    volatility_percentile=50.0,
                    volume_trend=0.0,
                    confidence=0.3,
                    last_updated=datetime.now()
                )
            
            # Calculate trend strength (multiple timeframes)
            trend_strength = self._calculate_trend_strength(btc_data, eth_data)
            
            # Calculate volatility percentile
            volatility_percentile = self._calculate_volatility_percentile(btc_data)
            
            # Calculate volume trend
            volume_trend = self._calculate_volume_trend(btc_data, eth_data)
            
            # Determine regime based on conditions
            regime = self._determine_regime(trend_strength, volatility_percentile, volume_trend)
            
            # Calculate confidence based on consistency
            confidence = self._calculate_confidence(trend_strength, volatility_percentile, volume_trend)
            
            condition = MarketCondition(
                regime=regime,
                trend_strength=trend_strength,
                volatility_percentile=volatility_percentile,
                volume_trend=volume_trend,
                confidence=confidence,
                last_updated=datetime.now()
            )
            
            self.current_market_condition = condition
            self.market_history.append(condition)
            
            # Keep only last 100 market conditions
            if len(self.market_history) > 100:
                self.market_history = self.market_history[-100:]
            
            return condition
            
        except Exception as e:
            logger.error(f"Error analyzing market regime: {e}")
            return MarketCondition(
                regime=MarketRegime.SIDEWAYS,
                trend_strength=0.0,
                volatility_percentile=50.0,
                volume_trend=0.0,
                confidence=0.1,
                last_updated=datetime.now()
            )
    
    def _calculate_trend_strength(self, btc_data: Dict, eth_data: Dict) -> float:
        """Calculate overall trend strength (-1 to 1)"""
        try:
            scores = []
            
            for symbol, data in [('BTC', btc_data), ('ETH', eth_data)]:
                if 'close' not in data or len(data['close']) < 50:
                    continue
                    
                prices = np.array(data['close'][-50:])  # Last 50 candles
                
                # Short-term trend (20 periods)
                sma_20 = np.mean(prices[-20:])
                sma_50 = np.mean(prices[-50:])
                short_trend = (sma_20 - sma_50) / sma_50
                
                # Price momentum 
                current_price = prices[-1]
                price_20_ago = prices[-20] if len(prices) >= 20 else prices[0]
                momentum = (current_price - price_20_ago) / price_20_ago
                
                # EMA slope
                ema_21 = pd.Series(prices).ewm(span=21).mean()
                ema_slope = (ema_21.iloc[-1] - ema_21.iloc[-5]) / ema_21.iloc[-5]
                
                # Combine scores
                symbol_score = np.mean([short_trend, momentum, ema_slope])
                scores.append(symbol_score)
            
            if not scores:
                return 0.0
                
            # Average and normalize to -1 to 1
            trend_strength = np.mean(scores)
            return max(-1.0, min(1.0, trend_strength * 5))  # Scale up sensitivity
            
        except Exception as e:
            logger.error(f"Error calculating trend strength: {e}")
            return 0.0
    
    def _calculate_volatility_percentile(self, btc_data: Dict) -> float:
        """Calculate volatility percentile (0-100)"""
        try:
            if 'high' not in btc_data or 'low' not in btc_data or len(btc_data['high']) < 100:
                return 50.0
                
            # Calculate True Range for last 100 periods
            highs = np.array(btc_data['high'][-100:])
            lows = np.array(btc_data['low'][-100:])
            closes = np.array(btc_data['close'][-101:-1])  # Previous closes
            
            tr1 = highs - lows
            tr2 = np.abs(highs - closes)
            tr3 = np.abs(lows - closes)
            
            true_range = np.maximum(tr1, np.maximum(tr2, tr3))
            current_atr = np.mean(true_range[-14:])  # 14-period ATR
            
            # Calculate percentile vs historical ATR
            historical_atr = np.array([np.mean(true_range[i-13:i+1]) for i in range(13, len(true_range))])
            percentile = (current_atr > historical_atr).mean() * 100
            
            return percentile
            
        except Exception as e:
            logger.error(f"Error calculating volatility percentile: {e}")
            return 50.0
    
    def _calculate_volume_trend(self, btc_data: Dict, eth_data: Dict) -> float:
        """Calculate volume trend (-1 to 1)"""
        try:
            volume_scores = []
            
            for data in [btc_data, eth_data]:
                if 'volume' not in data or len(data['volume']) < 30:
                    continue
                    
                volumes = np.array(data['volume'][-30:])
                
                # Short vs long term volume
                recent_avg = np.mean(volumes[-10:])
                older_avg = np.mean(volumes[-30:-10])
                
                if older_avg > 0:
                    volume_trend = (recent_avg - older_avg) / older_avg
                    volume_scores.append(volume_trend)
            
            if not volume_scores:
                return 0.0
                
            return max(-1.0, min(1.0, np.mean(volume_scores)))
            
        except Exception as e:
            logger.error(f"Error calculating volume trend: {e}")
            return 0.0
    
    def _determine_regime(self, trend_strength: float, volatility_percentile: float, volume_trend: float) -> MarketRegime:
        """Determine market regime based on indicators"""
        
        # Strong bull market
        if trend_strength > 0.4 and volume_trend > 0.2 and volatility_percentile < 70:
            return MarketRegime.BULL_STRONG
        
        # Moderate bull market  
        elif trend_strength > 0.1 and trend_strength <= 0.4:
            return MarketRegime.BULL_MODERATE
            
        # Strong bear market
        elif trend_strength < -0.4 and volume_trend < -0.1:
            return MarketRegime.BEAR_STRONG
            
        # Moderate bear market
        elif trend_strength < -0.1 and trend_strength >= -0.4:
            return MarketRegime.BEAR_MODERATE
            
        # Accumulation phase
        elif abs(trend_strength) < 0.1 and volume_trend > 0.3 and volatility_percentile < 40:
            return MarketRegime.ACCUMULATION
            
        # Distribution phase
        elif abs(trend_strength) < 0.1 and volume_trend < -0.2 and volatility_percentile > 60:
            return MarketRegime.DISTRIBUTION
            
        # Default to sideways
        else:
            return MarketRegime.SIDEWAYS
    
    def _calculate_confidence(self, trend_strength: float, volatility_percentile: float, volume_trend: float) -> float:
        """Calculate confidence in regime classification"""
        
        # Higher confidence for extreme values
        trend_confidence = min(1.0, abs(trend_strength) * 2)
        volume_confidence = min(1.0, abs(volume_trend) * 2)
        
        # Volatility adds confidence for extreme regimes
        if volatility_percentile > 80 or volatility_percentile < 20:
            vol_confidence = 0.8
        else:
            vol_confidence = 0.4
            
        return np.mean([trend_confidence, volume_confidence, vol_confidence])
    
    def calculate_optimal_allocation(self, market_condition: MarketCondition, performance_data: Dict) -> Dict[str, float]:
        """
        Calculate optimal strategy allocation based on:
        1. Current market regime
        2. Historical performance
        3. Risk management rules
        """
        
        # Base allocations by market regime
        regime_allocations = {
            MarketRegime.BULL_STRONG: {
                StrategyType.TREND_FOLLOWING: 40.0,
                StrategyType.MOMENTUM_BREAKOUT: 30.0,
                StrategyType.SMART_MONEY: 20.0,
                StrategyType.SCALPING: 10.0
            },
            MarketRegime.BULL_MODERATE: {
                StrategyType.TREND_FOLLOWING: 35.0,
                StrategyType.SMART_MONEY: 30.0,
                StrategyType.MOMENTUM_BREAKOUT: 25.0,
                StrategyType.SCALPING: 10.0
            },
            MarketRegime.SIDEWAYS: {
                StrategyType.SMART_MONEY: 35.0,
                StrategyType.SCALPING: 30.0,
                StrategyType.MOMENTUM_BREAKOUT: 20.0,
                StrategyType.TREND_FOLLOWING: 15.0
            },
            MarketRegime.BEAR_MODERATE: {
                StrategyType.SMART_MONEY: 40.0,
                StrategyType.MOMENTUM_BREAKOUT: 30.0,
                StrategyType.DEFENSIVE: 30.0
            },
            MarketRegime.BEAR_STRONG: {
                StrategyType.DEFENSIVE: 50.0,
                StrategyType.SMART_MONEY: 30.0,
                StrategyType.MOMENTUM_BREAKOUT: 20.0
            },
            MarketRegime.ACCUMULATION: {
                StrategyType.MOMENTUM_BREAKOUT: 35.0,
                StrategyType.SMART_MONEY: 30.0,
                StrategyType.TREND_FOLLOWING: 25.0,
                StrategyType.SCALPING: 10.0
            },
            MarketRegime.DISTRIBUTION: {
                StrategyType.SMART_MONEY: 40.0,
                StrategyType.DEFENSIVE: 30.0,
                StrategyType.MOMENTUM_BREAKOUT: 20.0,
                StrategyType.TREND_FOLLOWING: 10.0
            }
        }
        
        base_allocation = regime_allocations.get(market_condition.regime, {})
        
        # Adjust based on recent performance
        adjusted_allocation = {}
        
        for strategy_name, strategy in self.strategies.items():
            if not strategy.active:
                continue
                
            # Get base allocation for this strategy type
            base_pct = base_allocation.get(strategy.strategy_type, 0.0)
            
            # Adjust based on performance
            perf = self.strategy_performance.get(strategy_name, {})
            
            # Performance multiplier (0.5 to 2.0)
            sharpe = perf.get('sharpe_ratio', 0.0)
            win_rate = perf.get('win_rate', 0.5)
            
            perf_multiplier = 1.0
            if sharpe > 1.0:
                perf_multiplier = min(2.0, 1.0 + (sharpe - 1.0) * 0.5)
            elif sharpe < -0.5:
                perf_multiplier = max(0.5, 1.0 + sharpe * 0.5)
                
            if win_rate > 0.6:
                perf_multiplier *= 1.2
            elif win_rate < 0.4:
                perf_multiplier *= 0.8
            
            # Calculate adjusted allocation
            adjusted_pct = base_pct * perf_multiplier * market_condition.confidence
            
            # Apply min/max constraints
            adjusted_pct = max(strategy.min_allocation, min(strategy.max_allocation, adjusted_pct))
            
            adjusted_allocation[strategy_name] = adjusted_pct
        
        # Normalize to 100%
        total_allocation = sum(adjusted_allocation.values())
        if total_allocation > 0:
            for strategy_name in adjusted_allocation:
                adjusted_allocation[strategy_name] = (adjusted_allocation[strategy_name] / total_allocation) * 100
        
        return adjusted_allocation
    
    def should_rebalance(self) -> bool:
        """Determine if portfolio should be rebalanced"""
        
        if self.last_rebalance is None:
            return True
            
        time_since_rebalance = datetime.now() - self.last_rebalance
        if time_since_rebalance.total_seconds() / 3600 >= self.rebalance_frequency:
            return True
            
        # Force rebalance if market regime changed significantly
        if (self.current_market_condition and 
            len(self.market_history) >= 2 and
            self.current_market_condition.regime != self.market_history[-2].regime):
            return True
            
        return False
    
    def rebalance_portfolio(self, market_data: Dict, performance_data: Dict) -> Dict:
        """
        Rebalance the entire portfolio:
        1. Analyze market conditions
        2. Calculate optimal allocations
        3. Generate rebalancing instructions
        """
        
        logger.info("Starting portfolio rebalance...")
        
        # Analyze current market
        market_condition = self.analyze_market_regime(market_data)
        
        # Calculate optimal allocations
        new_allocations = self.calculate_optimal_allocation(market_condition, performance_data)
        
        # Generate rebalancing instructions
        rebalance_instructions = {
            'timestamp': datetime.now().isoformat(),
            'market_regime': market_condition.regime.value,
            'confidence': market_condition.confidence,
            'allocations': new_allocations,
            'changes': {}
        }
        
        # Calculate changes from current allocations
        for strategy_name, new_pct in new_allocations.items():
            old_pct = self.strategies[strategy_name].allocation_pct
            change = new_pct - old_pct
            
            if abs(change) > 2.0:  # Only log significant changes
                rebalance_instructions['changes'][strategy_name] = {
                    'old_pct': round(old_pct, 1),
                    'new_pct': round(new_pct, 1), 
                    'change': round(change, 1)
                }
                
                # Update strategy allocation
                self.strategies[strategy_name].allocation_pct = new_pct
        
        self.last_rebalance = datetime.now()
        
        logger.info(f"Portfolio rebalanced for {market_condition.regime.value} market")
        logger.info(f"Significant changes: {rebalance_instructions['changes']}")
        
        return rebalance_instructions
    
    def get_strategy_configs(self) -> Dict:
        """Generate Freqtrade configurations for each active strategy"""
        
        configs = {}
        
        for strategy_name, allocation in self.strategies.items():
            if not allocation.active or allocation.allocation_pct < 1.0:
                continue
                
            # Calculate stake amount based on allocation
            stake_amount = (self.total_capital * allocation.allocation_pct / 100) / 5  # Divide by max_open_trades
            
            # Base config for this strategy
            config = {
                "strategy": strategy_name,
                "stake_amount": max(10, round(stake_amount, 2)),  # Minimum $10 per trade
                "max_open_trades": min(5, int(allocation.allocation_pct / 10)),  # More allocation = more concurrent trades
                "allocation_pct": allocation.allocation_pct,
                "active": True
            }
            
            configs[strategy_name] = config
        
        return configs
    
    def update_strategy_performance(self, strategy_name: str, performance_data: Dict):
        """Update performance data for a strategy"""
        
        if strategy_name not in self.strategy_performance:
            self.strategy_performance[strategy_name] = {}
            
        self.strategy_performance[strategy_name].update({
            'total_return': performance_data.get('total_return', 0.0),
            'win_rate': performance_data.get('win_rate', 0.0),
            'sharpe_ratio': performance_data.get('sharpe_ratio', 0.0),
            'max_drawdown': performance_data.get('max_drawdown', 0.0),
            'trades_count': performance_data.get('trades_count', 0),
            'last_updated': datetime.now()
        })
    
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary"""
        
        total_value = sum([
            self.total_capital * (allocation.allocation_pct / 100) 
            for allocation in self.strategies.values() 
            if allocation.active
        ])
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_capital': self.total_capital,
            'allocated_capital': total_value,
            'current_market_regime': self.current_market_condition.regime.value if self.current_market_condition else 'unknown',
            'market_confidence': self.current_market_condition.confidence if self.current_market_condition else 0.0,
            'active_strategies': len([s for s in self.strategies.values() if s.active]),
            'strategies': {
                name: {
                    'allocation_pct': allocation.allocation_pct,
                    'capital_allocated': self.total_capital * (allocation.allocation_pct / 100),
                    'active': allocation.active,
                    'performance': self.strategy_performance.get(name, {})
                }
                for name, allocation in self.strategies.items()
            },
            'last_rebalance': self.last_rebalance.isoformat() if self.last_rebalance else None
        }
        
        return summary