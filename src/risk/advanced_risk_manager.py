"""
Advanced Risk Management System
Implements professional-grade risk management with:
1. Portfolio heat tracking (max 6% total account risk)
2. Dynamic position sizing based on setup quality
3. Correlation limits between positions
4. ATR-based volatility adjustments
5. Drawdown protection and circuit breakers
"""

import numpy as np
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class TradeRisk:
    """Individual trade risk assessment"""
    pair: str
    side: str  # 'long' or 'short'
    entry_price: float
    stop_price: float
    position_size: float
    risk_amount: float
    risk_percent: float
    confidence_level: float  # 0.0 to 1.0
    setup_quality: float     # 0.0 to 1.0
    atr_multiple: float
    correlation_score: float # With existing positions

@dataclass
class PortfolioRisk:
    """Overall portfolio risk metrics"""
    total_risk_percent: float
    total_risk_amount: float
    individual_risks: List[TradeRisk]
    max_correlated_risk: float
    current_drawdown: float
    consecutive_losses: int
    risk_adjusted_score: float
    heat_level: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'

class AdvancedRiskManager:
    """
    Professional risk management system
    
    Features:
    - Portfolio heat management (max 6% total risk)
    - Dynamic position sizing based on setup quality
    - Correlation analysis between positions
    - Volatility-adjusted stops and sizing
    - Drawdown protection and loss limits
    - Performance-based risk adjustments
    """
    
    def __init__(self,
                 max_portfolio_risk: float = 0.06,  # 6% max total risk
                 max_single_trade_risk: float = 0.025,  # 2.5% per trade
                 max_correlated_risk: float = 0.04,  # 4% in correlated trades
                 daily_loss_limit: float = 0.02,   # 2% daily loss limit
                 weekly_loss_limit: float = 0.08,  # 8% weekly loss limit
                 min_rratio: float = 2.0):          # Minimum 1:2 R:R
        
        self.max_portfolio_risk = max_portfolio_risk
        self.max_single_trade_risk = max_single_trade_risk
        self.max_correlated_risk = max_correlated_risk
        self.daily_loss_limit = daily_loss_limit
        self.weekly_loss_limit = weekly_loss_limit
        self.min_rratio = min_rratio
        
        # Track positions and performance
        self.active_positions: Dict[str, TradeRisk] = {}
        self.closed_trades: List[Dict[str, Any]] = []
        self.daily_pnl: List[Dict[str, float]] = []
        self.peak_balance = 0.0
        
        # Risk state tracking
        self.consecutive_losses = 0
        self.current_drawdown = 0.0
        self.last_risk_assessment = None
        
        # Correlation matrix for major crypto pairs
        self.correlation_matrix = self._initialize_correlation_matrix()
        
        logger.info("Advanced Risk Manager initialized")
        logger.info(f"Max Portfolio Risk: {self.max_portfolio_risk:.1%}")
        logger.info(f"Max Single Trade Risk: {self.max_single_trade_risk:.1%}")
    
    def evaluate_trade_proposal(self,
                               pair: str,
                               side: str,
                               entry_price: float,
                               stop_price: float,
                               confidence_level: float,
                               setup_quality: float,
                               account_balance: float,
                               current_volatility: float = 0.03) -> Dict[str, Any]:
        """
        Evaluate a proposed trade and return position sizing recommendation
        
        Returns:
            Dict containing position size, risk assessment, and approval status
        """
        
        try:
            # Calculate basic trade metrics
            stop_distance = abs(entry_price - stop_price) / entry_price
            
            # Estimate reward potential (simplified)
            reward_distance = stop_distance * self.min_rratio
            target_price = entry_price * (1 + reward_distance if side == 'long' else 1 - reward_distance)
            
            # Calculate dynamic position size
            position_size = self._calculate_optimal_position_size(
                account_balance=account_balance,
                entry_price=entry_price,
                stop_price=stop_price,
                confidence_level=confidence_level,
                setup_quality=setup_quality,
                current_volatility=current_volatility
            )
            
            # Create trade risk object
            risk_amount = position_size * stop_distance
            trade_risk = TradeRisk(
                pair=pair,
                side=side,
                entry_price=entry_price,
                stop_price=stop_price,
                position_size=position_size,
                risk_amount=risk_amount,
                risk_percent=risk_amount / account_balance,
                confidence_level=confidence_level,
                setup_quality=setup_quality,
                atr_multiple=stop_distance / current_volatility if current_volatility > 0 else 2.0,
                correlation_score=self._calculate_correlation_risk(pair, side)
            )
            
            # Assess portfolio impact
            portfolio_assessment = self._assess_portfolio_impact(trade_risk, account_balance)
            
            # Determine approval
            approval_decision = self._make_approval_decision(trade_risk, portfolio_assessment)
            
            return {
                'approved': approval_decision['approved'],
                'position_size': position_size,
                'risk_amount': risk_amount,
                'risk_percent': trade_risk.risk_percent,
                'target_price': target_price,
                'expected_rr': reward_distance / stop_distance,
                'portfolio_risk_after': portfolio_assessment.total_risk_percent,
                'heat_level': portfolio_assessment.heat_level,
                'rejection_reason': approval_decision.get('reason'),
                'risk_adjustments': approval_decision.get('adjustments', {}),
                'trade_risk': trade_risk
            }
            
        except Exception as e:
            logger.error(f"Error evaluating trade proposal: {e}")
            return {
                'approved': False,
                'rejection_reason': f'Risk evaluation error: {e}',
                'position_size': 0,
                'risk_amount': 0,
                'risk_percent': 0
            }
    
    def _calculate_optimal_position_size(self,
                                       account_balance: float,
                                       entry_price: float,
                                       stop_price: float,
                                       confidence_level: float,
                                       setup_quality: float,
                                       current_volatility: float) -> float:
        """Calculate optimal position size based on multiple factors"""
        
        # Base risk per trade
        base_risk = self.max_single_trade_risk
        
        # Adjust based on confidence level (0.5x to 1.5x)
        confidence_multiplier = 0.5 + confidence_level
        
        # Adjust based on setup quality (0.7x to 1.3x)
        quality_multiplier = 0.7 + (setup_quality * 0.6)
        
        # Adjust based on current portfolio risk
        current_portfolio_risk = self._calculate_current_portfolio_risk(account_balance)
        portfolio_multiplier = max(0.3, 1 - (current_portfolio_risk / self.max_portfolio_risk))
        
        # Adjust based on volatility (reduce size in high volatility)
        vol_adjustment = min(1.0, 0.03 / max(current_volatility, 0.01))
        
        # Adjust based on recent performance
        performance_multiplier = self._get_performance_multiplier()
        
        # Calculate final risk per trade
        final_risk = base_risk * confidence_multiplier * quality_multiplier * portfolio_multiplier * vol_adjustment * performance_multiplier
        
        # Ensure within bounds
        final_risk = np.clip(final_risk, 0.005, self.max_single_trade_risk)
        
        # Convert to position size
        risk_amount = account_balance * final_risk
        stop_distance = abs(entry_price - stop_price)
        position_size = risk_amount / stop_distance if stop_distance > 0 else 0
        
        return position_size
    
    def _calculate_correlation_risk(self, pair: str, side: str) -> float:
        """Calculate correlation risk with existing positions"""
        
        if not self.active_positions:
            return 0.0
        
        base_asset = pair.split('/')[0]
        correlation_risk = 0.0
        
        for position in self.active_positions.values():
            position_base = position.pair.split('/')[0]
            
            # Check correlation
            correlation = self._get_pair_correlation(base_asset, position_base)
            
            # Same direction positions increase correlation risk
            direction_multiplier = 1.0 if position.side == side else -0.5
            
            correlation_risk += abs(correlation * direction_multiplier * position.risk_percent)
        
        return correlation_risk
    
    def _assess_portfolio_impact(self, trade_risk: TradeRisk, account_balance: float) -> PortfolioRisk:
        """Assess impact of adding this trade to current portfolio"""
        
        # Calculate portfolio risk including this trade
        total_risk = self._calculate_current_portfolio_risk(account_balance) + trade_risk.risk_percent
        
        # Calculate correlated risk
        correlated_risk = trade_risk.correlation_score + trade_risk.risk_percent
        
        # Determine heat level
        if total_risk > self.max_portfolio_risk:
            heat_level = 'CRITICAL'
        elif total_risk > self.max_portfolio_risk * 0.8:
            heat_level = 'HIGH'
        elif total_risk > self.max_portfolio_risk * 0.6:
            heat_level = 'MEDIUM'
        else:
            heat_level = 'LOW'
        
        # Risk-adjusted score
        risk_score = min(1.0, total_risk / self.max_portfolio_risk)
        quality_score = trade_risk.setup_quality
        confidence_score = trade_risk.confidence_level
        
        risk_adjusted_score = (quality_score * 0.4 + confidence_score * 0.3 + (1 - risk_score) * 0.3)
        
        return PortfolioRisk(
            total_risk_percent=total_risk,
            total_risk_amount=total_risk * account_balance,
            individual_risks=list(self.active_positions.values()) + [trade_risk],
            max_correlated_risk=correlated_risk,
            current_drawdown=self.current_drawdown,
            consecutive_losses=self.consecutive_losses,
            risk_adjusted_score=risk_adjusted_score,
            heat_level=heat_level
        )
    
    def _make_approval_decision(self, trade_risk: TradeRisk, portfolio_risk: PortfolioRisk) -> Dict[str, Any]:
        """Make final approval decision for the trade"""
        
        # Check hard limits
        if portfolio_risk.total_risk_percent > self.max_portfolio_risk:
            return {
                'approved': False,
                'reason': f'Portfolio risk limit exceeded: {portfolio_risk.total_risk_percent:.1%} > {self.max_portfolio_risk:.1%}'
            }
        
        if trade_risk.risk_percent > self.max_single_trade_risk:
            return {
                'approved': False,
                'reason': f'Single trade risk too high: {trade_risk.risk_percent:.1%} > {self.max_single_trade_risk:.1%}'
            }
        
        if portfolio_risk.max_correlated_risk > self.max_correlated_risk:
            return {
                'approved': False,
                'reason': f'Correlation risk too high: {portfolio_risk.max_correlated_risk:.1%} > {self.max_correlated_risk:.1%}'
            }
        
        # Check drawdown limits
        if self.current_drawdown > self.daily_loss_limit:
            return {
                'approved': False,
                'reason': f'Daily loss limit reached: {self.current_drawdown:.1%}'
            }
        
        # Check consecutive losses
        if self.consecutive_losses >= 5:
            return {
                'approved': False,
                'reason': f'Too many consecutive losses: {self.consecutive_losses}'
            }
        
        # Quality checks
        if trade_risk.setup_quality < 0.3:
            return {
                'approved': False,
                'reason': f'Setup quality too low: {trade_risk.setup_quality:.1%}'
            }
        
        if trade_risk.confidence_level < 0.4:
            return {
                'approved': False,
                'reason': f'Confidence level too low: {trade_risk.confidence_level:.1%}'
            }
        
        # Adjust position size if needed
        adjustments = {}
        
        if portfolio_risk.heat_level == 'HIGH':
            adjustments['size_reduction'] = 0.8
            adjustments['reason'] = 'Reduced size due to high portfolio heat'
        
        if trade_risk.correlation_score > 0.02:  # 2% correlation risk
            adjustments['correlation_warning'] = True
            adjustments['reason'] = 'High correlation with existing positions'
        
        return {
            'approved': True,
            'adjustments': adjustments,
            'portfolio_score': portfolio_risk.risk_adjusted_score
        }
    
    def update_position(self, pair: str, trade_risk: TradeRisk):
        """Add new position to tracking"""
        self.active_positions[pair] = trade_risk
        logger.info(f"Added position: {pair} {trade_risk.side} - Risk: {trade_risk.risk_percent:.2%}")
    
    def close_position(self, pair: str, exit_price: float, pnl: float, account_balance: float):
        """Remove position and update performance tracking"""
        
        if pair not in self.active_positions:
            logger.warning(f"Attempted to close non-existent position: {pair}")
            return
        
        trade_risk = self.active_positions.pop(pair)
        
        # Record closed trade
        trade_result = {
            'pair': pair,
            'side': trade_risk.side,
            'entry_price': trade_risk.entry_price,
            'exit_price': exit_price,
            'position_size': trade_risk.position_size,
            'pnl': pnl,
            'pnl_percent': pnl / account_balance,
            'risk_taken': trade_risk.risk_percent,
            'r_multiple': pnl / trade_risk.risk_amount if trade_risk.risk_amount > 0 else 0,
            'setup_quality': trade_risk.setup_quality,
            'confidence_level': trade_risk.confidence_level,
            'timestamp': datetime.now()
        }
        
        self.closed_trades.append(trade_result)
        
        # Update performance metrics
        self._update_performance_metrics(trade_result, account_balance)
        
        logger.info(f"Closed position: {pair} - PnL: ${pnl:.2f} ({trade_result['r_multiple']:.2f}R)")
    
    def _update_performance_metrics(self, trade_result: Dict[str, Any], account_balance: float):
        """Update performance tracking metrics"""
        
        pnl = trade_result['pnl']
        
        # Track consecutive losses
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        # Update peak balance and drawdown
        if account_balance > self.peak_balance:
            self.peak_balance = account_balance
            self.current_drawdown = 0.0
        else:
            self.current_drawdown = (self.peak_balance - account_balance) / self.peak_balance
        
        # Add to daily PnL tracking
        today = datetime.now().date()
        daily_record = next(
            (record for record in self.daily_pnl if record['date'] == today),
            None
        )
        
        if daily_record:
            daily_record['pnl'] += pnl
            daily_record['trades'] += 1
        else:
            self.daily_pnl.append({
                'date': today,
                'pnl': pnl,
                'trades': 1,
                'balance': account_balance
            })
        
        # Keep only last 30 days
        cutoff_date = datetime.now().date() - timedelta(days=30)
        self.daily_pnl = [record for record in self.daily_pnl if record['date'] >= cutoff_date]
    
    def _get_performance_multiplier(self) -> float:
        """Get performance-based risk multiplier"""
        
        if len(self.closed_trades) < 5:
            return 1.0  # Neutral for insufficient data
        
        # Recent performance (last 10 trades)
        recent_trades = self.closed_trades[-10:]
        recent_r_multiples = [trade['r_multiple'] for trade in recent_trades]
        avg_r_multiple = np.mean(recent_r_multiples)
        
        # Win rate
        winners = sum(1 for r in recent_r_multiples if r > 0)
        win_rate = winners / len(recent_r_multiples)
        
        # Performance score
        performance_score = avg_r_multiple * 0.6 + (win_rate - 0.5) * 0.4
        
        # Convert to multiplier (0.7x to 1.3x)
        multiplier = 1.0 + np.clip(performance_score, -0.3, 0.3)
        
        # Reduce risk after losses
        if self.consecutive_losses >= 3:
            multiplier *= 0.7
        elif self.consecutive_losses >= 2:
            multiplier *= 0.85
        
        return multiplier
    
    def _calculate_current_portfolio_risk(self, account_balance: float) -> float:
        """Calculate current total portfolio risk"""
        return sum(position.risk_percent for position in self.active_positions.values())
    
    def _get_pair_correlation(self, asset1: str, asset2: str) -> float:
        """Get correlation between two assets"""
        
        if asset1 == asset2:
            return 1.0
        
        # Check correlation matrix
        key1 = f"{asset1}_{asset2}"
        key2 = f"{asset2}_{asset1}"
        
        if key1 in self.correlation_matrix:
            return self.correlation_matrix[key1]
        elif key2 in self.correlation_matrix:
            return self.correlation_matrix[key2]
        
        # Default correlation for unknown pairs
        if asset1 in ['BTC', 'ETH'] and asset2 in ['BTC', 'ETH']:
            return 0.7  # High correlation between major cryptos
        elif 'BTC' in [asset1, asset2] or 'ETH' in [asset1, asset2]:
            return 0.5  # Moderate correlation with major cryptos
        else:
            return 0.4  # Default altcoin correlation
    
    def _initialize_correlation_matrix(self) -> Dict[str, float]:
        """Initialize correlation matrix for major crypto pairs"""
        return {
            'BTC_ETH': 0.75,
            'BTC_BNB': 0.65,
            'BTC_SOL': 0.70,
            'BTC_ADA': 0.60,
            'BTC_AVAX': 0.68,
            'BTC_DOT': 0.62,
            'BTC_LINK': 0.58,
            'BTC_UNI': 0.64,
            'BTC_MATIC': 0.66,
            'BTC_LTC': 0.72,
            'ETH_BNB': 0.60,
            'ETH_SOL': 0.68,
            'ETH_ADA': 0.55,
            'ETH_AVAX': 0.70,
            'ETH_DOT': 0.58,
            'ETH_LINK': 0.62,
            'ETH_UNI': 0.72,
            'ETH_MATIC': 0.68,
            'SOL_AVAX': 0.65,
            'SOL_ADA': 0.52,
            'ADA_DOT': 0.58,
            'LINK_UNI': 0.55,
            # Add more correlations as needed
        }
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio risk summary"""
        
        if not self.active_positions:
            return {
                'status': 'No active positions',
                'total_risk': 0.0,
                'heat_level': 'LOW'
            }
        
        total_risk = sum(pos.risk_percent for pos in self.active_positions.values())
        
        return {
            'active_positions': len(self.active_positions),
            'total_risk_percent': f"{total_risk:.2%}",
            'max_allowed_risk': f"{self.max_portfolio_risk:.2%}",
            'risk_utilization': f"{total_risk/self.max_portfolio_risk:.1%}",
            'current_drawdown': f"{self.current_drawdown:.2%}",
            'consecutive_losses': self.consecutive_losses,
            'recent_performance': self._get_recent_performance_summary(),
            'heat_level': self._get_heat_level(total_risk),
            'positions': [
                {
                    'pair': pos.pair,
                    'side': pos.side,
                    'risk_percent': f"{pos.risk_percent:.2%}",
                    'confidence': f"{pos.confidence_level:.1%}",
                    'setup_quality': f"{pos.setup_quality:.1%}"
                }
                for pos in self.active_positions.values()
            ]
        }
    
    def _get_heat_level(self, total_risk: float) -> str:
        """Determine portfolio heat level"""
        if total_risk > self.max_portfolio_risk:
            return 'CRITICAL'
        elif total_risk > self.max_portfolio_risk * 0.8:
            return 'HIGH'
        elif total_risk > self.max_portfolio_risk * 0.6:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _get_recent_performance_summary(self) -> Dict[str, Any]:
        """Get summary of recent trading performance"""
        
        if len(self.closed_trades) < 3:
            return {'status': 'Insufficient trade history'}
        
        recent_trades = self.closed_trades[-10:]  # Last 10 trades
        
        win_count = sum(1 for trade in recent_trades if trade['pnl'] > 0)
        win_rate = win_count / len(recent_trades)
        
        r_multiples = [trade['r_multiple'] for trade in recent_trades]
        avg_r_multiple = np.mean(r_multiples)
        
        total_pnl = sum(trade['pnl'] for trade in recent_trades)
        
        return {
            'total_trades': len(recent_trades),
            'win_rate': f"{win_rate:.1%}",
            'avg_r_multiple': f"{avg_r_multiple:.2f}R",
            'total_pnl': f"${total_pnl:.2f}",
            'best_trade': f"{max(r_multiples):.2f}R",
            'worst_trade': f"{min(r_multiples):.2f}R"
        }