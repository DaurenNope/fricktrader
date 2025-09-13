"""
Dashboard Routes Blueprint - Main web interface routes
"""
import sys
from pathlib import Path
from flask import Blueprint, render_template, jsonify
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    """Main dashboard page"""
    return render_template('professional_dashboard.html', 
                         symbols=["BTC/USDT", "ETH/USDT", "ADA/USDT", "SOL/USDT"])

@dashboard_bp.route('/dashboard')
def dashboard():
    """Dashboard page - same as index"""
    return render_template('professional_dashboard.html',
                         symbols=["BTC/USDT", "ETH/USDT", "ADA/USDT", "SOL/USDT"])

@dashboard_bp.route('/api/dashboard-stats')
def get_dashboard_stats():
    """Get dashboard statistics"""
    return jsonify({
        'total_portfolio_value': 125420.55,
        'day_change': 2.34,
        'day_change_percent': 1.89,
        'active_positions': 8,
        'pending_signals': 3,
        'successful_trades_today': 12,
        'win_rate': 78.5,
        'last_update': datetime.now().isoformat()
    })

@dashboard_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'FrickTrader Dashboard'
    })