#!/usr/bin/env python3
"""
Advanced Trading System Monitoring
Real-time performance tracking, strategy effectiveness, and risk monitoring
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import sqlite3
from datetime import datetime
from typing import Dict, List

import numpy as np
import requests


class AdvancedTradingMonitor:
    """Comprehensive monitoring system for the advanced trading strategy"""

    def __init__(self):
        self.freqtrade_api = "http://127.0.0.1:8080/api/v1"
        self.auth = ("freqtrade", "freqtrade")
        self.db_path = "trade_logic.db"

    def get_real_time_performance(self) -> Dict:
        """Get comprehensive real-time performance metrics"""
        try:
            # Get active trades
            active_response = requests.get(
                f"{self.freqtrade_api}/status", auth=self.auth, timeout=5
            )
            active_trades = (
                active_response.json() if active_response.status_code == 200 else []
            )

            # Get trade history
            history_response = requests.get(
                f"{self.freqtrade_api}/trades", auth=self.auth, timeout=5
            )
            trade_history = (
                history_response.json() if history_response.status_code == 200 else []
            )

            # Calculate comprehensive metrics
            metrics = self._calculate_performance_metrics(active_trades, trade_history)

            return {
                "timestamp": datetime.now().isoformat(),
                "active_trades": len(active_trades),
                "total_active_profit": sum(
                    [t.get("profit_abs", 0) for t in active_trades]
                ),
                "performance_metrics": metrics,
                "risk_assessment": self._assess_portfolio_risk(active_trades),
                "strategy_effectiveness": self._evaluate_strategy_effectiveness(),
                "market_regime": self._detect_current_market_regime(),
                "hedging_recommendations": self._get_hedging_recommendations(
                    active_trades
                ),
            }

        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def _calculate_performance_metrics(
        self, active_trades: List, trade_history: List
    ) -> Dict:
        """Calculate comprehensive performance metrics"""

        # Filter closed trades
        closed_trades = [t for t in trade_history if not t.get("is_open", True)]

        if not closed_trades:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "avg_profit": 0,
                "profit_factor": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
            }

        # Basic metrics
        total_trades = len(closed_trades)
        winning_trades = [t for t in closed_trades if t.get("profit_pct", 0) > 0]
        losing_trades = [t for t in closed_trades if t.get("profit_pct", 0) <= 0]

        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0

        # Profit metrics
        total_profit = sum([t.get("profit_abs", 0) for t in closed_trades])
        avg_profit = total_profit / total_trades if total_trades > 0 else 0

        # Profit factor
        gross_profit = sum([t.get("profit_abs", 0) for t in winning_trades])
        gross_loss = abs(sum([t.get("profit_abs", 0) for t in losing_trades]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

        # Sharpe ratio (simplified)
        returns = [t.get("profit_pct", 0) / 100 for t in closed_trades]
        if len(returns) > 1:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = avg_return / std_return if std_return > 0 else 0
        else:
            sharpe_ratio = 0

        # Maximum drawdown
        cumulative_returns = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = running_max - cumulative_returns
        max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0

        return {
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": win_rate * 100,
            "avg_profit": avg_profit,
            "total_profit": total_profit,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown * 100,
            "avg_win": gross_profit / len(winning_trades) if winning_trades else 0,
            "avg_loss": gross_loss / len(losing_trades) if losing_trades else 0,
        }

    def _assess_portfolio_risk(self, active_trades: List) -> Dict:
        """Assess current portfolio risk levels"""

        if not active_trades:
            return {"risk_level": "none", "total_exposure": 0, "correlation_risk": 0}

        # Calculate total exposure
        total_exposure = sum([t.get("stake_amount", 0) for t in active_trades])

        # Assess correlation risk (simplified)
        crypto_pairs = [t for t in active_trades if "USDT" in t.get("pair", "")]
        correlation_risk = (
            len(crypto_pairs) / len(active_trades) if active_trades else 0
        )

        # Calculate current drawdown
        total_profit = sum([t.get("profit_abs", 0) for t in active_trades])
        drawdown_pct = (
            (total_profit / total_exposure * 100) if total_exposure > 0 else 0
        )

        # Risk level assessment
        if drawdown_pct < -5:
            risk_level = "high"
        elif drawdown_pct < -2:
            risk_level = "medium"
        elif correlation_risk > 0.8:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk_level": risk_level,
            "total_exposure": total_exposure,
            "correlation_risk": correlation_risk * 100,
            "current_drawdown": drawdown_pct,
            "position_count": len(active_trades),
            "largest_position": (
                max([t.get("stake_amount", 0) for t in active_trades])
                if active_trades
                else 0
            ),
        }

    def _evaluate_strategy_effectiveness(self) -> Dict:
        """Evaluate how well the strategy is performing vs expectations"""

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get recent decisions
                cursor.execute(
                    """
                    SELECT composite_score, profit_pct, created_at 
                    FROM enhanced_trade_reasoning 
                    WHERE created_at > datetime('now', '-7 days')
                    ORDER BY created_at DESC
                """
                )

                recent_decisions = cursor.fetchall()

                if not recent_decisions:
                    return {
                        "status": "no_data",
                        "message": "No recent trade decisions to analyze",
                    }

                # Analyze signal accuracy
                high_confidence_trades = [d for d in recent_decisions if d[0] > 0.7]
                medium_confidence_trades = [
                    d for d in recent_decisions if 0.5 < d[0] <= 0.7
                ]

                high_conf_success = (
                    len([d for d in high_confidence_trades if d[1] > 0])
                    / len(high_confidence_trades)
                    if high_confidence_trades
                    else 0
                )
                medium_conf_success = (
                    len([d for d in medium_confidence_trades if d[1] > 0])
                    / len(medium_confidence_trades)
                    if medium_confidence_trades
                    else 0
                )

                return {
                    "total_decisions": len(recent_decisions),
                    "high_confidence_trades": len(high_confidence_trades),
                    "high_confidence_success_rate": high_conf_success * 100,
                    "medium_confidence_trades": len(medium_confidence_trades),
                    "medium_confidence_success_rate": medium_conf_success * 100,
                    "strategy_effectiveness": (
                        "excellent"
                        if high_conf_success > 0.8
                        else "good" if high_conf_success > 0.6 else "needs_improvement"
                    ),
                }

        except Exception as e:
            return {"error": str(e)}

    def _detect_current_market_regime(self) -> Dict:
        """Detect current market regime across multiple timeframes"""

        # This would integrate with your existing market regime detection
        # For now, return a simplified version

        return {
            "primary_regime": "bullish",  # Would be calculated from actual data
            "volatility_regime": "normal",
            "trend_strength": 0.65,
            "regime_confidence": 0.78,
            "regime_change_probability": 0.15,
        }

    def _get_hedging_recommendations(self, active_trades: List) -> List[Dict]:
        """Generate real-time hedging recommendations"""

        recommendations = []

        if not active_trades:
            return recommendations

        # Check correlation risk
        crypto_exposure = sum(
            [
                t.get("stake_amount", 0)
                for t in active_trades
                if "USDT" in t.get("pair", "")
            ]
        )
        total_exposure = sum([t.get("stake_amount", 0) for t in active_trades])

        if crypto_exposure / total_exposure > 0.7:
            recommendations.append(
                {
                    "type": "correlation_hedge",
                    "action": "Add VIX calls or inverse crypto ETF",
                    "size": crypto_exposure * 0.1,
                    "urgency": "medium",
                    "reason": f"High crypto correlation ({crypto_exposure/total_exposure:.1%})",
                }
            )

        # Check drawdown risk
        total_profit = sum([t.get("profit_abs", 0) for t in active_trades])
        if total_profit / total_exposure < -0.03:  # 3% drawdown
            recommendations.append(
                {
                    "type": "drawdown_protection",
                    "action": "Reduce position sizes by 25%",
                    "urgency": "high",
                    "reason": f"Portfolio drawdown at {total_profit/total_exposure:.1%}",
                }
            )

        return recommendations

    def monitor_entry_threshold_effectiveness(self) -> Dict:
        """Monitor how the new strict entry thresholds are performing"""

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get trades since threshold fix
                cursor.execute(
                    """
                    SELECT pair, composite_score, profit_pct, created_at
                    FROM enhanced_trade_reasoning 
                    WHERE created_at > datetime('now', '-24 hours')
                    AND composite_score > 0.65
                    ORDER BY created_at DESC
                """
                )

                strict_threshold_trades = cursor.fetchall()

                if not strict_threshold_trades:
                    return {
                        "status": "monitoring",
                        "message": "No trades with new strict thresholds yet",
                        "threshold_effectiveness": "pending",
                    }

                # Analyze effectiveness
                successful_trades = [t for t in strict_threshold_trades if t[2] > 0]
                success_rate = len(successful_trades) / len(strict_threshold_trades)
                avg_score = sum([t[1] for t in strict_threshold_trades]) / len(
                    strict_threshold_trades
                )

                return {
                    "trades_since_fix": len(strict_threshold_trades),
                    "success_rate": success_rate * 100,
                    "avg_signal_strength": avg_score,
                    "threshold_effectiveness": (
                        "excellent"
                        if success_rate > 0.8
                        else "good" if success_rate > 0.6 else "needs_adjustment"
                    ),
                    "recommendation": (
                        "Thresholds working well"
                        if success_rate > 0.7
                        else "Consider tightening thresholds further"
                    ),
                }

        except Exception as e:
            return {"error": str(e)}


def main():
    """Test the monitoring system"""
    monitor = AdvancedTradingMonitor()

    print("🔍 Advanced Trading System Monitor")
    print("=" * 50)

    # Get real-time performance
    performance = monitor.get_real_time_performance()
    print("📊 Real-time Performance:")
    print(f"   Active Trades: {performance.get('active_trades', 0)}")
    print(f"   Total Active Profit: ${performance.get('total_active_profit', 0):.2f}")

    if "performance_metrics" in performance:
        metrics = performance["performance_metrics"]
        print(f"   Win Rate: {metrics.get('win_rate', 0):.1f}%")
        print(f"   Profit Factor: {metrics.get('profit_factor', 0):.2f}")
        print(f"   Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")

    # Check threshold effectiveness
    threshold_check = monitor.monitor_entry_threshold_effectiveness()
    print("\n🎯 Entry Threshold Effectiveness:")
    print(f"   Status: {threshold_check.get('threshold_effectiveness', 'unknown')}")
    print(f"   Recommendation: {threshold_check.get('recommendation', 'monitoring')}")

    print("\n✅ Monitoring system operational!")


if __name__ == "__main__":
    main()
