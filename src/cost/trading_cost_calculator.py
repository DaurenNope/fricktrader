"""
Trading Cost Calculator - Realistic Cost Accounting
Implements comprehensive cost modeling including:
1. Exchange fees (maker/taker, VIP discounts)
2. Dynamic slippage based on volatility and order size
3. Funding costs for futures positions
4. Network withdrawal fees
5. Impact of order book depth
"""

import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"

class TradingSide(Enum):
    BUY = "buy"
    SELL = "sell"

@dataclass
class TradingFees:
    """Exchange fee structure"""
    maker_fee: float
    taker_fee: float
    futures_maker_fee: float
    futures_taker_fee: float
    vip_discount: float = 0.0

@dataclass
class SlippageModel:
    """Slippage parameters based on market conditions"""
    base_slippage: float
    volatility_multiplier: float
    size_impact_factor: float
    news_event_multiplier: float = 1.0
    market_hours_multiplier: float = 1.0

@dataclass
class TradeCost:
    """Complete cost breakdown for a trade"""
    exchange_fees: float
    slippage_cost: float
    funding_cost: float
    withdrawal_cost: float
    total_cost: float
    cost_percent: float
    effective_price: float
    
class TradingCostCalculator:
    """
    Comprehensive trading cost calculator for crypto markets
    
    Features:
    - Multi-exchange fee structures
    - Dynamic slippage modeling 
    - Futures funding costs
    - Order size impact
    - Market volatility adjustments
    """
    
    def __init__(self):
        # Initialize exchange fee structures
        self.exchange_fees = {
            'binance': TradingFees(
                maker_fee=0.001,    # 0.1% maker
                taker_fee=0.001,    # 0.1% taker
                futures_maker_fee=0.0002,  # 0.02% futures maker
                futures_taker_fee=0.0004   # 0.04% futures taker
            ),
            'coinbase': TradingFees(
                maker_fee=0.005,    # 0.5% maker
                taker_fee=0.005,    # 0.5% taker  
                futures_maker_fee=0.003,   # 0.3% futures maker
                futures_taker_fee=0.005    # 0.5% futures taker
            ),
            'kraken': TradingFees(
                maker_fee=0.0016,   # 0.16% maker
                taker_fee=0.0026,   # 0.26% taker
                futures_maker_fee=0.0002,  # 0.02% futures maker
                futures_taker_fee=0.0005   # 0.05% futures taker
            )
        }
        
        # Slippage models for different volatility regimes
        self.slippage_models = {
            'low_vol': SlippageModel(
                base_slippage=0.0002,        # 0.02% base
                volatility_multiplier=0.5,
                size_impact_factor=0.0001
            ),
            'normal_vol': SlippageModel(
                base_slippage=0.0003,        # 0.03% base
                volatility_multiplier=1.0,
                size_impact_factor=0.0002
            ),
            'high_vol': SlippageModel(
                base_slippage=0.0005,        # 0.05% base
                volatility_multiplier=2.0,
                size_impact_factor=0.0005
            ),
            'extreme_vol': SlippageModel(
                base_slippage=0.0015,        # 0.15% base
                volatility_multiplier=5.0,
                size_impact_factor=0.001
            )
        }
        
        # Network withdrawal fees (approximate)
        self.withdrawal_fees = {
            'BTC': {'fixed': 0.0005, 'network_fee': 0.00005},  # ~$25 + network
            'ETH': {'fixed': 0.005, 'network_fee': 0.002},     # Variable gas
            'BNB': {'fixed': 0.001, 'network_fee': 0.0001},
            'USDT': {'fixed': 1.0, 'network_fee': 0.1},       # USD equivalent
            'USDC': {'fixed': 1.0, 'network_fee': 0.1},
        }
        
        # VIP tier discounts (trading volume based)
        self.vip_discounts = {
            0: 0.00,    # No discount
            1: 0.05,    # 5% discount  
            2: 0.10,    # 10% discount
            3: 0.15,    # 15% discount
            4: 0.20,    # 20% discount
            5: 0.25     # 25% discount
        }
        
        logger.info("Trading Cost Calculator initialized")
    
    def calculate_trade_cost(self,
                           pair: str,
                           order_type: OrderType,
                           trading_side: TradingSide,
                           order_size: float,
                           price: float,
                           exchange: str = 'binance',
                           is_futures: bool = False,
                           current_volatility: float = 0.03,
                           market_impact_factor: float = 1.0,
                           vip_tier: int = 0,
                           news_event: bool = False,
                           market_hours: bool = True,
                           funding_rate: Optional[float] = None,
                           position_duration_hours: float = 24) -> TradeCost:
        """
        Calculate comprehensive trading costs for a given trade
        
        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            order_type: Market or limit order
            trading_side: Buy or sell
            order_size: Size in base currency
            price: Trade price
            exchange: Exchange name
            is_futures: Whether this is a futures trade
            current_volatility: Current market volatility (ATR%)
            market_impact_factor: Order size impact multiplier
            vip_tier: VIP tier for fee discounts
            news_event: Whether there's a major news event
            market_hours: Whether trading during active hours
            funding_rate: Funding rate for futures (if None, estimated)
            position_duration_hours: Expected holding period for futures
            
        Returns:
            TradeCost object with complete cost breakdown
        """
        
        try:
            notional_value = order_size * price
            
            # 1. Calculate exchange fees
            exchange_fees = self._calculate_exchange_fees(
                notional_value, order_type, exchange, is_futures, vip_tier
            )
            
            # 2. Calculate slippage
            slippage_cost = self._calculate_slippage_cost(
                pair, notional_value, current_volatility, market_impact_factor,
                order_type, news_event, market_hours
            )
            
            # 3. Calculate funding costs (futures only)
            funding_cost = 0.0
            if is_futures:
                funding_cost = self._calculate_funding_cost(
                    notional_value, funding_rate, position_duration_hours
                )
            
            # 4. Calculate withdrawal costs (if applicable)
            withdrawal_cost = self._estimate_withdrawal_cost(pair, order_size)
            
            # 5. Calculate total cost
            total_cost = exchange_fees + slippage_cost + funding_cost + withdrawal_cost
            cost_percent = total_cost / notional_value
            
            # 6. Calculate effective execution price
            slippage_direction = 1 if trading_side == TradingSide.BUY else -1
            price_impact = slippage_cost / order_size
            effective_price = price + (price_impact * slippage_direction)
            
            return TradeCost(
                exchange_fees=exchange_fees,
                slippage_cost=slippage_cost,
                funding_cost=funding_cost,
                withdrawal_cost=withdrawal_cost,
                total_cost=total_cost,
                cost_percent=cost_percent,
                effective_price=effective_price
            )
            
        except Exception as e:
            logger.error(f"Error calculating trade cost: {e}")
            # Return conservative high-cost estimate
            return TradeCost(
                exchange_fees=notional_value * 0.002,
                slippage_cost=notional_value * 0.001,
                funding_cost=0.0,
                withdrawal_cost=0.0,
                total_cost=notional_value * 0.003,
                cost_percent=0.003,
                effective_price=price * 1.001
            )
    
    def _calculate_exchange_fees(self,
                               notional_value: float,
                               order_type: OrderType,
                               exchange: str,
                               is_futures: bool,
                               vip_tier: int) -> float:
        """Calculate exchange fees including VIP discounts"""
        
        if exchange not in self.exchange_fees:
            logger.warning(f"Unknown exchange: {exchange}, using Binance fees")
            exchange = 'binance'
        
        fees = self.exchange_fees[exchange]
        
        # Select appropriate fee rate
        if is_futures:
            if order_type == OrderType.LIMIT:
                fee_rate = fees.futures_maker_fee
            else:
                fee_rate = fees.futures_taker_fee
        else:
            if order_type == OrderType.LIMIT:
                fee_rate = fees.maker_fee
            else:
                fee_rate = fees.taker_fee
        
        # Apply VIP discount
        vip_discount = self.vip_discounts.get(vip_tier, 0.0)
        discounted_fee_rate = fee_rate * (1 - vip_discount)
        
        return notional_value * discounted_fee_rate
    
    def _calculate_slippage_cost(self,
                               pair: str,
                               notional_value: float,
                               current_volatility: float,
                               market_impact_factor: float,
                               order_type: OrderType,
                               news_event: bool,
                               market_hours: bool) -> float:
        """Calculate dynamic slippage based on market conditions"""
        
        # Determine volatility regime
        if current_volatility < 0.015:
            vol_regime = 'low_vol'
        elif current_volatility < 0.03:
            vol_regime = 'normal_vol'
        elif current_volatility < 0.06:
            vol_regime = 'high_vol'
        else:
            vol_regime = 'extreme_vol'
        
        slippage_model = self.slippage_models[vol_regime]
        
        # Base slippage
        base_slippage = slippage_model.base_slippage
        
        # Volatility adjustment
        vol_adjustment = 1 + (current_volatility * slippage_model.volatility_multiplier)
        
        # Order size impact
        # Assume $100k is a "normal" order size
        size_impact = 1 + (notional_value / 100000) * slippage_model.size_impact_factor * market_impact_factor
        
        # Market order vs limit order
        order_type_multiplier = 1.5 if order_type == OrderType.MARKET else 1.0
        
        # News event impact
        news_multiplier = 2.0 if news_event else 1.0
        
        # Market hours impact (less liquidity outside main hours)
        hours_multiplier = 1.0 if market_hours else 1.3
        
        # Major pair adjustment (better liquidity)
        pair_adjustment = 0.8 if pair in ['BTC/USDT', 'ETH/USDT', 'BNB/USDT'] else 1.0
        
        # Calculate final slippage
        total_slippage_percent = (base_slippage * vol_adjustment * size_impact * 
                                order_type_multiplier * news_multiplier * 
                                hours_multiplier * pair_adjustment)
        
        # Cap maximum slippage
        total_slippage_percent = min(total_slippage_percent, 0.005)  # 0.5% max
        
        return notional_value * total_slippage_percent
    
    def _calculate_funding_cost(self,
                              notional_value: float,
                              funding_rate: Optional[float],
                              position_duration_hours: float) -> float:
        """Calculate futures funding costs"""
        
        if funding_rate is None:
            # Estimate funding rate based on typical ranges
            # Positive funding rate = longs pay shorts
            funding_rate = np.random.normal(0.0001, 0.0002)  # 0.01% ± 0.02%
        
        # Funding is charged every 8 hours
        funding_periods = position_duration_hours / 8
        
        total_funding_cost = abs(funding_rate) * notional_value * funding_periods
        
        return total_funding_cost
    
    def _estimate_withdrawal_cost(self, pair: str, order_size: float) -> float:
        """Estimate withdrawal costs (usually not applicable for active trading)"""
        
        base_asset = pair.split('/')[0]
        
        if base_asset in self.withdrawal_fees:
            fees = self.withdrawal_fees[base_asset]
            
            # Only apply withdrawal costs for very large positions
            # (assuming most trading doesn't involve withdrawals)
            if order_size * 50000 > 100000:  # > $100k position
                return fees['fixed'] * 50000 + fees['network_fee'] * 50000  # Convert to USD
        
        return 0.0  # Most trades don't involve immediate withdrawals
    
    def calculate_round_trip_cost(self,
                                pair: str,
                                order_size: float,
                                entry_price: float,
                                exit_price: float,
                                exchange: str = 'binance',
                                is_futures: bool = False,
                                volatility: float = 0.03,
                                position_duration_hours: float = 24) -> Dict[str, any]:
        """Calculate complete round-trip trading costs (entry + exit)"""
        
        # Entry costs
        entry_cost = self.calculate_trade_cost(
            pair=pair,
            order_type=OrderType.LIMIT,  # Assume limit orders for better fees
            trading_side=TradingSide.BUY,
            order_size=order_size,
            price=entry_price,
            exchange=exchange,
            is_futures=is_futures,
            current_volatility=volatility
        )
        
        # Exit costs
        exit_cost = self.calculate_trade_cost(
            pair=pair,
            order_type=OrderType.LIMIT,
            trading_side=TradingSide.SELL,
            order_size=order_size,
            price=exit_price,
            exchange=exchange,
            is_futures=is_futures,
            current_volatility=volatility
        )
        
        # Add futures funding costs if applicable
        funding_cost = 0.0
        if is_futures:
            notional_value = order_size * entry_price
            funding_cost = self._calculate_funding_cost(
                notional_value, None, position_duration_hours
            )
        
        # Calculate totals
        total_fees = entry_cost.exchange_fees + exit_cost.exchange_fees
        total_slippage = entry_cost.slippage_cost + exit_cost.slippage_cost
        total_funding = entry_cost.funding_cost + exit_cost.funding_cost + funding_cost
        total_cost = total_fees + total_slippage + total_funding
        
        # Gross P&L
        gross_pnl = (exit_price - entry_price) * order_size
        
        # Net P&L after costs
        net_pnl = gross_pnl - total_cost
        
        # Break-even analysis
        cost_per_unit = total_cost / order_size
        breakeven_exit_price = entry_price + cost_per_unit
        
        return {
            'gross_pnl': gross_pnl,
            'net_pnl': net_pnl,
            'total_cost': total_cost,
            'total_fees': total_fees,
            'total_slippage': total_slippage,
            'total_funding': total_funding,
            'cost_percent': total_cost / (order_size * entry_price),
            'breakeven_price': breakeven_exit_price,
            'entry_effective_price': entry_cost.effective_price,
            'exit_effective_price': exit_cost.effective_price,
            'profit_reduction': (gross_pnl - net_pnl) / abs(gross_pnl) if gross_pnl != 0 else 0
        }
    
    def get_minimum_profit_target(self,
                                pair: str,
                                order_size: float,
                                entry_price: float,
                                exchange: str = 'binance',
                                is_futures: bool = False,
                                volatility: float = 0.03,
                                target_net_return: float = 0.02) -> float:
        """Calculate minimum profit target to achieve desired net return"""
        
        # Estimate round-trip costs at entry price
        notional_value = order_size * entry_price
        
        # Entry cost
        entry_cost = self.calculate_trade_cost(
            pair, OrderType.LIMIT, TradingSide.BUY, order_size, entry_price,
            exchange, is_futures, volatility
        )
        
        # Exit cost (estimated at entry price)
        exit_cost = self.calculate_trade_cost(
            pair, OrderType.LIMIT, TradingSide.SELL, order_size, entry_price,
            exchange, is_futures, volatility
        )
        
        # Total costs
        total_cost = entry_cost.total_cost + exit_cost.total_cost
        
        # Required gross profit
        required_net_profit = notional_value * target_net_return
        required_gross_profit = required_net_profit + total_cost
        
        # Required exit price
        required_exit_price = entry_price + (required_gross_profit / order_size)
        
        # Minimum percentage move needed
        min_move_percent = (required_exit_price - entry_price) / entry_price
        
        return {
            'required_exit_price': required_exit_price,
            'min_move_percent': min_move_percent,
            'total_cost': total_cost,
            'cost_percent': total_cost / notional_value,
            'required_gross_profit': required_gross_profit,
            'target_net_profit': required_net_profit
        }
    
    def optimize_order_execution(self,
                                pair: str,
                                order_size: float,
                                price: float,
                                side: TradingSide,
                                volatility: float = 0.03,
                                urgency: str = 'normal') -> Dict[str, any]:
        """Optimize order execution strategy based on costs"""
        
        # Compare market vs limit order costs
        market_cost = self.calculate_trade_cost(
            pair, OrderType.MARKET, side, order_size, price, 
            current_volatility=volatility
        )
        
        limit_cost = self.calculate_trade_cost(
            pair, OrderType.LIMIT, side, order_size, price,
            current_volatility=volatility
        )
        
        # Calculate savings
        savings = market_cost.total_cost - limit_cost.total_cost
        savings_percent = savings / (order_size * price)
        
        # Execution recommendations
        if urgency == 'high' or volatility > 0.05:
            recommendation = 'market'
            reason = 'High urgency or volatility - prioritize execution certainty'
        elif savings_percent > 0.001:  # > 0.1% savings
            recommendation = 'limit'
            reason = f'Significant cost savings: {savings_percent:.2%}'
        else:
            recommendation = 'limit'
            reason = 'Default to limit orders for better fees'
        
        return {
            'recommended_order_type': recommendation,
            'reason': reason,
            'market_cost': market_cost.total_cost,
            'limit_cost': limit_cost.total_cost,
            'potential_savings': savings,
            'savings_percent': savings_percent,
            'market_effective_price': market_cost.effective_price,
            'limit_target_price': price
        }


