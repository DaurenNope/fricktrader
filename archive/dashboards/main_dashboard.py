#!/usr/bin/env python3
"""
FRICKTRADER CLEAN DASHBOARD
Single file, no duplicates, minimal working dashboard

Author: FrickTrader Team
Version: Clean 1.0
"""

import os
from datetime import datetime
from flask import Flask, jsonify, render_template_string
import logging
from src.defi_yield import DeFiYieldOptimizer, RiskLevel

# Add project root to path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import other major systems
try:
    from src.backtesting.core_engine import BacktestingEngine
    from src.advanced_signal_engine import AdvancedSignalEngine
    SYSTEMS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Some systems unavailable: {e}")
    SYSTEMS_AVAILABLE = False

# Initialize DeFi optimizer
defi_optimizer = DeFiYieldOptimizer()

# Initialize other systems if available
if SYSTEMS_AVAILABLE:
    try:
        backtesting_engine = BacktestingEngine()
        signal_engine = AdvancedSignalEngine()
        logger.info("✅ All trading systems initialized")
    except Exception as e:
        logger.error(f"System initialization error: {e}")
        SYSTEMS_AVAILABLE = False

# Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'fricktrader-clean-2024'

# Simple in-memory data store
data_store = {
    'portfolio': {
        'total_value': 10000.0,
        'today_pnl': 0.0,
        'positions': 0,
        'win_rate': 0.0
    },
    'market': {
        'btc_price': 105000,
        'eth_price': 4300,
        'sol_price': 215,
        'ada_price': 1.2
    }
}

# Clean HTML template
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FrickTrader - Clean Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .card { @apply bg-gray-800 p-6 rounded-lg border border-gray-700; }
        .metric-value { @apply text-2xl font-bold text-green-400; }
        .metric-label { @apply text-sm text-gray-400; }
    </style>
</head>
<body class="bg-gray-900 text-white">
    <div class="container mx-auto p-6">
        <h1 class="text-3xl font-bold mb-8 text-blue-400">🚀 FrickTrader - Clean Dashboard</h1>

        <!-- Portfolio Section -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="card">
                <div class="metric-label">Portfolio Value</div>
                <div class="metric-value" id="portfolioValue">$0</div>
            </div>
            <div class="card">
                <div class="metric-label">Today P&L</div>
                <div class="metric-value" id="todayPnl">$0</div>
            </div>
            <div class="card">
                <div class="metric-label">Positions</div>
                <div class="metric-value" id="positions">0</div>
            </div>
            <div class="card">
                <div class="metric-label">Win Rate</div>
                <div class="metric-value" id="winRate">0%</div>
            </div>
        </div>

        <!-- Market Prices -->
        <div class="card mb-8">
            <h2 class="text-xl font-bold mb-4 text-yellow-400">📊 Market Prices</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                    <div class="metric-label">BTC/USDT</div>
                    <div class="metric-value text-orange-400" id="btcPrice">$0</div>
                </div>
                <div>
                    <div class="metric-label">ETH/USDT</div>
                    <div class="metric-value text-blue-400" id="ethPrice">$0</div>
                </div>
                <div>
                    <div class="metric-label">SOL/USDT</div>
                    <div class="metric-value text-purple-400" id="solPrice">$0</div>
                </div>
                <div>
                    <div class="metric-label">ADA/USDT</div>
                    <div class="metric-value text-cyan-400" id="adaPrice">$0</div>
                </div>
            </div>
        </div>

        <!-- Status -->
        <div class="card">
            <h2 class="text-xl font-bold mb-4 text-green-400">✅ System Status</h2>
            <div id="status" class="text-green-400">Loading...</div>
            <div id="lastUpdate" class="text-gray-400 text-sm mt-2"></div>
        </div>
    </div>

    <script>
        // Simple API calls
        async function loadData() {
            try {
                console.log('Loading dashboard data...');

                // Load portfolio data
                const portfolioResponse = await fetch('/api/portfolio');
                if (portfolioResponse.ok) {
                    const portfolio = await portfolioResponse.json();
                    document.getElementById('portfolioValue').textContent = `$${portfolio.total_value.toLocaleString()}`;
                    document.getElementById('todayPnl').textContent = `$${portfolio.today_pnl.toLocaleString()}`;
                    document.getElementById('positions').textContent = portfolio.positions;
                    document.getElementById('winRate').textContent = `${portfolio.win_rate}%`;
                } else {
                    console.error('Portfolio API failed:', portfolioResponse.status);
                }

                // Load market data
                const marketResponse = await fetch('/api/market');
                if (marketResponse.ok) {
                    const market = await marketResponse.json();
                    document.getElementById('btcPrice').textContent = `$${market.btc_price.toLocaleString()}`;
                    document.getElementById('ethPrice').textContent = `$${market.eth_price.toLocaleString()}`;
                    document.getElementById('solPrice').textContent = `$${market.sol_price.toLocaleString()}`;
                    document.getElementById('adaPrice').textContent = `$${market.ada_price.toLocaleString()}`;
                } else {
                    console.error('Market API failed:', marketResponse.status);
                }

                // Update status
                document.getElementById('status').textContent = 'System Operational';
                document.getElementById('lastUpdate').textContent = `Last updated: ${new Date().toLocaleTimeString()}`;

            } catch (error) {
                console.error('Error loading data:', error);
                document.getElementById('status').textContent = 'System Error';
                document.getElementById('status').className = 'text-red-400';
            }
        }

        // Load data on page load
        document.addEventListener('DOMContentLoaded', loadData);

        // Auto-refresh every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/api/portfolio')
