"""
DeFi Routes Blueprint - Yield optimization and protocol analysis
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

# Import DeFi optimizer
try:
    from src.defi_yield_optimizer import DeFiYieldOptimizer
    DEFI_OPTIMIZER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ DeFi optimizer not available: {e}")
    DEFI_OPTIMIZER_AVAILABLE = False

defi_bp = Blueprint('defi', __name__, url_prefix='/api/defi')

# Initialize optimizer
if DEFI_OPTIMIZER_AVAILABLE:
    defi_optimizer = DeFiYieldOptimizer()

# Rate limiting
last_api_call = {}

def rate_limit(seconds=3):
    """Rate limiting decorator for DeFi operations"""
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

@defi_bp.route('/optimize-yield', methods=['POST'])
@rate_limit(10)
def optimize_yield():
    """Optimize yield for user's token portfolio"""
    if not DEFI_OPTIMIZER_AVAILABLE:
        return jsonify({
            'error': 'DeFi optimizer not available',
            'optimization_result': None
        })
    
    try:
        data = request.get_json()
        user_tokens = data.get('tokens', {})
        preferences = data.get('preferences', {})
        
        # Run async optimization in new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            defi_optimizer.optimize_yield_for_portfolio(user_tokens, preferences)
        )
        
        loop.close()
        
        return jsonify({
            'optimization_result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'optimization_result': None
        })

@defi_bp.route('/protocols/<protocol_name>')
@rate_limit(5)
def get_protocol_opportunities(protocol_name):
    """Get opportunities for a specific DeFi protocol"""
    if not DEFI_OPTIMIZER_AVAILABLE:
        return jsonify({
            'error': 'DeFi optimizer not available',
            'protocol': protocol_name,
            'opportunities': []
        })
    
    try:
        # Mock protocol-specific data
        protocol_data = {
            'ethena': {
                'name': 'Ethena Protocol',
                'tvl': '$2.5B',
                'main_product': 'USDe Delta Neutral Staking',
                'current_apy': '21.0%',
                'risk_level': 'Medium',
                'opportunities': [
                    {
                        'pool_name': 'USDe Staking',
                        'apy': '21.0%',
                        'tvl': '$2.5B',
                        'min_deposit': '$100',
                        'lockup': 'None',
                        'risk_factors': ['Smart contract risk', 'Synthetic asset risk'],
                        'advantages': ['Delta neutral', 'High yield', 'No IL risk']
                    }
                ]
            },
            'pendle': {
                'name': 'Pendle Finance',
                'tvl': '$850M',
                'main_product': 'Yield Trading',
                'current_apy': '16.0%',
                'risk_level': 'Medium',
                'opportunities': [
                    {
                        'pool_name': 'PT-stETH Dec2025',
                        'apy': '16.0%',
                        'tvl': '$850M',
                        'min_deposit': '$200',
                        'lockup': 'Until maturity',
                        'risk_factors': ['Interest rate risk', 'Smart contract risk'],
                        'advantages': ['Fixed yield', 'Liquid PT tokens', 'Battle-tested']
                    }
                ]
            },
            'uniswap': {
                'name': 'Uniswap V3',
                'tvl': '$45B',
                'main_product': 'Concentrated Liquidity',
                'current_apy': '11.0%',
                'risk_level': 'Medium',
                'opportunities': [
                    {
                        'pool_name': 'ETH/USDC 0.30%',
                        'apy': '11.0%',
                        'tvl': '$45B',
                        'min_deposit': '$500',
                        'lockup': 'None',
                        'risk_factors': ['Impermanent loss', 'Active management needed'],
                        'advantages': ['High liquidity', 'Fee rewards', 'UNI incentives']
                    }
                ]
            }
        }
        
        protocol_info = protocol_data.get(protocol_name.lower(), {
            'name': protocol_name.title(),
            'error': 'Protocol not found or not supported yet',
            'opportunities': []
        })
        
        return jsonify({
            'protocol': protocol_name,
            'data': protocol_info,
            'last_update': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'protocol': protocol_name,
            'opportunities': []
        })

@defi_bp.route('/yield-comparison')
@rate_limit(5)
def get_yield_comparison():
    """Compare yields across different protocols"""
    return jsonify({
        'protocols': [
            {'name': 'Ethena USDe', 'apy': 21.0, 'risk': 'Medium', 'liquidity': 'High'},
            {'name': 'Pendle PT-stETH', 'apy': 16.0, 'risk': 'Medium', 'liquidity': 'High'},
            {'name': 'Uniswap V3 ETH/USDC', 'apy': 11.0, 'risk': 'Medium', 'liquidity': 'Very High'},
            {'name': 'Aave USDC', 'apy': 3.5, 'risk': 'Low', 'liquidity': 'Very High'}
        ],
        'timestamp': datetime.now().isoformat()
    })