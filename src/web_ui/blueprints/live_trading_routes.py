"""
Live Trading API Routes Blueprint
"""
import sys
from pathlib import Path
from flask import Blueprint, jsonify, request
from functools import wraps
import time
import asyncio
import threading
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

live_trading_bp = Blueprint('live_trading', __name__, url_prefix='/api/live-trading')

# Global storage for live trading engines
live_trading_engines = {}

# Rate limiting
last_api_call = {}

def rate_limit(seconds=1):
    """Rate limiting decorator to prevent API abuse"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = f"{f.__name__}:{':'.join(map(str, args))}"
            now = time.time()
            
            if key in last_api_call:
                if now - last_api_call[key] < seconds:
                    return jsonify({'error': 'Rate limit exceeded', 'retry_after': seconds}), 429
            
            last_api_call[key] = now
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@live_trading_bp.route('/start', methods=['POST'])
@rate_limit(5)
def start_live_trading():
    """Start live trading with selected strategies"""
    try:
        data = request.get_json()
        strategies = data.get('strategies', [])
        symbols = data.get('symbols', ['BTC/USDT'])
        initial_capital = data.get('initial_capital', 10000)
        
        # Import live trading engine
        from src.live_trading_engine import LiveTradingEngine
        
        # Start live trading engine
        engine = LiveTradingEngine(initial_capital=initial_capital)
        
        # Load and start strategies
        for strategy_name in strategies:
            engine.load_strategy(strategy_name, symbols)
        
        # Start the engine in background
        def run_engine():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(engine.run())
        
        engine_id = f"engine_{int(time.time())}"
        live_trading_engines[engine_id] = engine
        
        # Start engine in background thread
        trading_thread = threading.Thread(target=run_engine, daemon=True)
        trading_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': f'Live trading started with {len(strategies)} strategies on {len(symbols)} symbols',
            'engine_id': engine_id,
            'strategies': strategies,
            'symbols': symbols,
            'initial_capital': initial_capital,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@live_trading_bp.route('/stop', methods=['POST'])
@rate_limit(2)
def stop_live_trading():
    """Stop live trading engine"""
    try:
        data = request.get_json()
        engine_id = data.get('engine_id', 'all')
        
        if engine_id == 'all':
            # Stop all engines
            for engine in live_trading_engines.values():
                engine.stop()
            live_trading_engines.clear()
            message = "All live trading engines stopped"
        elif engine_id in live_trading_engines:
            # Stop specific engine
            live_trading_engines[engine_id].stop()
            del live_trading_engines[engine_id]
            message = f"Live trading engine {engine_id} stopped"
        else:
            return jsonify({
                'status': 'error',
                'error': f'Engine {engine_id} not found',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        return jsonify({
            'status': 'success',
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@live_trading_bp.route('/status')
@rate_limit(1)
def get_live_trading_status():
    """Get live trading status and performance"""
    try:
        if not live_trading_engines:
            return jsonify({
                'status': 'inactive',
                'message': 'No live trading engines running',
                'engines': [],
                'total_engines': 0,
                'timestamp': datetime.now().isoformat()
            })
        
        engine_statuses = []
        total_pnl = 0
        total_positions = 0
        total_trades = 0
        
        for engine_id, engine in live_trading_engines.items():
            portfolio_status = engine.get_portfolio_status()
            engine_statuses.append({
                'engine_id': engine_id,
                'status': 'active' if engine.running else 'stopped',
                'strategies': list(engine.strategies.keys()),
                'symbols': list(engine.symbol_data.keys()),
                'total_pnl': portfolio_status.get('total_pnl', 0),
                'active_positions': len(portfolio_status.get('positions', [])),
                'total_trades': len(portfolio_status.get('trades', [])),
                'start_time': engine.start_time.isoformat() if hasattr(engine, 'start_time') else None
            })
            
            total_pnl += portfolio_status.get('total_pnl', 0)
            total_positions += len(portfolio_status.get('positions', []))
            total_trades += len(portfolio_status.get('trades', []))
        
        return jsonify({
            'status': 'active',
            'engines': engine_statuses,
            'total_engines': len(engine_statuses),
            'portfolio_summary': {
                'total_pnl': round(total_pnl, 2),
                'total_positions': total_positions,
                'total_trades': total_trades,
                'daily_return': round((total_pnl / 10000) * 100, 2) if total_pnl != 0 else 0
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@live_trading_bp.route('/positions')
@rate_limit(1)
def get_live_positions():
    """Get current live trading positions"""
    try:
        all_positions = []
        
        for engine_id, engine in live_trading_engines.items():
            portfolio_status = engine.get_portfolio_status()
            positions = portfolio_status.get('positions', [])
            
            for pos in positions:
                all_positions.append({
                    'engine_id': engine_id,
                    'symbol': pos.get('symbol'),
                    'strategy': pos.get('strategy'),
                    'entry_price': pos.get('entry_price'),
                    'current_price': pos.get('current_price'),
                    'quantity': pos.get('quantity'),
                    'pnl': pos.get('pnl'),
                    'pnl_percent': pos.get('pnl_percent'),
                    'side': pos.get('side', 'LONG'),
                    'entry_time': pos.get('entry_time'),
                    'trailing_stop': pos.get('trailing_stop')
                })
        
        return jsonify({
            'status': 'success',
            'positions': all_positions,
            'total_positions': len(all_positions),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'positions': [],
            'timestamp': datetime.now().isoformat()
        }), 500

@live_trading_bp.route('/trades')
@rate_limit(1)
def get_live_trades():
    """Get recent live trading trades"""
    try:
        all_trades = []
        
        for engine_id, engine in live_trading_engines.items():
            portfolio_status = engine.get_portfolio_status()
            trades = portfolio_status.get('trades', [])
            
            # Get last 50 trades per engine
            recent_trades = trades[-50:] if len(trades) > 50 else trades
            
            for trade in recent_trades:
                all_trades.append({
                    'engine_id': engine_id,
                    'symbol': trade.get('symbol'),
                    'strategy': trade.get('strategy'),
                    'side': trade.get('side', 'LONG'),
                    'entry_price': trade.get('entry_price'),
                    'exit_price': trade.get('exit_price'),
                    'quantity': trade.get('quantity'),
                    'pnl': trade.get('pnl'),
                    'pnl_percent': trade.get('pnl_percent'),
                    'entry_time': trade.get('entry_time'),
                    'exit_time': trade.get('exit_time'),
                    'exit_reason': trade.get('exit_reason')
                })
        
        # Sort by exit time (most recent first)
        all_trades.sort(key=lambda x: x.get('exit_time', ''), reverse=True)
        
        return jsonify({
            'status': 'success',
            'trades': all_trades[:100],  # Limit to 100 most recent trades
            'total_trades': len(all_trades),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'trades': [],
            'timestamp': datetime.now().isoformat()
        }), 500

@live_trading_bp.route('/batch-backtest', methods=['POST'])
@rate_limit(10)
def run_batch_backtest():
    """Run batch backtest on multiple strategies"""
    try:
        data = request.get_json()
        strategies = data.get('strategies', 'all')
        symbol = data.get('symbol', 'BTC/USDT')
        timeframe = data.get('timeframe', '1h')
        initial_capital = data.get('initial_capital', 10000)
        
        from src.advanced_backtesting_engine import run_advanced_backtest
        from src.custom_strategy_manager import list_custom_strategies
        
        # Get all available strategies if 'all' is selected
        if strategies == 'all':
            built_in_strategies = ['advanced_sma', 'mean_reversion', 'momentum_breakout', 'volatility_scaling']
            custom_strategies = list_custom_strategies()
            strategies = built_in_strategies + custom_strategies
        
        batch_results = []
        
        for strategy_name in strategies:
            try:
                result = run_advanced_backtest(
                    strategy_name=strategy_name,
                    symbol=symbol,
                    timeframe=timeframe,
                    initial_capital=initial_capital
                )
                
                strategy_result = {
                    'strategy': strategy_name,
                    'status': result.get('status', 'success'),
                    'total_return': result.get('results', {}).get('total_return', 0),
                    'win_rate': result.get('results', {}).get('win_rate', 0),
                    'max_drawdown': result.get('results', {}).get('max_drawdown', 0),
                    'sharpe_ratio': result.get('results', {}).get('sharpe_ratio', 0),
                    'total_trades': result.get('results', {}).get('total_trades', 0),
                    'profit_factor': result.get('results', {}).get('profit_factor', 0),
                    'final_capital': result.get('results', {}).get('final_capital', initial_capital)
                }
                
                batch_results.append(strategy_result)
                
            except Exception as strategy_error:
                batch_results.append({
                    'strategy': strategy_name,
                    'status': 'error',
                    'error': str(strategy_error),
                    'total_return': 0,
                    'win_rate': 0,
                    'max_drawdown': 0,
                    'sharpe_ratio': 0,
                    'total_trades': 0,
                    'profit_factor': 0,
                    'final_capital': initial_capital
                })
        
        batch_results.sort(key=lambda x: x.get('total_return', 0), reverse=True)
        successful_strategies = [r for r in batch_results if r.get('status') == 'success']
        
        summary = {
            'total_strategies': len(strategies),
            'successful_backtests': len(successful_strategies),
            'failed_backtests': len(strategies) - len(successful_strategies),
            'best_strategy': successful_strategies[0]['strategy'] if successful_strategies else None,
            'best_return': successful_strategies[0]['total_return'] if successful_strategies else 0,
            'avg_return': sum(s['total_return'] for s in successful_strategies) / len(successful_strategies) if successful_strategies else 0,
            'avg_win_rate': sum(s['win_rate'] for s in successful_strategies) / len(successful_strategies) if successful_strategies else 0
        }
        
        return jsonify({
            'status': 'success',
            'symbol': symbol,
            'timeframe': timeframe,
            'initial_capital': initial_capital,
            'results': batch_results,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@live_trading_bp.route("/realistic-trades")
@rate_limit(2)
def get_realistic_trades():
    """Get realistic trade history with actual historical BTC prices"""
    try:
        # Import the real trade generator
        from src.web_ui.real_trade_generator import update_trade_history_with_real_data
        
        realistic_data = update_trade_history_with_real_data()
        
        if realistic_data:
            return jsonify(realistic_data)
        else:
            return jsonify({
                "trades": [],
                "summary": {
                    "total_trades": 0,
                    "total_profit_abs": 0,
                    "total_stake": 0,
                    "win_rate": 0,
                    "data_source": "Error generating realistic data"
                }
            }), 500
            
    except Exception as e:
        return jsonify({
            "error": str(e),
            "trades": [],
            "summary": {
                "total_trades": 0,
                "total_profit_abs": 0,
                "data_source": f"Error: {str(e)}"
            }
        }), 500