def get_portfolio():
    """Get portfolio data - CLEAN API"""
    try:
        return jsonify(data_store['portfolio'])
    except Exception as e:
        logger.error(f"Portfolio API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/signals/live')
def get_live_signals():
    """Get live trading signals"""
    try:
        # Mock live signals data
        live_signals = [
            {
                'symbol': 'BTC/USDT',
                'signal': 'BUY',
                'strength': 8.5,
                'price': 104850,
                'target': 108000,
                'stop_loss': 102000,
                'confidence': 85,
                'timestamp': datetime.now().isoformat(),
                'strategy': 'Momentum Breakout'
            },
            {
                'symbol': 'ETH/USDT',
                'signal': 'SELL',
                'strength': 7.2,
                'price': 4381,
                'target': 4200,
                'stop_loss': 4450,
                'confidence': 72,
                'timestamp': datetime.now().isoformat(),
                'strategy': 'RSI Divergence'
            },
            {
                'symbol': 'SOL/USDT',
                'signal': 'HOLD',
                'strength': 6.1,
                'price': 215.52,
                'target': 0,
                'stop_loss': 0,
                'confidence': 61,
                'timestamp': datetime.now().isoformat(),
                'strategy': 'Range Trading'
            }
        ]

        return jsonify({
            'signals': live_signals,
            'total_signals': len(live_signals),
            'active_strategies': ['Momentum Breakout', 'RSI Divergence', 'Range Trading'],
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Live signals API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/backtesting/results')
def get_backtest_results():
    """Get recent backtesting results"""
    try:
        # Mock backtesting results
        backtest_results = [
            {
                'strategy': 'DCA Bitcoin',
                'period': '1M',
                'total_return': 15.8,
                'sharpe_ratio': 1.42,
                'max_drawdown': -8.5,
                'win_rate': 68.5,
                'total_trades': 24,
                'status': 'completed'
            },
            {
                'strategy': 'ETH Momentum',
                'period': '1M',
                'total_return': 23.4,
                'sharpe_ratio': 1.78,
                'max_drawdown': -12.3,
                'win_rate': 71.2,
                'total_trades': 18,
                'status': 'completed'
            },
            {
                'strategy': 'Multi-Altcoin',
                'period': '2W',
                'total_return': 8.9,
                'sharpe_ratio': 0.95,
                'max_drawdown': -15.7,
                'win_rate': 58.3,
                'total_trades': 42,
                'status': 'running'
            }
        ]

        return jsonify({
            'results': backtest_results,
            'summary': {
                'avg_return': sum(r['total_return'] for r in backtest_results) / len(backtest_results),
                'best_strategy': max(backtest_results, key=lambda x: x['total_return'])['strategy'],
                'total_strategies': len(backtest_results)
            },
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Backtest results API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/analysis')
def get_market_analysis():
    """Get market sentiment and technical analysis"""
    try:
        market_analysis = {
            'sentiment': {
                'overall': 'BULLISH',
                'score': 72,
                'fear_greed_index': 68,
                'social_sentiment': 'POSITIVE',
                'news_sentiment': 'NEUTRAL'
            },
            'technical': {
                'btc_trend': 'UPWARD',
                'support_level': 102000,
                'resistance_level': 108000,
                'rsi': 65.8,
                'macd': 'BULLISH_CROSSOVER'
            },
            'alerts': [
                {
                    'type': 'BREAKOUT',
                    'message': 'BTC broke resistance at $105K',
                    'priority': 'HIGH',
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'type': 'VOLUME',
                    'message': 'ETH volume spike detected',
                    'priority': 'MEDIUM',
                    'timestamp': datetime.now().isoformat()
                }
            ],
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(market_analysis)

    except Exception as e:
        logger.error(f"Market analysis API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trading/positions')
def get_active_positions():
    """Get active trading positions"""
    try:
        positions = [
            {
                'symbol': 'BTC/USDT',
                'side': 'LONG',
                'size': 0.5,
                'entry_price': 102500,
                'current_price': 104850,
                'pnl': 1175.0,
                'pnl_percent': 2.29,
                'margin': 10250,
                'leverage': 5,
                'status': 'OPEN'
            },
            {
                'symbol': 'ETH/USDT',
                'side': 'LONG',
                'size': 2.0,
                'entry_price': 4200,
                'current_price': 4381,
                'pnl': 362.0,
                'pnl_percent': 4.31,
                'margin': 4200,
                'leverage': 2,
                'status': 'OPEN'
            }
        ]

        total_pnl = sum(pos['pnl'] for pos in positions)
        total_margin = sum(pos['margin'] for pos in positions)

        return jsonify({
            'positions': positions,
            'summary': {
                'total_positions': len(positions),
                'total_pnl': total_pnl,
                'total_margin': total_margin,
                'total_pnl_percent': (total_pnl / total_margin) * 100 if total_margin > 0 else 0
            },
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Active positions API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market')
def get_market():
    """Get market data - CLEAN API"""
    try:
        return jsonify(data_store['market'])
    except Exception as e:
        logger.error(f"Market API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """Get system status - CLEAN API"""
    return jsonify({
        'status': 'operational',
        'timestamp': datetime.now().isoformat(),
        'version': 'Clean 1.0'
    })

@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'healthy'})

@app.route('/api/defi/opportunities')
def get_defi_opportunities():
    """Get DeFi yield opportunities"""
    try:
        # Sample user portfolio
        user_tokens = {
            'USDT': 1000.0,
            'ETH': 2.5,
            'USDC': 500.0,
            'BTC': 0.1
        }

        # Get opportunities for each token
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        preferences = {
            'max_risk_level': RiskLevel.MEDIUM,
            'min_apy': 5.0,
            'gas_budget': 100
        }

        all_opportunities = []
        for token, amount in user_tokens.items():
            if amount > 0:
                opportunities = loop.run_until_complete(
                    defi_optimizer.get_opportunities_for_token(token, amount, preferences)
                )
                for opp in opportunities[:2]:  # Top 2 per token
                    all_opportunities.append({
                        'protocol': opp.protocol,
                        'pool_name': opp.pool_name,
                        'token': token,
                        'apy': opp.total_apy,
                        'risk_level': opp.risk_level.name,
                        'tvl': opp.tvl,
                        'minimum_deposit': opp.minimum_deposit,
                        'auto_compound': opp.auto_compound,
                        'estimated_gas': opp.estimated_gas_cost
                    })

        loop.close()

        return jsonify({
            'opportunities': all_opportunities,
            'total_opportunities': len(all_opportunities),
            'user_portfolio': user_tokens,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"DeFi opportunities API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/defi/optimize')
def optimize_portfolio():
    """Optimize DeFi portfolio allocation"""
    try:
        # Sample user portfolio
        user_tokens = {
            'USDT': 1000.0,
            'ETH': 2.5,
            'USDC': 500.0,
            'BTC': 0.1
        }

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            defi_optimizer.optimize_yield_for_portfolio(user_tokens)
        )

        loop.close()

        # Format for frontend
        formatted_result = {
            'total_expected_apy': result.get('total_expected_apy', 0),
            'total_risk_score': result.get('total_risk_score', 0),
            'estimated_gas_costs': result.get('estimated_gas_costs', 0),
            'portfolio_metrics': result.get('portfolio_metrics', {}),
            'recommendations': result.get('recommendations', []),
            'user_portfolio': result.get('user_portfolio', {}),
            'analysis_timestamp': result.get('analysis_timestamp', '')
        }

        return jsonify(formatted_result)

    except Exception as e:
        logger.error(f"Portfolio optimization API error: {e}")
        return jsonify({'error': str(e)}), 500

def update_portfolio_data():
    """Update portfolio with real data (placeholder for now)"""
    # This is where we'd connect to actual trading systems
    data_store['portfolio'].update({
        'total_value': 10000.0,
        'today_pnl': 150.0,
        'positions': 3,
        'win_rate': 75.5
    })

def update_market_data():
    """Update market prices (placeholder for now)"""
    # This is where we'd connect to actual market data
    import random
    base_prices = {'btc': 105000, 'eth': 4300, 'sol': 215, 'ada': 1.2}

    for coin, base_price in base_prices.items():
        # Simulate price movement
        change = random.uniform(-0.02, 0.02)  # ±2%
        new_price = base_price * (1 + change)
        data_store['market'][f'{coin}_price'] = round(new_price, 2 if coin != 'ada' else 4)

if __name__ == '__main__':
    print("🚀 Starting Clean FrickTrader Dashboard...")
    print("📊 Features:")
    print("  • Portfolio overview")
    print("  • Market prices")
    print("  • System status")
    print("  • Real-time updates")
    print("")

    # Update data once on startup
    update_portfolio_data()
    update_market_data()

    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5001))
    print(f"🌐 Dashboard available at: http://127.0.0.1:{port}")

    app.run(
        host='127.0.0.1',
        port=port,
        debug=True,
        use_reloader=False
    )
