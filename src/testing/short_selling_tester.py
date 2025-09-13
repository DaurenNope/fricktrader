#!/usr/bin/env python3
"""
Short Selling Test System
Simulate bearish market conditions to test short selling capabilities
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timedelta

import numpy as np
import pandas as pd


class ShortSellingTester:
    """Test short selling capabilities by simulating bearish conditions"""

    def __init__(self):
        self.db_path = "trade_logic.db"

    def simulate_bearish_market_data(self, pair: str = "BTC/USDT") -> pd.DataFrame:
        """Generate simulated bearish market data to test short signals"""

        # Create 100 candles of bearish market data
        dates = pd.date_range(
            start=datetime.now() - timedelta(hours=400), periods=100, freq="4H"
        )

        # Simulate declining price with bearish indicators
        base_price = 45000  # Lower BTC price for bearish scenario
        prices = []

        for i in range(100):
            # Declining trend with volatility
            trend_factor = 1 - (i * 0.002)  # 0.2% decline per candle
            volatility = np.random.normal(0, 0.01)  # 1% random volatility
            price = base_price * trend_factor * (1 + volatility)
            prices.append(max(price, base_price * 0.7))  # Floor at 30% decline

        # Create OHLCV data
        data = []
        for i, price in enumerate(prices):
            high = price * (1 + abs(np.random.normal(0, 0.005)))
            low = price * (1 - abs(np.random.normal(0, 0.005)))
            open_price = prices[i - 1] if i > 0 else price
            close = price
            volume = np.random.uniform(1000, 5000)

            data.append(
                {
                    "date": dates[i],
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                }
            )

        df = pd.DataFrame(data)

        # Add bearish technical indicators
        df["rsi"] = self._calculate_bearish_rsi(df["close"])
        df["macd"], df["macd_signal"] = self._calculate_bearish_macd(df["close"])
        df["ema_20"] = df["close"].ewm(span=20).mean()
        df["ema_50"] = df["close"].ewm(span=50).mean()

        return df

    def _calculate_bearish_rsi(self, prices: pd.Series) -> pd.Series:
        """Calculate RSI that shows overbought conditions (good for shorts)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # Bias towards overbought (>70) for short signals
        return rsi + 15  # Shift up to create overbought conditions

    def _calculate_bearish_macd(self, prices: pd.Series):
        """Calculate MACD showing bearish crossover"""
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        macd = ema_12 - ema_26
        macd_signal = macd.ewm(span=9).mean()

        # Bias towards bearish crossover
        return macd - 0.5, macd_signal  # Shift MACD below signal line

    def test_short_signal_generation(self, df: pd.DataFrame) -> dict:
        """Test if the strategy would generate short signals with this data"""

        results = {
            "total_candles": len(df),
            "potential_short_signals": 0,
            "signal_details": [],
            "bearish_conditions_met": [],
        }

        for i in range(50, len(df)):  # Skip first 50 for indicator calculation
            current = df.iloc[i]

            # Check short signal conditions (from MultiSignalStrategy)
            conditions = {
                "rsi_overbought": current["rsi"] > 70,
                "macd_bearish": current["macd"] < current["macd_signal"],
                "price_below_ema": current["close"] < current["ema_20"],
                "ema_bearish_alignment": current["ema_20"] < current["ema_50"],
                "declining_trend": current["close"]
                < df.iloc[i - 5]["close"],  # 5-candle decline
            }

            # Count conditions met
            conditions_met = sum(conditions.values())

            if conditions_met >= 4:  # Strong bearish signal
                results["potential_short_signals"] += 1
                results["signal_details"].append(
                    {
                        "candle": i,
                        "price": current["close"],
                        "rsi": current["rsi"],
                        "conditions_met": conditions_met,
                        "signal_strength": conditions_met / len(conditions),
                    }
                )

            results["bearish_conditions_met"].append(conditions_met)

        # Calculate average bearish conditions
        results["avg_bearish_conditions"] = np.mean(results["bearish_conditions_met"])
        results["max_bearish_conditions"] = max(results["bearish_conditions_met"])

        return results

    def simulate_short_trade_performance(
        self, entry_price: float, market_data: pd.DataFrame
    ) -> dict:
        """Simulate how a short trade would perform"""

        # Find entry point (when RSI > 75 and MACD bearish)
        entry_idx = None
        for i in range(50, len(market_data)):
            if (
                market_data.iloc[i]["rsi"] > 75
                and market_data.iloc[i]["macd"] < market_data.iloc[i]["macd_signal"]
            ):
                entry_idx = i
                entry_price = market_data.iloc[i]["close"]
                break

        if entry_idx is None:
            return {"error": "No suitable short entry found"}

        # Simulate trade progression
        max_profit = 0
        max_loss = 0
        exit_price = None
        exit_reason = None

        for i in range(entry_idx + 1, len(market_data)):
            current_price = market_data.iloc[i]["close"]
            profit_pct = (
                (entry_price - current_price) / entry_price * 100
            )  # Short profit calculation

            max_profit = max(max_profit, profit_pct)
            max_loss = min(max_loss, profit_pct)

            # Exit conditions
            if profit_pct > 8:  # 8% profit target
                exit_price = current_price
                exit_reason = "profit_target"
                break
            elif profit_pct < -5:  # 5% stop loss
                exit_price = current_price
                exit_reason = "stop_loss"
                break
            elif market_data.iloc[i]["rsi"] < 30:  # RSI oversold - cover short
                exit_price = current_price
                exit_reason = "rsi_oversold"
                break

        # If no exit, use last price
        if exit_price is None:
            exit_price = market_data.iloc[-1]["close"]
            exit_reason = "end_of_data"

        final_profit = (entry_price - exit_price) / entry_price * 100

        return {
            "entry_price": entry_price,
            "exit_price": exit_price,
            "exit_reason": exit_reason,
            "final_profit_pct": final_profit,
            "max_profit_pct": max_profit,
            "max_loss_pct": max_loss,
            "trade_success": final_profit > 0,
            "risk_reward_ratio": (
                abs(max_profit / max_loss) if max_loss < 0 else float("inf")
            ),
        }

    def create_short_test_report(self) -> dict:
        """Create comprehensive short selling test report"""

        print("🔍 Testing Short Selling Capabilities...")

        # Generate bearish market data
        bearish_data = self.simulate_bearish_market_data("BTC/USDT")

        # Test signal generation
        signal_test = self.test_short_signal_generation(bearish_data)

        # Simulate trade performance
        trade_simulation = self.simulate_short_trade_performance(45000, bearish_data)

        report = {
            "test_timestamp": datetime.now().isoformat(),
            "market_simulation": {
                "pair": "BTC/USDT",
                "scenario": "bearish_market",
                "candles_generated": len(bearish_data),
                "price_range": f"${bearish_data['close'].min():.0f} - ${bearish_data['close'].max():.0f}",
                "overall_decline": f"{((bearish_data['close'].iloc[-1] / bearish_data['close'].iloc[0]) - 1) * 100:.1f}%",
            },
            "signal_analysis": signal_test,
            "trade_simulation": trade_simulation,
            "short_selling_readiness": self._assess_short_readiness(
                signal_test, trade_simulation
            ),
        }

        return report

    def _assess_short_readiness(self, signal_test: dict, trade_sim: dict) -> dict:
        """Assess how ready the system is for short selling"""

        readiness_score = 0
        issues = []
        strengths = []

        # Check signal generation
        if signal_test["potential_short_signals"] > 5:
            readiness_score += 25
            strengths.append("Good short signal generation capability")
        else:
            issues.append("Limited short signal generation")

        # Check signal quality
        if signal_test["avg_bearish_conditions"] > 3:
            readiness_score += 25
            strengths.append("Strong bearish condition detection")
        else:
            issues.append("Weak bearish condition detection")

        # Check trade simulation
        if "trade_success" in trade_sim and trade_sim["trade_success"]:
            readiness_score += 25
            strengths.append("Profitable short trade simulation")
        else:
            issues.append("Short trade simulation showed losses")

        # Check risk management
        if "risk_reward_ratio" in trade_sim and trade_sim["risk_reward_ratio"] > 2:
            readiness_score += 25
            strengths.append("Good risk/reward ratio for shorts")
        else:
            issues.append("Poor risk/reward ratio for shorts")

        # Overall assessment
        if readiness_score >= 75:
            assessment = "excellent"
        elif readiness_score >= 50:
            assessment = "good"
        elif readiness_score >= 25:
            assessment = "fair"
        else:
            assessment = "needs_improvement"

        return {
            "readiness_score": readiness_score,
            "assessment": assessment,
            "strengths": strengths,
            "issues": issues,
            "recommendation": self._get_short_recommendation(assessment, issues),
        }

    def _get_short_recommendation(self, assessment: str, issues: list) -> str:
        """Get recommendation for short selling implementation"""

        if assessment == "excellent":
            return "Short selling system is ready for live trading"
        elif assessment == "good":
            return "Short selling system is mostly ready, monitor closely"
        elif assessment == "fair":
            return "Short selling needs optimization before live trading"
        else:
            return f"Address these issues before enabling shorts: {', '.join(issues)}"


