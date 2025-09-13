#!/usr/bin/env python3
"""
Advanced Portfolio Hedging System
Optimized algorithms for portfolio protection and risk management
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime
from typing import Dict, List



class AdvancedHedgingSystem:
    """Sophisticated hedging system with multiple strategies"""

    def __init__(self):
        self.freqtrade_api = "http://127.0.0.1:8080/api/v1"
        self.auth = ("freqtrade", "freqtrade")
        self.vix_threshold = 25  # VIX level for crash protection
        self.correlation_threshold = 0.8  # Portfolio correlation limit
        self.drawdown_threshold = 0.05  # 5% drawdown trigger

    def analyze_portfolio_risk(self, active_trades: List[Dict]) -> Dict:
        """Comprehensive portfolio risk analysis"""

        if not active_trades:
            return {
                "risk_level": "none",
                "hedging_required": False,
                "recommendations": [],
            }

        # Calculate portfolio metrics
        total_exposure = sum([t.get("stake_amount", 0) for t in active_trades])
        total_profit = sum([t.get("profit_abs", 0) for t in active_trades])

        # Asset class analysis
        crypto_pairs = [t for t in active_trades if "USDT" in t.get("pair", "")]
        stock_pairs = [
            t
            for t in active_trades
            if t.get("pair", "").split("/")[1] in ["USD", "EUR"]
        ]

        crypto_exposure = sum([t.get("stake_amount", 0) for t in crypto_pairs])
        stock_exposure = sum([t.get("stake_amount", 0) for t in stock_pairs])

        # Risk calculations
        correlation_risk = crypto_exposure / total_exposure if total_exposure > 0 else 0
        drawdown_risk = total_profit / total_exposure if total_exposure > 0 else 0
        concentration_risk = self._calculate_concentration_risk(active_trades)

        # Overall risk assessment
        risk_factors = {
            "correlation": correlation_risk > self.correlation_threshold,
            "drawdown": drawdown_risk < -self.drawdown_threshold,
            "concentration": concentration_risk > 0.4,
            "position_count": len(active_trades) > 5,
        }

        risk_score = sum(risk_factors.values()) / len(risk_factors)

        if risk_score >= 0.75:
            risk_level = "critical"
        elif risk_score >= 0.5:
            risk_level = "high"
        elif risk_score >= 0.25:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "correlation_risk": correlation_risk,
            "drawdown_risk": drawdown_risk,
            "concentration_risk": concentration_risk,
            "total_exposure": total_exposure,
            "crypto_exposure": crypto_exposure,
            "stock_exposure": stock_exposure,
            "hedging_required": risk_score >= 0.5,
            "risk_factors": risk_factors,
        }

    def _calculate_concentration_risk(self, active_trades: List[Dict]) -> float:
        """Calculate portfolio concentration risk"""

        if not active_trades:
            return 0.0

        # Calculate position sizes
        position_sizes = [t.get("stake_amount", 0) for t in active_trades]
        total_size = sum(position_sizes)

        if total_size == 0:
            return 0.0

        # Calculate Herfindahl-Hirschman Index (HHI) for concentration
        weights = [size / total_size for size in position_sizes]
        hhi = sum([w**2 for w in weights])

        # Normalize to 0-1 scale (1 = maximum concentration)
        max_hhi = 1.0  # All money in one position
        min_hhi = 1.0 / len(active_trades)  # Equally distributed

        normalized_concentration = (
            (hhi - min_hhi) / (max_hhi - min_hhi) if max_hhi > min_hhi else 0
        )

        return max(0, min(1, normalized_concentration))

    def generate_hedge_recommendations(
        self, portfolio_risk: Dict, active_trades: List[Dict]
    ) -> List[Dict]:
        """Generate optimized hedge recommendations based on portfolio analysis"""

        recommendations = []

        if not portfolio_risk["hedging_required"]:
            return recommendations

        # 1. Correlation Hedge
        if portfolio_risk["correlation_risk"] > self.correlation_threshold:
            hedge_size = portfolio_risk["crypto_exposure"] * 0.15  # 15% hedge ratio

            recommendations.append(
                {
                    "type": "correlation_hedge",
                    "priority": (
                        "high" if portfolio_risk["correlation_risk"] > 0.9 else "medium"
                    ),
                    "instrument": "inverse_crypto_etf",
                    "action": "Buy inverse crypto ETF or VIX calls",
                    "size_usd": hedge_size,
                    "hedge_ratio": 0.15,
                    "expected_correlation": -0.8,
                    "reason": f'High crypto correlation ({portfolio_risk["correlation_risk"]:.1%})',
                    "implementation": {
                        "method": "etf_purchase",
                        "symbols": ["BITI", "SQQQ"],  # Inverse crypto/tech ETFs
                        "allocation": hedge_size,
                        "rebalance_frequency": "weekly",
                    },
                }
            )

        # 2. Drawdown Protection
        if portfolio_risk["drawdown_risk"] < -self.drawdown_threshold:
            protection_size = portfolio_risk["total_exposure"] * 0.1  # 10% protection

            recommendations.append(
                {
                    "type": "drawdown_protection",
                    "priority": "critical",
                    "instrument": "protective_puts",
                    "action": "Buy protective puts on major positions",
                    "size_usd": protection_size,
                    "hedge_ratio": 0.1,
                    "expected_protection": 0.8,  # 80% downside protection
                    "reason": f'Portfolio drawdown at {portfolio_risk["drawdown_risk"]:.1%}',
                    "implementation": {
                        "method": "options_purchase",
                        "strategy": "protective_puts",
                        "strike_selection": "5% OTM",
                        "expiration": "30-45 days",
                        "allocation": protection_size,
                    },
                }
            )

        # 3. Volatility Hedge
        if len(active_trades) >= 3:
            vol_hedge_size = (
                portfolio_risk["total_exposure"] * 0.05
            )  # 5% volatility hedge

            recommendations.append(
                {
                    "type": "volatility_hedge",
                    "priority": "medium",
                    "instrument": "vix_calls",
                    "action": "Buy VIX calls for crash protection",
                    "size_usd": vol_hedge_size,
                    "hedge_ratio": 0.05,
                    "expected_spike_protection": 2.0,  # 2x return during volatility spikes
                    "reason": "Multiple positions exposed to systematic risk",
                    "implementation": {
                        "method": "options_purchase",
                        "strategy": "long_vix_calls",
                        "strike_selection": "20% OTM",
                        "expiration": "60-90 days",
                        "allocation": vol_hedge_size,
                    },
                }
            )

        # 4. Concentration Hedge
        if portfolio_risk["concentration_risk"] > 0.4:
            # Find the largest position for hedging
            largest_position = max(
                active_trades, key=lambda x: x.get("stake_amount", 0)
            )
            hedge_size = (
                largest_position.get("stake_amount", 0) * 0.2
            )  # 20% of largest position

            recommendations.append(
                {
                    "type": "concentration_hedge",
                    "priority": "medium",
                    "instrument": "pair_hedge",
                    "action": f'Hedge largest position ({largest_position.get("pair", "Unknown")})',
                    "size_usd": hedge_size,
                    "hedge_ratio": 0.2,
                    "target_pair": largest_position.get("pair", "Unknown"),
                    "reason": f'High concentration risk ({portfolio_risk["concentration_risk"]:.1%})',
                    "implementation": {
                        "method": "short_position",
                        "target": largest_position.get("pair", "Unknown"),
                        "size": hedge_size,
                        "hedge_effectiveness": 0.9,
                    },
                }
            )

        # 5. Sector Rotation Hedge
        if portfolio_risk["crypto_exposure"] > portfolio_risk["total_exposure"] * 0.6:
            rotation_size = portfolio_risk["crypto_exposure"] * 0.1  # 10% rotation

            recommendations.append(
                {
                    "type": "sector_rotation",
                    "priority": "low",
                    "instrument": "alternative_assets",
                    "action": "Rotate into uncorrelated assets (commodities, bonds)",
                    "size_usd": rotation_size,
                    "hedge_ratio": 0.1,
                    "target_correlation": 0.2,  # Low correlation target
                    "reason": "Over-concentration in crypto sector",
                    "implementation": {
                        "method": "asset_rotation",
                        "targets": ["GLD", "TLT", "DBA"],  # Gold, Bonds, Commodities
                        "allocation": rotation_size / 3,  # Split equally
                        "rebalance_trigger": "monthly",
                    },
                }
            )

        return recommendations

    def calculate_hedge_effectiveness(
        self, hedge_type: str, portfolio_risk: Dict
    ) -> Dict:
        """Calculate expected effectiveness of different hedge strategies"""

        effectiveness_models = {
            "correlation_hedge": {
                "risk_reduction": min(0.8, portfolio_risk["correlation_risk"] * 0.9),
                "cost_estimate": 0.02,  # 2% of hedged amount annually
                "success_probability": 0.85,
                "max_loss_reduction": 0.6,
            },
            "drawdown_protection": {
                "risk_reduction": 0.8,  # 80% downside protection
                "cost_estimate": 0.03,  # 3% of hedged amount
                "success_probability": 0.9,
                "max_loss_reduction": 0.8,
            },
            "volatility_hedge": {
                "risk_reduction": 0.4,  # Moderate risk reduction
                "cost_estimate": 0.015,  # 1.5% cost
                "success_probability": 0.7,  # Lower probability but high payoff
                "max_loss_reduction": 0.3,
            },
            "concentration_hedge": {
                "risk_reduction": portfolio_risk["concentration_risk"] * 0.8,
                "cost_estimate": 0.01,  # 1% cost
                "success_probability": 0.9,
                "max_loss_reduction": 0.5,
            },
        }

        return effectiveness_models.get(
            hedge_type,
            {
                "risk_reduction": 0.3,
                "cost_estimate": 0.02,
                "success_probability": 0.7,
                "max_loss_reduction": 0.4,
            },
        )

    def optimize_hedge_portfolio(
        self, recommendations: List[Dict], budget_limit: float
    ) -> List[Dict]:
        """Optimize hedge portfolio for maximum risk reduction within budget"""

        if not recommendations or budget_limit <= 0:
            return []

        # Calculate risk-adjusted return for each hedge
        optimized_hedges = []
        remaining_budget = budget_limit

        # Sort by priority and effectiveness
        priority_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}

        for hedge in recommendations:
            priority_score = priority_weights.get(hedge["priority"], 1)
            effectiveness = self.calculate_hedge_effectiveness(hedge["type"], {})

            # Calculate efficiency score (risk reduction per dollar)
            cost = hedge["size_usd"] * effectiveness["cost_estimate"]
            efficiency = (effectiveness["risk_reduction"] * priority_score) / max(
                cost, 1
            )

            hedge["efficiency_score"] = efficiency
            hedge["estimated_cost"] = cost
            hedge["expected_risk_reduction"] = effectiveness["risk_reduction"]

        # Sort by efficiency score
        sorted_hedges = sorted(
            recommendations, key=lambda x: x["efficiency_score"], reverse=True
        )

        # Select hedges within budget
        for hedge in sorted_hedges:
            if hedge["estimated_cost"] <= remaining_budget:
                optimized_hedges.append(hedge)
                remaining_budget -= hedge["estimated_cost"]

        return optimized_hedges

    def create_hedge_execution_plan(self, optimized_hedges: List[Dict]) -> Dict:
        """Create detailed execution plan for hedge implementation"""

        execution_plan = {
            "timestamp": datetime.now().isoformat(),
            "total_hedges": len(optimized_hedges),
            "total_cost": sum([h["estimated_cost"] for h in optimized_hedges]),
            "expected_risk_reduction": (
                sum([h["expected_risk_reduction"] for h in optimized_hedges])
                / len(optimized_hedges)
                if optimized_hedges
                else 0
            ),
            "execution_phases": [],
        }

        # Group hedges by urgency
        critical_hedges = [h for h in optimized_hedges if h["priority"] == "critical"]
        high_hedges = [h for h in optimized_hedges if h["priority"] == "high"]
        medium_hedges = [h for h in optimized_hedges if h["priority"] == "medium"]
        low_hedges = [h for h in optimized_hedges if h["priority"] == "low"]

        # Phase 1: Critical hedges (immediate)
        if critical_hedges:
            execution_plan["execution_phases"].append(
                {
                    "phase": 1,
                    "urgency": "immediate",
                    "timeframe": "within 1 hour",
                    "hedges": critical_hedges,
                    "total_cost": sum([h["estimated_cost"] for h in critical_hedges]),
                }
            )

        # Phase 2: High priority hedges (same day)
        if high_hedges:
            execution_plan["execution_phases"].append(
                {
                    "phase": 2,
                    "urgency": "high",
                    "timeframe": "within 24 hours",
                    "hedges": high_hedges,
                    "total_cost": sum([h["estimated_cost"] for h in high_hedges]),
                }
            )

        # Phase 3: Medium priority hedges (within week)
        if medium_hedges:
            execution_plan["execution_phases"].append(
                {
                    "phase": 3,
                    "urgency": "medium",
                    "timeframe": "within 1 week",
                    "hedges": medium_hedges,
                    "total_cost": sum([h["estimated_cost"] for h in medium_hedges]),
                }
            )

        # Phase 4: Low priority hedges (within month)
        if low_hedges:
            execution_plan["execution_phases"].append(
                {
                    "phase": 4,
                    "urgency": "low",
                    "timeframe": "within 1 month",
                    "hedges": low_hedges,
                    "total_cost": sum([h["estimated_cost"] for h in low_hedges]),
                }
            )

        return execution_plan


def main():
    """Test the advanced hedging system"""
    hedging_system = AdvancedHedgingSystem()

    print("🛡️ Advanced Portfolio Hedging System")
    print("=" * 50)

    # Simulate portfolio with high correlation risk
    mock_trades = [
        {"pair": "BTC/USDT", "stake_amount": 1000, "profit_abs": -50},
        {"pair": "ETH/USDT", "stake_amount": 800, "profit_abs": -30},
        {"pair": "ADA/USDT", "stake_amount": 600, "profit_abs": -20},
        {"pair": "DOT/USDT", "stake_amount": 400, "profit_abs": 10},
    ]

    # Analyze portfolio risk
    risk_analysis = hedging_system.analyze_portfolio_risk(mock_trades)
    print("📊 Portfolio Risk Analysis:")
    print(f"   Risk Level: {risk_analysis['risk_level'].upper()}")
    print(f"   Risk Score: {risk_analysis['risk_score']:.2f}")
    print(f"   Correlation Risk: {risk_analysis['correlation_risk']:.1%}")
    print(f"   Drawdown Risk: {risk_analysis['drawdown_risk']:.1%}")
    print(f"   Hedging Required: {risk_analysis['hedging_required']}")

    # Generate hedge recommendations
    recommendations = hedging_system.generate_hedge_recommendations(
        risk_analysis, mock_trades
    )
    print(f"\n🎯 Hedge Recommendations: {len(recommendations)}")

    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec['type'].title()}: {rec['action']}")
        print(
            f"      Priority: {rec['priority'].upper()}, Size: ${rec['size_usd']:.0f}"
        )

    # Optimize hedge portfolio
    budget = 500  # $500 hedge budget
    optimized = hedging_system.optimize_hedge_portfolio(recommendations, budget)
    print(f"\n💰 Optimized Hedges (Budget: ${budget}):")

    for hedge in optimized:
        print(
            f"   • {hedge['type']}: ${hedge['estimated_cost']:.0f} cost, {hedge['expected_risk_reduction']:.1%} risk reduction"
        )

    # Create execution plan
    execution_plan = hedging_system.create_hedge_execution_plan(optimized)
    print("\n📋 Execution Plan:")
    print(f"   Total Cost: ${execution_plan['total_cost']:.0f}")
    print(
        f"   Expected Risk Reduction: {execution_plan['expected_risk_reduction']:.1%}"
    )
    print(f"   Execution Phases: {len(execution_plan['execution_phases'])}")

    print("\n✅ Advanced hedging system operational!")
    return execution_plan


if __name__ == "__main__":
    main()
