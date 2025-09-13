
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta

signals_bp = Blueprint('signals', __name__)

# Freqtrade API configuration
FREQTRADE_API = "http://127.0.0.1:8080/api/v1"
FREQTRADE_AUTH = ("freqtrade", "freqtrade")

@signals_bp.route("/api/signals/pending")
def get_pending_signals():
    """Get pending signals for manual approval"""
    try:
        # Import and use the real approval manager
        import os
        import sys

        sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

        from approval.manual_approval_manager import ManualApprovalManager

        # Get real pending signals
        approval_manager = ManualApprovalManager()
        pending_approvals = approval_manager.get_pending_signals()

        # Convert to JSON format
        pending_signals = []
        for approval in pending_approvals:
            pending_signals.append(
                {
                    "id": approval.id,
                    "pair": approval.pair,
                    "signal_type": approval.signal_type,
                    "technical_score": approval.technical_score,
                    "onchain_score": approval.onchain_score,
                    "sentiment_score": approval.sentiment_score,
                    "composite_score": approval.composite_score,
                    "price": approval.price,
                    "timestamp": approval.timestamp.isoformat(),
                    "reasoning": approval.reasoning,
                    "expires_at": approval.expires_at.isoformat(),
                }
            )

        return jsonify(pending_signals)

    except Exception:
        # Fallback to demo data
        return jsonify(
            [
                {
                    "id": 1,
                    "pair": "BTC/USDT",
                    "signal_type": "BUY",
                    "technical_score": 0.75,
                    "onchain_score": 0.35,
                    "sentiment_score": 0.58,
                    "composite_score": 0.68,
                    "timestamp": datetime.now().isoformat(),
                    "reasoning": "Multi-signal analysis - Technical indicators strong, on-chain neutral, sentiment positive",
                }
            ]
        )


@signals_bp.route("/api/signals/<int:signal_id>/approve", methods=["POST"])
def approve_signal(signal_id):
    """Approve or reject a trading signal"""
    try:
        decision = request.json.get("decision")  # 'approve' or 'reject'
        reason = request.json.get("reason", "")

        # Import and use the real approval manager
        import os
        import sys

        sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

        from approval.manual_approval_manager import ManualApprovalManager

        # Process the decision
        approval_manager = ManualApprovalManager()

        if decision == "approve":
            success = approval_manager.approve_signal(
                signal_id, approved_by="web_user", reason=reason
            )
        else:
            success = approval_manager.reject_signal(
                signal_id, rejected_by="web_user", reason=reason
            )

        result = {
            "signal_id": signal_id,
            "decision": decision,
            "reason": reason,
            "status": "processed" if success else "failed",
            "timestamp": datetime.now().isoformat(),
        }

        return jsonify(result)

    except Exception as e:
        return jsonify(
            {
                "signal_id": signal_id,
                "decision": "error",
                "reason": str(e),
                "status": "error",
                "timestamp": datetime.now().isoformat(),
            }
        )

# Additional endpoints needed by dashboard tabs
@signals_bp.route("/api/recent-signals")
def get_recent_signals():
    """Get recent trading signals for dashboard"""
    try:
        return jsonify([
            {
                'id': 1,
                'symbol': 'BTC-USDT',
                'signal_type': 'BUY',
                'strength': 0.85,
                'price': 45250.0,
                'timestamp': datetime.now().isoformat(),
                'source': 'Smart Money Tracker'
            },
            {
                'id': 2,
                'symbol': 'ETH-USDT',
                'signal_type': 'SELL',
                'strength': 0.72,
                'price': 2350.0,
                'timestamp': (datetime.now() - timedelta(minutes=15)).isoformat(),
                'source': 'Whale Movements'
            }
        ])
    except Exception as e:
        return jsonify({'error': str(e)})

@signals_bp.route("/api/smart-money-screener")
def get_smart_money_screener():
    """Get smart money screening data"""
    try:
        return jsonify({
            'whale_movements': [
                {
                    'symbol': 'BTC',
                    'amount': 1250.5,
                    'direction': 'inflow',
                    'exchange': 'Coinbase',
                    'timestamp': datetime.now().isoformat()
                }
            ],
            'large_transactions': [
                {
                    'symbol': 'ETH',
                    'value': 25000000,
                    'transaction_hash': '0x123...',
                    'timestamp': datetime.now().isoformat()
                }
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@signals_bp.route("/api/social-sentiment/<path:symbol>")
def get_social_sentiment(symbol):
    """Get social sentiment for symbol"""
    try:
        return jsonify({
            'symbol': symbol,
            'sentiment_score': 0.65,
            'mentions_24h': 1250,
            'trending_keywords': ['bullish', 'breakout', 'moon'],
            'sources': {
                'twitter': 0.7,
                'reddit': 0.6,
                'telegram': 0.65
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@signals_bp.route("/api/followed-traders")
def get_followed_traders():
    """Get followed traders data"""
    try:
        return jsonify([
            {
                'id': 1,
                'name': 'CryptoWhale',
                'win_rate': 0.78,
                'total_followers': 125000,
                'recent_pnl': 12.5,
                'last_signal': {
                    'symbol': 'BTC-USDT',
                    'action': 'BUY',
                    'timestamp': datetime.now().isoformat()
                }
            }
        ])
    except Exception as e:
        return jsonify({'error': str(e)})

@signals_bp.route("/api/trade-logic/<path:symbol>")
def get_trade_logic(symbol):
    """Get trade logic analysis for symbol"""
    try:
        return jsonify({
            'symbol': symbol,
            'analysis': {
                'technical_score': 0.75,
                'fundamental_score': 0.65,
                'sentiment_score': 0.72,
                'overall_score': 0.71
            },
            'recommendations': [
                'Strong bullish momentum detected',
                'Volume confirmation present',
                'Support level holding at $44,500'
            ],
            'risk_assessment': 'Medium'
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@signals_bp.route("/api/timeframe-data/<path:symbol>/<timeframe>")
def get_timeframe_data(symbol, timeframe):
    """Get timeframe-specific data for symbol"""
    try:
        return jsonify({
            'symbol': symbol,
            'timeframe': timeframe,
            'ohlcv': [
                [datetime.now().timestamp() * 1000, 45000, 45300, 44900, 45250, 1250.5]
            ],
            'indicators': {
                'rsi': 65.5,
                'macd': 0.25,
                'bb_upper': 46000,
                'bb_lower': 44000
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)})