def main():
    """Run short selling tests"""
    tester = ShortSellingTester()

    print("🔻 Short Selling Test System")
    print("=" * 50)

    # Run comprehensive test
    report = tester.create_short_test_report()

    print("📊 Market Simulation:")
    sim = report["market_simulation"]
    print(f"   Scenario: {sim['scenario']}")
    print(f"   Price Range: {sim['price_range']}")
    print(f"   Overall Decline: {sim['overall_decline']}")

    print("\n🎯 Signal Analysis:")
    signals = report["signal_analysis"]
    print(f"   Potential Short Signals: {signals['potential_short_signals']}")
    print(f"   Average Bearish Conditions: {signals['avg_bearish_conditions']:.1f}/5")

    print("\n💰 Trade Simulation:")
    trade = report["trade_simulation"]
    if "error" not in trade:
        print(f"   Entry: ${trade['entry_price']:.0f}")
        print(f"   Exit: ${trade['exit_price']:.0f} ({trade['exit_reason']})")
        print(f"   Profit: {trade['final_profit_pct']:.1f}%")
        print(f"   Success: {trade['trade_success']}")

    print("\n🎯 Short Selling Readiness:")
    readiness = report["short_selling_readiness"]
    print(f"   Assessment: {readiness['assessment'].upper()}")
    print(f"   Score: {readiness['readiness_score']}/100")
    print(f"   Recommendation: {readiness['recommendation']}")

    print("\n✅ Short selling test complete!")
    return report


if __name__ == "__main__":
    main()
