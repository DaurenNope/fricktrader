"""
Live Trading Engine - Execute Strategies in Real-Time
Continuously monitors markets and executes trades based on strategy signals
"""

import asyncio
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import sqlite3
from dataclasses import dataclass
from src.custom_strategy_manager import list_custom_strategies, load_custom_strategy

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Represents an open position"""
    strategy_name: str
    symbol: str
    entry_price: float
    entry_time: datetime
    position_size: float
    position_type: str  # 'LONG' or 'SHORT'
    stop_loss: float = 0.0
    take_profit: float = 0.0
    trailing_stop: float = 0.0

@dataclass
class Trade:
    """Represents a completed trade"""
    strategy_name: str
    symbol: str
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    position_size: float
    pnl: float
    return_pct: float
    trade_type: str
    exit_reason: str

class LiveTradingEngine:
    """
    Main live trading engine that manages multiple strategies
    """
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.active_positions: Dict[str, Position] = {}  # position_id -> Position
        self.completed_trades: List[Trade] = []
        self.strategy_instances = {}
        self.market_data_cache = {}
        self.running = False
        
        # Risk management
        self.max_positions = 10
        self.max_risk_per_trade = 0.02  # 2% max risk per trade
        self.max_portfolio_risk = 0.20  # 20% max portfolio risk
        
        # Initialize database for trade logging
        self.init_database()
        
        # Load available strategies
        self.load_strategies()
    
    def init_database(self):
        """Initialize SQLite database for trade logging"""
        self.db_path = "live_trades.db"
        conn = sqlite3.connect(self.db_path)
        
        # Create tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS live_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT,
                symbol TEXT,
                entry_price REAL,
                exit_price REAL,
                entry_time TEXT,
                exit_time TEXT,
                position_size REAL,
                pnl REAL,
                return_pct REAL,
                trade_type TEXT,
                exit_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS live_positions (
                id TEXT PRIMARY KEY,
                strategy_name TEXT,
                symbol TEXT,
                entry_price REAL,
                entry_time TEXT,
                position_size REAL,
                position_type TEXT,
                stop_loss REAL,
                take_profit REAL,
                trailing_stop REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized")
    
    def load_strategies(self):
        """Load all available custom strategies"""
        try:
            custom_strategies = list_custom_strategies()
            
            for strategy_name in custom_strategies:
                strategy_func = load_custom_strategy(strategy_name)
                if strategy_func:
                    self.strategy_instances[strategy_name] = strategy_func
                    logger.info(f"✅ Loaded strategy: {strategy_name}")
            
            logger.info(f"📈 Total strategies loaded: {len(self.strategy_instances)}")
            
        except Exception as e:
            logger.error(f"❌ Error loading strategies: {e}")
    
    async def get_market_data(self, symbol: str, timeframe: str = "1m", limit: int = 100) -> pd.DataFrame:
        """
        Get real-time market data for a symbol
        This is a mock implementation - replace with real API calls
        """
        try:
            # Mock data generation - replace with real API
            dates = pd.date_range(
                start=datetime.now() - timedelta(minutes=limit),
                end=datetime.now(),
                freq='1min'
            )
            
            # Generate realistic OHLCV data
            np.random.seed(int(time.time()) % 1000)
            base_price = 45000 if symbol == "BTC/USDT" else 2500
            
            data = []
            price = base_price
            
            for date in dates:
                # Random walk with slight upward bias
                change = np.random.normal(0, 0.002)
                price *= (1 + change)
                
                high = price * (1 + abs(np.random.normal(0, 0.001)))
                low = price * (1 - abs(np.random.normal(0, 0.001)))
                volume = np.random.uniform(100, 1000)
                
                data.append({
                    'timestamp': date,
                    'open': price,
                    'high': high,
                    'low': low,
                    'close': price,
                    'volume': volume
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            
            # Add technical indicators
            df = self.add_technical_indicators(df)
            
            # Cache the data
            self.market_data_cache[f"{symbol}_{timeframe}"] = df
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error getting market data for {symbol}: {e}")
            return pd.DataFrame()
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to market data"""
        if len(df) < 50:
            return df
            
        try:
            # Moving averages
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['ema_12'] = df['close'].ewm(span=12).mean()
            df['ema_26'] = df['close'].ewm(span=26).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # Bollinger Bands
            bb_period = 20
            bb_std = 2
            df['bb_middle'] = df['close'].rolling(window=bb_period).mean()
            bb_std_dev = df['close'].rolling(window=bb_period).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std_dev * bb_std)
            df['bb_lower'] = df['bb_middle'] - (bb_std_dev * bb_std)
            
            # Volume indicators
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            
            # ATR
            df['tr'] = np.maximum(
                df['high'] - df['low'],
                np.maximum(
                    abs(df['high'] - df['close'].shift(1)),
                    abs(df['low'] - df['close'].shift(1))
                )
            )
            df['atr'] = df['tr'].rolling(window=14).mean()
            df['atr_pct'] = df['atr'] / df['close'] * 100
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error adding technical indicators: {e}")
            return df
    
    def calculate_position_size(self, strategy_name: str, symbol: str, entry_price: float, 
                              stop_loss: float, risk_pct: float = 0.02) -> float:
        """Calculate position size based on risk management"""
        try:
            if stop_loss == 0:
                # If no stop loss, use 1% of capital
                return self.current_capital * 0.01
            
            # Risk per trade in dollars
            risk_dollars = self.current_capital * risk_pct
            
            # Price difference (risk per share)
            price_diff = abs(entry_price - stop_loss)
            if price_diff == 0:
                return self.current_capital * 0.01
            
            # Position size
            position_size = risk_dollars / price_diff * entry_price
            
            # Cap at maximum position size
            max_position = self.current_capital * 0.10  # 10% max per position
            position_size = min(position_size, max_position)
            
            return position_size
            
        except Exception as e:
            logger.error(f"❌ Error calculating position size: {e}")
            return self.current_capital * 0.01
    
    async def execute_strategy_signal(self, strategy_name: str, symbol: str, 
                                    market_data: pd.DataFrame) -> Optional[Dict]:
        """Execute a strategy and return trading signal"""
        try:
            strategy_func = self.strategy_instances.get(strategy_name)
            if not strategy_func:
                return None
            
            # Execute strategy on recent data
            initial_capital = 10000  # Use fixed capital for signal calculation
            result = strategy_func(market_data, initial_capital)
            
            if not result or 'trades' not in result:
                return None
            
            trades = result['trades']
            if not trades:
                return None
            
            # Get the most recent trade signal
            latest_trade = trades[-1]
            
            # Check if this is a new signal (within last few minutes)
            current_time = datetime.now()
            
            # Return signal information
            return {
                'strategy_name': strategy_name,
                'symbol': symbol,
                'action': 'BUY' if latest_trade['type'] == 'LONG' else 'SELL',
                'entry_price': latest_trade['entry_price'],
                'signal_strength': len(trades),  # More trades = stronger signal
                'timestamp': current_time
            }
            
        except Exception as e:
            logger.error(f"❌ Error executing strategy {strategy_name}: {e}")
            return None
    
    def open_position(self, signal: Dict) -> bool:
        """Open a new position based on signal"""
        try:
            # Check position limits
            if len(self.active_positions) >= self.max_positions:
                logger.warning("⚠️ Maximum positions reached, skipping signal")
                return False
            
            # Check if we already have a position for this strategy+symbol
            position_key = f"{signal['strategy_name']}_{signal['symbol']}"
            if position_key in self.active_positions:
                logger.info(f"📍 Already have position for {position_key}")
                return False
            
            # Calculate position size and risk
            entry_price = signal['entry_price']
            stop_loss = entry_price * 0.97  # 3% stop loss default
            take_profit = entry_price * 1.06  # 6% take profit default
            
            position_size = self.calculate_position_size(
                signal['strategy_name'], 
                signal['symbol'], 
                entry_price, 
                stop_loss
            )
            
            # Create position
            position = Position(
                strategy_name=signal['strategy_name'],
                symbol=signal['symbol'],
                entry_price=entry_price,
                entry_time=datetime.now(),
                position_size=position_size,
                position_type=signal['action'],
                stop_loss=stop_loss,
                take_profit=take_profit,
                trailing_stop=stop_loss
            )
            
            # Store position
            self.active_positions[position_key] = position
            
            # Log to database
            self.log_position_to_db(position)
            
            logger.info(f"🚀 OPENED {signal['action']} position: {signal['strategy_name']} | "
                       f"{signal['symbol']} | Size: ${position_size:.2f} | Entry: ${entry_price:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error opening position: {e}")
            return False
    
    def close_position(self, position_key: str, exit_price: float, exit_reason: str) -> bool:
        """Close an existing position"""
        try:
            if position_key not in self.active_positions:
                return False
            
            position = self.active_positions[position_key]
            
            # Calculate P&L
            if position.position_type == 'LONG':
                pnl = position.position_size * (exit_price - position.entry_price) / position.entry_price
            else:
                pnl = position.position_size * (position.entry_price - exit_price) / position.entry_price
            
            return_pct = pnl / position.position_size * 100
            
            # Update capital
            self.current_capital += pnl
            
            # Create trade record
            trade = Trade(
                strategy_name=position.strategy_name,
                symbol=position.symbol,
                entry_price=position.entry_price,
                exit_price=exit_price,
                entry_time=position.entry_time,
                exit_time=datetime.now(),
                position_size=position.position_size,
                pnl=pnl,
                return_pct=return_pct,
                trade_type=position.position_type,
                exit_reason=exit_reason
            )
            
            # Store trade
            self.completed_trades.append(trade)
            
            # Log to database
            self.log_trade_to_db(trade)
            
            # Remove position
            del self.active_positions[position_key]
            
            # Remove from position database
            self.remove_position_from_db(position_key)
            
            logger.info(f"🏁 CLOSED {position.position_type} position: {position.strategy_name} | "
                       f"{position.symbol} | P&L: ${pnl:.2f} ({return_pct:.2f}%) | Reason: {exit_reason}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error closing position {position_key}: {e}")
            return False
    
    def log_position_to_db(self, position: Position):
        """Log position to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            position_key = f"{position.strategy_name}_{position.symbol}"
            
            conn.execute('''
                INSERT OR REPLACE INTO live_positions 
                (id, strategy_name, symbol, entry_price, entry_time, position_size, 
                 position_type, stop_loss, take_profit, trailing_stop)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                position_key, position.strategy_name, position.symbol,
                position.entry_price, position.entry_time.isoformat(),
                position.position_size, position.position_type,
                position.stop_loss, position.take_profit, position.trailing_stop
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error logging position to DB: {e}")
    
    def log_trade_to_db(self, trade: Trade):
        """Log completed trade to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            conn.execute('''
                INSERT INTO live_trades 
                (strategy_name, symbol, entry_price, exit_price, entry_time, exit_time,
                 position_size, pnl, return_pct, trade_type, exit_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade.strategy_name, trade.symbol, trade.entry_price, trade.exit_price,
                trade.entry_time.isoformat(), trade.exit_time.isoformat(),
                trade.position_size, trade.pnl, trade.return_pct, 
                trade.trade_type, trade.exit_reason
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error logging trade to DB: {e}")
    
    def remove_position_from_db(self, position_key: str):
        """Remove position from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('DELETE FROM live_positions WHERE id = ?', (position_key,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Error removing position from DB: {e}")
    
    async def monitor_positions(self):
        """Monitor open positions and manage exits"""
        try:
            for position_key, position in list(self.active_positions.items()):
                # Get current market data
                market_data = await self.get_market_data(position.symbol, "1m", 50)
                if market_data.empty:
                    continue
                
                current_price = market_data['close'].iloc[-1]
                
                # Check exit conditions
                should_exit = False
                exit_reason = ""
                
                if position.position_type == 'LONG':
                    # Take profit
                    if current_price >= position.take_profit:
                        should_exit = True
                        exit_reason = "Take profit"
                    # Stop loss
                    elif current_price <= position.stop_loss:
                        should_exit = True
                        exit_reason = "Stop loss"
                    # Update trailing stop
                    else:
                        new_trailing = current_price * 0.97  # 3% trailing
                        if new_trailing > position.trailing_stop:
                            position.trailing_stop = new_trailing
                        elif current_price <= position.trailing_stop:
                            should_exit = True
                            exit_reason = "Trailing stop"
                
                else:  # SHORT position
                    if current_price <= position.take_profit:
                        should_exit = True
                        exit_reason = "Take profit"
                    elif current_price >= position.stop_loss:
                        should_exit = True
                        exit_reason = "Stop loss"
                
                # Exit if needed
                if should_exit:
                    self.close_position(position_key, current_price, exit_reason)
                    
        except Exception as e:
            logger.error(f"❌ Error monitoring positions: {e}")
    
    def get_portfolio_status(self) -> Dict:
        """Get current portfolio status"""
        try:
            total_pnl = sum(trade.pnl for trade in self.completed_trades)
            total_return_pct = total_pnl / self.initial_capital * 100
            
            active_value = sum(pos.position_size for pos in self.active_positions.values())
            
            return {
                'initial_capital': self.initial_capital,
                'current_capital': self.current_capital,
                'total_pnl': total_pnl,
                'total_return_pct': total_return_pct,
                'active_positions': len(self.active_positions),
                'active_value': active_value,
                'completed_trades': len(self.completed_trades),
                'win_rate': len([t for t in self.completed_trades if t.pnl > 0]) / len(self.completed_trades) * 100 if self.completed_trades else 0,
                'strategies_running': len(self.strategy_instances),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting portfolio status: {e}")
            return {}
    
    async def trading_loop(self):
        """Main trading loop"""
        logger.info("🚀 Starting live trading engine...")
        
        symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT", "SOL/USDT"]
        self.running = True
        
        while self.running:
            try:
                # Monitor existing positions
                await self.monitor_positions()
                
                # Look for new signals from all strategies
                for strategy_name in self.strategy_instances.keys():
                    for symbol in symbols:
                        try:
                            # Get market data
                            market_data = await self.get_market_data(symbol, "1m", 100)
                            if market_data.empty:
                                continue
                            
                            # Check for signals
                            signal = await self.execute_strategy_signal(strategy_name, symbol, market_data)
                            if signal:
                                self.open_position(signal)
                            
                        except Exception as e:
                            logger.error(f"❌ Error processing {strategy_name} for {symbol}: {e}")
                
                # Log portfolio status
                status = self.get_portfolio_status()
                logger.info(f"💰 Portfolio: ${status['current_capital']:.2f} | "
                           f"P&L: ${status['total_pnl']:.2f} ({status['total_return_pct']:.2f}%) | "
                           f"Positions: {status['active_positions']} | "
                           f"Trades: {status['completed_trades']}")
                
                # Wait before next iteration
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"❌ Error in trading loop: {e}")
                await asyncio.sleep(10)
    
    def start_trading(self):
        """Start the live trading engine"""
        asyncio.run(self.trading_loop())
    
    def stop_trading(self):
        """Stop the live trading engine"""
        self.running = False
        logger.info("🛑 Live trading engine stopped")

if __name__ == "__main__":
    # Create and start the live trading engine
    engine = LiveTradingEngine(initial_capital=10000.0)
    
    try:
        engine.start_trading()
    except KeyboardInterrupt:
        engine.stop_trading()
        logger.info("👋 Goodbye!")