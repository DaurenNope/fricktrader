#!/usr/bin/env python3
"""
Demo script for the Market Regime Analyzer and Advanced Portfolio Manager
Shows how the system dynamically adjusts strategy allocations based on market conditions.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from market_analysis.crypto_market_regime_analyzer import (
    CryptoMarketRegimeAnalyzer
)
from core.advanced_portfolio_manager import AdvancedPortfolioManager

def generate_sample_market_data(regime_type="bull", days=100):
    """Generate sample market data for different regime types"""
    
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), end=datetime.now(), freq='1H')
    
    if regime_type == "bull":
        # Bull market: upward trending with volatility
        base_price = 30000
        trend = np.linspace(0, 0.5, len(dates))  # 50% upward trend
        volatility = np.random.normal(0, 0.02, len(dates))  # 2% volatility
        price_changes = trend + volatility
        
    elif regime_type == "bear":
        # Bear market: downward trending
        base_price = 45000
        trend = np.linspace(0, -0.3, len(dates))  # 30% downward trend
        volatility = np.random.normal(0, 0.03, len(dates))  # 3% volatility
        price_changes = trend + volatility
        
    elif regime_type == "sideways":
        # Sideways market: range-bound
        base_price = 35000
        trend = np.sin(np.linspace(0, 4*np.pi, len(dates))) * 0.05  # Oscillating ±5%
        volatility = np.random.normal(0, 0.015, len(dates))  # 1.5% volatility
        price_changes = trend + volatility
        
    else:  # volatile/transitional
        # Volatile/transitional market
        base_price = 40000
        trend = np.random.normal(0, 0.01, len(dates))  # No clear trend
        volatility = np.random.normal(0, 0.04, len(dates))  # 4% high volatility
        price_changes = trend + volatility
    
    # Generate price series
    prices = [base_price]
    for change in price_changes[1:]:
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1000))  # Floor at $1000
    
    # Create OHLCV data
    btc_data = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'close': prices,
        'volume': np.random.normal(1000000, 200000, len(dates))
    })
    btc_data.set_index('timestamp', inplace=True)
    
    # Generate ETH data (correlated but different)
    eth_multiplier = 0.08  # ETH ~8% of BTC price
    eth_data = btc_data.copy()
    eth_data *= eth_multiplier
    eth_data['volume'] *= 0.7  # Lower volume
    
    return {
        'BTC': btc_data,
        'ETH': eth_data,
        'total_market_cap': btc_data * 10  # Simulate total market cap
    }

def demo_regime_analyzer():
    """Demonstrate the Market Regime Analyzer with different market scenarios"""
    
    print("🚀 Crypto Market Regime Analyzer Demo")
    print("=" * 50)
    
    analyzer = CryptoMarketRegimeAnalyzer()
    
    # Test different market scenarios
    scenarios = [
        ("Bull Market", "bull"),
        ("Bear Market", "bear"), 
        ("Sideways Market", "sideways"),
        ("Volatile/Transitional", "volatile")
    ]
    
    for scenario_name, regime_type in scenarios:
        print(f"\n📊 Analyzing {scenario_name} Scenario")
        print("-" * 40)
        
        # Generate sample data
        market_data = generate_sample_market_data(regime_type)
        
        # Analyze regime
        result = analyzer.analyze_market_regime(market_data)
        
        # Display results
        print(f"Market Regime: {result.market_regime.value.upper()}")
        print(f"Volatility Regime: {result.volatility_regime.value}")
        print(f"Risk Environment: {result.risk_environment.value}")
        print(f"Fundamental Health: {result.fundamental_health.value}")
        print(f"Confidence Score: {result.confidence_score:.1%}")
        print(f"Regime Duration: {result.regime_duration} days")
        
        # Show key signals
        print("\n🔍 Key Signals:")
        important_signals = [
            'higher_tf_trend', 'market_structure', 'volatility_regime',
            'risk_environment', 'volume_trend'
        ]
        
        for signal in important_signals:
            if signal in result.signals:
                value = result.signals[signal]
                print(f"  {signal.replace('_', ' ').title()}: {value:+.2f}")
    
    return analyzer

def demo_advanced_portfolio_manager():
    """Demonstrate the Advanced Portfolio Manager with regime integration"""
    
    print("\n\n💼 Advanced Portfolio Manager Demo")
    print("=" * 50)
    
    # Initialize portfolio manager
    portfolio_manager = AdvancedPortfolioManager(initial_balance=10000.0)
    
    # Simulate different market conditions over time
    market_scenarios = [
        ("Initial Bull Run", "bull"),
        ("Market Correction", "bear"),
        ("Recovery Phase", "sideways"),
        ("New Bull Phase", "bull")
    ]
    
    for phase, regime_type in market_scenarios:
        print(f"\n📈 {phase}")
        print("-" * 30)
        
        # Generate market data for this phase
        market_data = generate_sample_market_data(regime_type, days=30)
        
        # Analyze and rebalance
        portfolio_state = portfolio_manager.analyze_and_rebalance(market_data)
        
        # Get and display portfolio summary
        summary = portfolio_manager.get_portfolio_summary()
        
        print("\n🏛️ Regime Analysis:")
        regime_info = summary['regime_info']
        print(f"  Market Regime: {regime_info['market_regime']}")
        print(f"  Volatility: {regime_info['volatility_regime']}")
        print(f"  Risk Environment: {regime_info['risk_environment']}")
        print(f"  Confidence: {regime_info['confidence']}")
        
        print("\n💰 Portfolio Metrics:")
        portfolio_metrics = summary['portfolio_metrics']
        print(f"  Total Balance: {portfolio_metrics['total_balance']}")
        print(f"  Allocated: {portfolio_metrics['allocated_balance']}")
        print(f"  Available: {portfolio_metrics['available_balance']}")
        print(f"  Risk Exposure: {portfolio_metrics['total_risk_exposure']}")
        print(f"  Active Strategies: {portfolio_metrics['active_strategies']}")
        
        print("\n🎯 Strategy Allocations:")
        if 'strategy_allocations' in summary and summary['strategy_allocations']:
            for strategy_name, details in summary['strategy_allocations'].items():
                print(f"  {strategy_name}:")
                print(f"    Allocation: {details['allocation']}")
                print(f"    Enabled: {details['enabled']}")
                print(f"    Regime Fit: {details['regime_suitability']}")
                print(f"    Risk Contribution: {details['risk_contribution']}")
        else:
            print("  No active strategy allocations")
        
        # Simulate some performance updates
        for strategy in portfolio_state.active_strategies:
            # Simulate random performance based on regime suitability
            regime_fit = portfolio_state.strategy_allocations[strategy].regime_suitability
            performance = np.random.normal(regime_fit * 0.02, 0.01)  # Better performance if regime fits
            portfolio_manager.update_strategy_performance(strategy, performance)

def main():
    """Run the complete demo"""
    print("🎯 Market Regime Analyzer & Portfolio Manager Demo")
    print("📅 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    try:
        # Demo 1: Market Regime Analyzer
        demo_regime_analyzer()
        
        # Demo 2: Advanced Portfolio Manager
        demo_advanced_portfolio_manager()
        
        print("\n\n✅ Demo completed successfully!")
        print("\n🔥 Key Features Demonstrated:")
        print("  ✓ Multi-timeframe market regime detection")
        print("  ✓ Volatility regime classification")
        print("  ✓ Risk environment analysis")
        print("  ✓ Dynamic strategy allocation based on market conditions")
        print("  ✓ Performance-based allocation adjustments")
        print("  ✓ Risk-managed portfolio rebalancing")
        
        print("\n🚀 Next Steps:")
        print("  • Integrate with live market data feeds")
        print("  • Add on-chain data integration")
        print("  • Implement real trading execution")
        print("  • Add machine learning enhancements")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()