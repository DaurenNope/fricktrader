#!/usr/bin/env python3
"""
Real Data Service - Connects dashboard to actual trading systems
No more hardcoded data - everything comes from real sources
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Any
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

class RealDataService:
    """Service that provides real trading data from actual systems"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.trade_logic_db = self.project_root / "src" / "web_ui" / "trade_logic.db"
        self.data_warehouse_db = self.project_root / "data_warehouse.db"

        # Initialize live market provider
        try:
            from src.market_data.live_market_provider import live_market
            self.market_provider = live_market
            logger.info("✅ Connected to live market data provider")
        except ImportError as e:
            logger.error(f"❌ Failed to import live market provider: {e}")
            self.market_provider = None

    def get_real_portfolio_data(self) -> Dict[str, Any]:
        """Get actual portfolio data from trading engine or database"""
        try:
            # Try to connect to live trading engine first
            try:
                from src.live_trading_engine import LiveTradingEngine
                engine = LiveTradingEngine()
                portfolio_status = engine.get_portfolio_status()

                if portfolio_status:
                    return {
                        'total_value': portfolio_status.get('current_capital', 0),
                        'today_pnl': portfolio_status.get('total_pnl', 0),
                        'today_pnl_percent': portfolio_status.get('total_return_pct', 0),
                        'positions': portfolio_status.get('active_positions', 0),
                        'completed_trades': portfolio_status.get('completed_trades', 0),
                        'win_rate': portfolio_status.get('win_rate', 0),
                        'data_source': 'Live Trading Engine'
                    }
            except Exception as e:
                logger.warning(f"Live trading engine not available: {e}")

            # Fallback to database data
            if self.data_warehouse_db.exists():
                with sqlite3.connect(self.data_warehouse_db) as conn:
                    cursor = conn.cursor()

                    # Try to get portfolio summary from database
                    cursor.execute("""
                        SELECT total_value, today_pnl, win_rate, active_positions
                        FROM portfolio_summary
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """)

                    result = cursor.fetchone()
                    if result:
                        return {
                            'total_value': result[0] or 0,
                            'today_pnl': result[1] or 0,
                            'today_pnl_percent': (result[1] / result[0] * 100) if result[0] > 0 else 0,
                            'positions': result[3] or 0,
                            'win_rate': result[2] or 0,
                            'data_source': 'Database'
                        }

            logger.warning("No portfolio data available from any source")
            return {
                'total_value': 0,
                'today_pnl': 0,
                'today_pnl_percent': 0,
                'positions': 0,
                'win_rate': 0,
                'data_source': 'No Data Available'
            }

        except Exception as e:
            logger.error(f"Error getting portfolio data: {e}")
            return {'error': str(e)}

    def get_real_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get real market data from live providers"""
        try:
            if self.market_provider:
                # Get live price data
                price_data = self.market_provider.get_symbol_price(symbol)
                if price_data:
                    return {
                        'symbol': symbol,
                        'price': price_data.get('price', 0),
                        'change_24h_percent': price_data.get('change_24h_percent', 0),
                        'volume_24h': price_data.get('volume_24h', 0),
                        'high_24h': price_data.get('high_24h', 0),
                        'low_24h': price_data.get('low_24h', 0),
                        'data_source': price_data.get('source', 'Live Market Data')
                    }

            logger.warning(f"No market data available for {symbol}")
            return {
                'symbol': symbol,
                'price': 0,
                'change_24h_percent': 0,
                'volume_24h': 0,
                'data_source': 'No Market Data Available'
            }

        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return {'error': str(e)}

    def get_real_trade_decisions(self, symbol: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get actual trade decisions from database"""
        try:
            if not self.trade_logic_db.exists():
                logger.warning("Trade logic database not found")
                return []

            with sqlite3.connect(self.trade_logic_db) as conn:
                cursor = conn.cursor()

                query = """
                    SELECT pair, timestamp, technical_score, sentiment_score,
                           onchain_score, composite_score, recommendation, signal_strength
                    FROM trade_decisions
                """
                params = []

                if symbol:
                    query += " WHERE pair = ?"
                    params.append(symbol)

                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                cursor.execute(query, params)
                results = cursor.fetchall()

                decisions = []
                for row in results:
                    decisions.append({
                        'pair': row[0],
                        'timestamp': row[1],
                        'technical_score': row[2] or 0,
                        'sentiment_score': row[3] or 0,
                        'onchain_score': row[4] or 0,
                        'composite_score': row[5] or 0,
                        'recommendation': row[6] or 'HOLD',
                        'signal_strength': row[7] or 0,
                        'data_source': 'Trade Logic Database'
                    })

                return decisions

        except Exception as e:
            logger.error(f"Error getting trade decisions: {e}")
            return []

    def get_real_technical_indicators(self, symbol: str) -> Dict[str, Any]:
        """Get real technical indicators from database"""
        try:
            if not self.trade_logic_db.exists():
                logger.warning("Trade logic database not found")
                return {}

            with sqlite3.connect(self.trade_logic_db) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT rsi, macd, macd_signal, ema_20, ema_50,
                           volume_ratio, atr_percent, technical_score
                    FROM technical_indicators
                    WHERE pair = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (symbol,))

                result = cursor.fetchone()
                if result:
                    return {
                        'rsi': result[0] or 0,
                        'macd': result[1] or 0,
                        'macd_signal': result[2] or 0,
                        'ema_20': result[3] or 0,
                        'ema_50': result[4] or 0,
                        'volume_ratio': result[5] or 1,
                        'atr_percent': result[6] or 0,
                        'technical_score': result[7] or 0,
                        'data_source': 'Technical Indicators Database'
                    }

                logger.warning(f"No technical indicators found for {symbol}")
                return {}

        except Exception as e:
            logger.error(f"Error getting technical indicators: {e}")
            return {}

    def get_real_active_positions(self) -> List[Dict[str, Any]]:
        """Get real active positions from trading engine"""
        try:
            # Try to get from live trading engine
            try:
                from src.live_trading_engine import LiveTradingEngine
                engine = LiveTradingEngine()

                positions = []
                if hasattr(engine, 'active_positions') and engine.active_positions:
                    for position_key, position in engine.active_positions.items():
                        # Get current market price for P&L calculation
                        current_price = 0
                        if self.market_provider:
                            market_data = self.market_provider.get_symbol_price(position.symbol)
                            if market_data:
                                current_price = market_data.get('price', 0)

                        # Calculate P&L
                        if current_price > 0:
                            if position.position_type == 'LONG':
                                pnl_pct = ((current_price - position.entry_price) / position.entry_price) * 100
                            else:  # SHORT
                                pnl_pct = ((position.entry_price - current_price) / position.entry_price) * 100
                            pnl_abs = (current_price - position.entry_price) * position.position_size
                        else:
                            pnl_pct = 0
                            pnl_abs = 0

                        positions.append({
                            'position_id': position_key,
                            'symbol': position.symbol,
                            'side': position.position_type,
                            'entry_price': position.entry_price,
                            'current_price': current_price,
                            'position_size': position.position_size,
                            'pnl_pct': round(pnl_pct, 2),
                            'pnl_abs': round(pnl_abs, 2),
                            'entry_time': position.entry_time.isoformat(),
                            'strategy': position.strategy_name,
                            'stop_loss': position.stop_loss if position.stop_loss > 0 else None,
                            'take_profit': position.take_profit if position.take_profit > 0 else None,
                            'data_source': 'Live Trading Engine'
                        })

                return positions

            except Exception as e:
                logger.warning(f"Live trading engine not available: {e}")

            # If live engine not available, return empty list with explanation
            return []

        except Exception as e:
            logger.error(f"Error getting active positions: {e}")
            return []

    def get_market_summary(self) -> Dict[str, Any]:
        """Get real market summary"""
        try:
            if self.market_provider:
                return self.market_provider.get_market_summary()
            else:
                return {
                    'total_symbols': 0,
                    'gainers': 0,
                    'losers': 0,
                    'data_source': 'No Market Provider Available'
                }
        except Exception as e:
            logger.error(f"Error getting market summary: {e}")
            return {'error': str(e)}

# Global instance
real_data = RealDataService()