# Example usage and testing
if __name__ == "__main__":
    calculator = TradingCostCalculator()
    
    print("🧮 Trading Cost Calculator Demo")
    print("=" * 40)
    
    # Example trade
    pair = "BTC/USDT"
    order_size = 0.1  # 0.1 BTC
    entry_price = 45000
    exit_price = 47000
    
    print("\n📊 Trade Example:")
    print(f"  Pair: {pair}")
    print(f"  Size: {order_size} BTC")
    print(f"  Entry: ${entry_price:,}")
    print(f"  Exit: ${exit_price:,}")
    
    # Calculate round-trip costs
    round_trip = calculator.calculate_round_trip_cost(
        pair, order_size, entry_price, exit_price
    )
    
    print("\n💰 Cost Analysis:")
    print(f"  Gross P&L: ${round_trip['gross_pnl']:,.2f}")
    print(f"  Total Costs: ${round_trip['total_cost']:,.2f}")
    print(f"  Net P&L: ${round_trip['net_pnl']:,.2f}")
    print(f"  Cost %: {round_trip['cost_percent']:.2%}")
    print(f"  Breakeven Price: ${round_trip['breakeven_price']:,.2f}")
    
    print("\n📈 Cost Breakdown:")
    print(f"  Exchange Fees: ${round_trip['total_fees']:,.2f}")
    print(f"  Slippage: ${round_trip['total_slippage']:,.2f}")
    print(f"  Funding: ${round_trip['total_funding']:,.2f}")
    
    # Minimum profit target
    min_target = calculator.get_minimum_profit_target(
        pair, order_size, entry_price, target_net_return=0.02
    )
    
    print("\n🎯 For 2% Net Return:")
    print(f"  Required Exit: ${min_target['required_exit_price']:,.2f}")
    print(f"  Min Move: {min_target['min_move_percent']:.2%}")
    
    # Order execution optimization
    optimization = calculator.optimize_order_execution(
        pair, order_size, entry_price, TradingSide.BUY
    )
    
    print("\n⚡ Execution Optimization:")
    print(f"  Recommended: {optimization['recommended_order_type'].upper()} order")
    print(f"  Reason: {optimization['reason']}")
    print(f"  Potential Savings: ${optimization['potential_savings']:.2f}")