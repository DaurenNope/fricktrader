"""
Signal Execution Engine - Automated Trading with Risk Management
Executes signals with sophisticated entry/exit logic and position management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from advanced_signal_engine import TradingSignal, SignalType, SignalStrength

logger = logging.getLogger(__name__)

class PositionStatus(Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    PARTIAL_CLOSE = "PARTIAL_CLOSE"
    CLOSED = "CLOSED"
    STOPPED_OUT = "STOPPED_OUT"

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"

@dataclass
class Position:
    id: str
    symbol: str
    signal: TradingSignal
    status: PositionStatus
    entry_price: float
    current_price: float
    quantity: float
    unrealized_pnl: float
    realized_pnl: float
    stop_loss_price: float
    trailing_stop_distance: float
    take_profit_levels: List[Tuple[float, float]]  # (price, quantity_to_close)
    entry_time: datetime
    last_update: datetime
    exit_reasons: List[str]
    max_profit: float
    max_loss: float
    
    def to_dict(self) -> Dict:
        return asdict(self)

class SignalExecutionEngine:
    """
    Advanced signal execution with automated position management
    """
    
    def __init__(self):
        self.active_positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self.execution_history: List[Dict] = []
        self.portfolio_balance = 100000.0  # Starting balance
        self.max_position_size = 0.1  # Max 10% per position
        self.max_total_exposure = 0.5  # Max 50% total exposure
        self.risk_per_trade = 0.02  # Max 2% risk per trade
        
    # =============================================================================
    # 1. SIGNAL EXECUTION SYSTEM
    # =============================================================================
    
    async def process_signals(self, signals: List[TradingSignal]) -> List[Dict]:
        """
        Process and execute trading signals with risk management
        """
        execution_results = []
        
        for signal in signals:
            try:
                # Risk assessment
                if not await self._assess_signal_risk(signal):
                    execution_results.append({
                        'signal': signal,
                        'action': 'REJECTED',
                        'reason': 'Risk limits exceeded',
                        'timestamp': datetime.now()
                    })
                    continue
                
                # Position sizing
                position_size = await self._calculate_position_size(signal)
                
                if position_size == 0:
                    execution_results.append({
                        'signal': signal,
                        'action': 'REJECTED',
                        'reason': 'Position size too small',
                        'timestamp': datetime.now()
                    })
                    continue
                
                # Execute the signal
                execution_result = await self._execute_signal(signal, position_size)
                execution_results.append(execution_result)
                
            except Exception as e:
                logger.error(f"Error processing signal for {signal.symbol}: {e}")
                execution_results.append({
                    'signal': signal,
                    'action': 'ERROR',
                    'reason': str(e),
                    'timestamp': datetime.now()
                })
        
        return execution_results
    
    async def _assess_signal_risk(self, signal: TradingSignal) -> bool:
        """
        Assess if signal meets risk management criteria
        """
        try:
            # Check confidence threshold
            if signal.confidence < 0.6:
                logger.info(f"Signal rejected: Low confidence {signal.confidence:.2f}")
                return False
            
            # Check risk-reward ratio
            if signal.risk_reward_ratio < 1.5:
                logger.info(f"Signal rejected: Poor R:R ratio {signal.risk_reward_ratio:.2f}")
                return False
            
            # Check current exposure
            current_exposure = sum(pos.quantity * pos.current_price for pos in self.active_positions.values())
            exposure_ratio = current_exposure / self.portfolio_balance
            
            if exposure_ratio >= self.max_total_exposure:
                logger.info(f"Signal rejected: Max exposure reached {exposure_ratio:.2%}")
                return False
            
            # Check symbol-specific limits
            existing_position = self._get_position_for_symbol(signal.symbol)
            if existing_position and existing_position.status == PositionStatus.ACTIVE:
                logger.info(f"Signal rejected: Already have position in {signal.symbol}")
                return False
            
            # Check market conditions
            if not await self._check_market_conditions():
                logger.info("Signal rejected: Poor market conditions")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error assessing signal risk: {e}")
            return False
    
    async def _calculate_position_size(self, signal: TradingSignal) -> float:
        """
        Calculate optimal position size based on risk management
        """
        try:
            # Risk-based position sizing
            stop_distance = abs(signal.entry_price - signal.stop_loss)
            risk_amount = self.portfolio_balance * self.risk_per_trade
            
            # Position size based on risk
            risk_based_size = risk_amount / stop_distance
            
            # Position size based on confidence
            confidence_multiplier = min(signal.confidence * 1.5, 1.0)
            confidence_based_size = (self.portfolio_balance * self.max_position_size) / signal.entry_price
            
            # Take the smaller of the two
            position_size = min(risk_based_size, confidence_based_size) * confidence_multiplier
            
            # Ensure minimum viable size
            min_position_value = 100  # $100 minimum
            if position_size * signal.entry_price < min_position_value:
                return 0
            
            logger.info(f"Position size calculated: {position_size:.4f} for {signal.symbol}")
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0
    
    async def _execute_signal(self, signal: TradingSignal, position_size: float) -> Dict:
        """
        Execute trading signal with proper order management
        """
        try:
            # Generate position ID
            position_id = f"{signal.symbol}_{int(datetime.now().timestamp())}"
            
            # Create position entry order
            entry_result = await self._place_entry_order(signal, position_size, position_id)
            
            if entry_result['status'] != 'FILLED':
                return {
                    'signal': signal,
                    'action': 'FAILED',
                    'reason': f"Entry order failed: {entry_result.get('error', 'Unknown error')}",
                    'timestamp': datetime.now()
                }
            
            # Create position object
            position = Position(
                id=position_id,
                symbol=signal.symbol,
                signal=signal,
                status=PositionStatus.ACTIVE,
                entry_price=entry_result['fill_price'],
                current_price=entry_result['fill_price'],
                quantity=position_size,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                stop_loss_price=signal.stop_loss,
                trailing_stop_distance=abs(entry_result['fill_price'] - signal.stop_loss),
                take_profit_levels=[(tp, position_size / len(signal.take_profit_levels)) for tp in signal.take_profit_levels],
                entry_time=datetime.now(),
                last_update=datetime.now(),
                exit_reasons=[],
                max_profit=0.0,
                max_loss=0.0
            )
            
            # Add to active positions
            self.active_positions[position_id] = position
            
            # Place stop loss order
            await self._place_stop_loss_order(position)
            
            # Place take profit orders
            await self._place_take_profit_orders(position)
            
            logger.info(f"✅ Position opened: {position_id} for {signal.symbol} at {entry_result['fill_price']}")
            
            return {
                'signal': signal,
                'action': 'EXECUTED',
                'position_id': position_id,
                'entry_price': entry_result['fill_price'],
                'quantity': position_size,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            return {
                'signal': signal,
                'action': 'ERROR',
                'reason': str(e),
                'timestamp': datetime.now()
            }
    
    # =============================================================================
    # 2. ORDER MANAGEMENT SYSTEM
    # =============================================================================
    
    async def _place_entry_order(self, signal: TradingSignal, quantity: float, position_id: str) -> Dict:
        """
        Place entry order (market or limit)
        """
        try:
            # For high-confidence signals, use market orders
            # For lower confidence, use limit orders near market price
            
            if signal.confidence >= 0.8:
                order_type = OrderType.MARKET
                order_price = signal.entry_price  # Market price
            else:
                order_type = OrderType.LIMIT
                # Limit order slightly better than current price
                if signal.signal_type == SignalType.ENTRY_LONG:
                    order_price = signal.entry_price * 0.999  # Buy slightly below
                else:
                    order_price = signal.entry_price * 1.001  # Sell slightly above
            
            # Simulate order execution
            execution_result = await self._simulate_order_execution(
                symbol=signal.symbol,
                side='BUY' if signal.signal_type == SignalType.ENTRY_LONG else 'SELL',
                quantity=quantity,
                order_type=order_type,
                price=order_price
            )
            
            # Log execution
            self.execution_history.append({
                'position_id': position_id,
                'action': 'ENTRY',
                'symbol': signal.symbol,
                'side': 'BUY' if signal.signal_type == SignalType.ENTRY_LONG else 'SELL',
                'quantity': quantity,
                'price': execution_result.get('fill_price', order_price),
                'order_type': order_type.value,
                'timestamp': datetime.now()
            })
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Error placing entry order: {e}")
            return {'status': 'FAILED', 'error': str(e)}
    
    async def _place_stop_loss_order(self, position: Position) -> Dict:
        """
        Place stop loss order for position protection
        """
        try:
            side = 'SELL' if position.signal.signal_type == SignalType.ENTRY_LONG else 'BUY'
            
            # Use stop market order for reliable execution
            result = await self._simulate_order_execution(
                symbol=position.symbol,
                side=side,
                quantity=position.quantity,
                order_type=OrderType.STOP,
                price=position.stop_loss_price
            )
            
            logger.info(f"Stop loss placed for {position.id}: {position.stop_loss_price}")
            return result
            
        except Exception as e:
            logger.error(f"Error placing stop loss: {e}")
            return {'status': 'FAILED', 'error': str(e)}
    
    async def _place_take_profit_orders(self, position: Position) -> List[Dict]:
        """
        Place multiple take profit orders for staged exits
        """
        results = []
        
        try:
            side = 'SELL' if position.signal.signal_type == SignalType.ENTRY_LONG else 'BUY'
            
            for i, (tp_price, tp_quantity) in enumerate(position.take_profit_levels):
                result = await self._simulate_order_execution(
                    symbol=position.symbol,
                    side=side,
                    quantity=tp_quantity,
                    order_type=OrderType.LIMIT,
                    price=tp_price
                )
                
                results.append(result)
                logger.info(f"Take profit {i+1} placed for {position.id}: {tp_price}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error placing take profit orders: {e}")
            return []
    
    async def _simulate_order_execution(
        self, 
        symbol: str, 
        side: str, 
        quantity: float, 
        order_type: OrderType, 
        price: float
    ) -> Dict:
        """
        Simulate order execution (replace with real exchange API)
        """
        try:
            # Mock execution with realistic slippage
            slippage_factor = 0.001 if order_type == OrderType.MARKET else 0.0
            
            if side == 'BUY':
                fill_price = price * (1 + slippage_factor)
            else:
                fill_price = price * (1 - slippage_factor)
            
            # Simulate execution delay
            await asyncio.sleep(0.1)
            
            return {
                'status': 'FILLED',
                'fill_price': fill_price,
                'fill_quantity': quantity,
                'fill_time': datetime.now(),
                'fees': quantity * fill_price * 0.001  # 0.1% fee
            }
            
        except Exception as e:
            return {
                'status': 'FAILED',
                'error': str(e)
            }
    
    # =============================================================================
    # 3. POSITION MANAGEMENT & TRAILING STOPS
    # =============================================================================
    
    async def update_positions(self, market_prices: Dict[str, float]):
        """
        Update all active positions with current prices and manage exits
        """
        for position_id, position in list(self.active_positions.items()):
            try:
                current_price = market_prices.get(position.symbol)
                if not current_price:
                    continue
                
                # Update position metrics
                old_price = position.current_price
                position.current_price = current_price
                position.last_update = datetime.now()
                
                # Calculate P&L
                if position.signal.signal_type == SignalType.ENTRY_LONG:
                    position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
                else:
                    position.unrealized_pnl = (position.entry_price - current_price) * position.quantity
                
                # Track max profit/loss
                position.max_profit = max(position.max_profit, position.unrealized_pnl)
                position.max_loss = min(position.max_loss, position.unrealized_pnl)
                
                # Update trailing stop
                await self._update_trailing_stop(position, old_price, current_price)
                
                # Check for exit conditions
                await self._check_exit_conditions(position)
                
            except Exception as e:
                logger.error(f"Error updating position {position_id}: {e}")
    
    async def _update_trailing_stop(self, position: Position, old_price: float, new_price: float):
        """
        Update trailing stop loss based on price movement
        """
        try:
            if position.signal.signal_type == SignalType.ENTRY_LONG:
                # Long position: trail stop up as price rises
                if new_price > old_price:
                    new_stop = new_price - position.trailing_stop_distance
                    if new_stop > position.stop_loss_price:
                        position.stop_loss_price = new_stop
                        logger.info(f"Trailing stop updated for {position.id}: {new_stop:.4f}")
            else:
                # Short position: trail stop down as price falls
                if new_price < old_price:
                    new_stop = new_price + position.trailing_stop_distance
                    if new_stop < position.stop_loss_price:
                        position.stop_loss_price = new_stop
                        logger.info(f"Trailing stop updated for {position.id}: {new_stop:.4f}")
                        
        except Exception as e:
            logger.error(f"Error updating trailing stop: {e}")
    
    async def _check_exit_conditions(self, position: Position):
        """
        Check various exit conditions for position
        """
        try:
            current_price = position.current_price
            
            # 1. Stop Loss Hit
            if position.signal.signal_type == SignalType.ENTRY_LONG:
                if current_price <= position.stop_loss_price:
                    await self._close_position(position, "Stop loss triggered", current_price)
                    return
            else:
                if current_price >= position.stop_loss_price:
                    await self._close_position(position, "Stop loss triggered", current_price)
                    return
            
            # 2. Take Profit Levels
            await self._check_take_profit_levels(position)
            
            # 3. Time-based exits
            await self._check_time_based_exits(position)
            
            # 4. Momentum-based exits
            await self._check_momentum_exits(position)
            
        except Exception as e:
            logger.error(f"Error checking exit conditions: {e}")
    
    async def _check_take_profit_levels(self, position: Position):
        """
        Check if take profit levels should be executed
        """
        try:
            current_price = position.current_price
            
            for i, (tp_price, tp_quantity) in enumerate(position.take_profit_levels):
                should_execute = False
                
                if position.signal.signal_type == SignalType.ENTRY_LONG:
                    should_execute = current_price >= tp_price
                else:
                    should_execute = current_price <= tp_price
                
                if should_execute and tp_quantity > 0:
                    # Execute partial close
                    await self._partial_close_position(position, tp_quantity, f"Take profit {i+1} hit", current_price)
                    
                    # Mark this TP level as executed
                    position.take_profit_levels[i] = (tp_price, 0)
                    
        except Exception as e:
            logger.error(f"Error checking take profit levels: {e}")
    
    async def _check_time_based_exits(self, position: Position):
        """
        Check time-based exit conditions
        """
        try:
            time_since_entry = datetime.now() - position.entry_time
            
            # Max hold time based on signal strength
            max_hold_hours = {
                SignalStrength.WEAK: 24,
                SignalStrength.MODERATE: 72,
                SignalStrength.STRONG: 168,  # 1 week
                SignalStrength.VERY_STRONG: 336  # 2 weeks
            }
            
            max_hold = max_hold_hours.get(position.signal.strength, 72)
            
            if time_since_entry > timedelta(hours=max_hold):
                await self._close_position(position, f"Max hold time ({max_hold}h) reached", position.current_price)
                
        except Exception as e:
            logger.error(f"Error checking time-based exits: {e}")
    
    async def _check_momentum_exits(self, position: Position):
        """
        Check momentum-based exit conditions
        """
        try:
            # Exit if profit target hit but momentum is weakening
            profit_threshold = position.entry_price * 0.05  # 5% profit
            
            if position.unrealized_pnl > profit_threshold:
                # Check if we should exit due to weakening momentum
                # This would normally involve analyzing recent price action
                # For now, use a simple trailing profit protection
                
                if position.unrealized_pnl < position.max_profit * 0.7:  # Gave back 30% of max profit
                    await self._close_position(position, "Momentum exit - profit protection", position.current_price)
                    
        except Exception as e:
            logger.error(f"Error checking momentum exits: {e}")
    
    async def _partial_close_position(self, position: Position, quantity: float, reason: str, price: float):
        """
        Partially close position (take partial profits)
        """
        try:
            if quantity >= position.quantity:
                # Close entire position
                await self._close_position(position, reason, price)
                return
            
            # Calculate realized P&L for the closed portion
            if position.signal.signal_type == SignalType.ENTRY_LONG:
                realized_pnl = (price - position.entry_price) * quantity
            else:
                realized_pnl = (position.entry_price - price) * quantity
            
            # Update position
            position.quantity -= quantity
            position.realized_pnl += realized_pnl
            position.status = PositionStatus.PARTIAL_CLOSE
            
            # Log the partial close
            self.execution_history.append({
                'position_id': position.id,
                'action': 'PARTIAL_CLOSE',
                'symbol': position.symbol,
                'quantity': quantity,
                'price': price,
                'reason': reason,
                'realized_pnl': realized_pnl,
                'timestamp': datetime.now()
            })
            
            logger.info(f"Partial close: {position.id}, qty: {quantity}, P&L: ${realized_pnl:.2f}")
            
        except Exception as e:
            logger.error(f"Error partially closing position: {e}")
    
    async def _close_position(self, position: Position, reason: str, price: float):
        """
        Completely close position
        """
        try:
            # Calculate final P&L
            if position.signal.signal_type == SignalType.ENTRY_LONG:
                final_pnl = (price - position.entry_price) * position.quantity
            else:
                final_pnl = (position.entry_price - price) * position.quantity
            
            position.realized_pnl += final_pnl
            position.status = PositionStatus.STOPPED_OUT if "stop loss" in reason.lower() else PositionStatus.CLOSED
            position.exit_reasons.append(reason)
            
            # Log the close
            self.execution_history.append({
                'position_id': position.id,
                'action': 'CLOSE',
                'symbol': position.symbol,
                'quantity': position.quantity,
                'price': price,
                'reason': reason,
                'total_pnl': position.realized_pnl,
                'timestamp': datetime.now()
            })
            
            # Move to closed positions
            self.closed_positions.append(position)
            del self.active_positions[position.id]
            
            # Update portfolio balance
            self.portfolio_balance += position.realized_pnl
            
            logger.info(f"Position closed: {position.id}, Reason: {reason}, P&L: ${position.realized_pnl:.2f}")
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
    
    # =============================================================================
    # 4. PORTFOLIO & RISK MANAGEMENT
    # =============================================================================
    
    def get_portfolio_summary(self) -> Dict:
        """
        Get comprehensive portfolio summary
        """
        try:
            total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.active_positions.values())
            total_realized_pnl = sum(pos.realized_pnl for pos in self.closed_positions)
            
            active_positions_value = sum(pos.quantity * pos.current_price for pos in self.active_positions.values())
            
            win_rate = 0
            if self.closed_positions:
                winning_trades = len([pos for pos in self.closed_positions if pos.realized_pnl > 0])
                win_rate = winning_trades / len(self.closed_positions)
            
            return {
                'portfolio_balance': self.portfolio_balance,
                'active_positions': len(self.active_positions),
                'closed_positions': len(self.closed_positions),
                'total_unrealized_pnl': total_unrealized_pnl,
                'total_realized_pnl': total_realized_pnl,
                'total_pnl': total_unrealized_pnl + total_realized_pnl,
                'portfolio_return': ((self.portfolio_balance + total_unrealized_pnl) / 100000 - 1) * 100,
                'active_positions_value': active_positions_value,
                'exposure_ratio': active_positions_value / self.portfolio_balance,
                'win_rate': win_rate,
                'positions': [pos.to_dict() for pos in self.active_positions.values()]
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {}
    
    def _get_position_for_symbol(self, symbol: str) -> Optional[Position]:
        """Get active position for symbol"""
        for position in self.active_positions.values():
            if position.symbol == symbol:
                return position
        return None
    
    async def _check_market_conditions(self) -> bool:
        """
        Check overall market conditions for trading
        """
        # Simple implementation - in practice, check VIX, market sentiment, etc.
        return True