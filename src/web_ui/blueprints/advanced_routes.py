"""
Advanced Trading Routes Blueprint - Signal generation and execution
"""
import sys
from pathlib import Path
from flask import Blueprint, jsonify, request
from functools import wraps
import time
import asyncio
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import advanced engines
try:
    from src.advanced_signal_engine import AdvancedSignalEngine
    from src.signal_execution_engine import SignalExecutionEngine
    ADVANCED_ENGINES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Advanced engines not available: {e}")
    ADVANCED_ENGINES_AVAILABLE = False

advanced_bp = Blueprint('advanced', __name__, url_prefix='/api/advanced')

# Initialize engines
if ADVANCED_ENGINES_AVAILABLE:
    signal_engine = AdvancedSignalEngine()
    execution_engine = SignalExecutionEngine()

# Rate limiting
last_api_call = {}

def rate_limit(seconds=2):
    """Rate limiting decorator for expensive operations"""
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

@advanced_bp.route('/generate-signals/<symbol>')
@rate_limit(5)
def generate_signals(symbol):
    """Generate comprehensive trading signals for a symbol"""
    if not ADVANCED_ENGINES_AVAILABLE:
        return jsonify({
            'error': 'Advanced signal engine not available',
            'symbol': symbol,
            'signals': []
        })
    
    try:
        # Run async signal generation in new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        signals = loop.run_until_complete(
            signal_engine.analyze_comprehensive_signals(symbol)
        )
        
        loop.close()
        
        return jsonify({
            'symbol': symbol,
            'signals': [signal.to_dict() for signal in signals],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'symbol': symbol,
            'signals': []
        })

@advanced_bp.route('/execute-signal', methods=['POST'])
@rate_limit(10)
def execute_signal():
    """Execute a trading signal"""
    if not ADVANCED_ENGINES_AVAILABLE:
        return jsonify({
            'error': 'Signal execution engine not available',
            'execution_result': None
        })
    
    try:
        signal_data = request.get_json()
        
        # Run async execution in new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            execution_engine.execute_signal_data(signal_data)
        )
        
        loop.close()
        
        return jsonify({
            'execution_result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'execution_result': None
        })

@advanced_bp.route('/portfolio/positions')
def get_positions():
    """Get current active positions"""
    if not ADVANCED_ENGINES_AVAILABLE:
        return jsonify({
            'error': 'Execution engine not available',
            'positions': []
        })
    
    try:
        positions = execution_engine.get_active_positions()
        return jsonify({
            'positions': positions,
            'count': len(positions),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'positions': []
        })