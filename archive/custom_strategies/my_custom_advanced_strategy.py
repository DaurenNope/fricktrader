"""
Custom Advanced Trading Strategy
Created manually with sophisticated features
"""

import pandas as pd
import numpy as np
from typing import Dict

def execute_strategy(data: pd.DataFrame, initial_capital: float, **params) -> Dict:
    """
    Your custom sophisticated trading strategy
    """
    
    # === CUSTOM PARAMETERS ===
    rsi_entry = params.get('rsi_entry', 35)
    rsi_exit = params.get('rsi_exit', 65)
    macd_confirmation = params.get('macd_confirmation', True)
    
    # Trailing Stop Configuration
    initial_stop_pct = params.get('initial_stop', 0.03)  # 3% initial stop
    tight_stop_pct = params.get('tight_stop', 0.015)     # 1.5% tight stop
    profit_threshold = params.get('profit_threshold', 0.05)  # 5% profit to tighten
    take_profit_pct = params.get('take_profit', 0.08)    # 8% take profit
    
    # Position Sizing (ATR-based)
    base_position_size = params.get('base_position', 0.1)
    atr_multiplier = params.get('atr_multiplier', 2.0)
    
    # Volume Filter
    volume_exit_threshold = params.get('volume_exit', 0.5)  # Exit if volume drops to 50%
    
    # Initialize tracking
    trades = []
    equity_curve = []
    position = 0
    entry_price = 0
    entry_volume = 0
    capital = initial_capital
    trailing_stop = 0
    
    for i in range(50, len(data)):
        current = data.iloc[i]
        price = current['close']
        rsi = current.get('rsi', 50)
        macd = current.get('macd', 0)
        macd_signal = current.get('macd_signal', 0)
        volume_ratio = current.get('volume_ratio', 1)
        atr = current.get('atr', price * 0.02)  # 2% default ATR
        
        if position == 0:
            # === CUSTOM ENTRY LOGIC ===
            rsi_condition = rsi <= rsi_entry
            macd_bullish = macd > macd_signal if macd_confirmation else True
            volume_confirmation = volume_ratio > 1.2
            
            if rsi_condition and macd_bullish and volume_confirmation:
                position = 1
                entry_price = price
                entry_volume = volume_ratio
                
                # ATR-based position sizing
                atr_risk = atr * atr_multiplier
                risk_adjusted_size = min(base_position_size, (initial_stop_pct * price) / atr_risk)
                position_size = capital * risk_adjusted_size
                
                # Set initial trailing stop
                trailing_stop = entry_price * (1 - initial_stop_pct)
                
        elif position == 1:
            # === SOPHISTICATED EXIT LOGIC ===
            current_profit = (price - entry_price) / entry_price
            
            # Update trailing stop logic
            if current_profit >= profit_threshold:
                # Tighten stop after 5% profit
                new_stop = price * (1 - tight_stop_pct)
                trailing_stop = max(trailing_stop, new_stop)
            else:
                # Regular trailing stop
                new_stop = price * (1 - initial_stop_pct)
                trailing_stop = max(trailing_stop, new_stop)
            
            exit_signal = False
            exit_reason = ""
            
            # Take profit at 8%
            if current_profit >= take_profit_pct:
                exit_signal = True
                exit_reason = f"Take profit ({current_profit:.2%})"
            
            # Trailing stop hit
            elif price <= trailing_stop:
                exit_signal = True
                exit_reason = f"Trailing stop ({current_profit:.2%})"
            
            # RSI overbought exit
            elif rsi >= rsi_exit:
                exit_signal = True
                exit_reason = "RSI overbought"
            
            # Volume drop exit (sophisticated feature)
            elif volume_ratio < (entry_volume * volume_exit_threshold):
                exit_signal = True
                exit_reason = "Volume dried up"
            
            # MACD bearish crossover
            elif macd_confirmation and macd < macd_signal and data.iloc[i-1].get('macd', 0) >= data.iloc[i-1].get('macd_signal', 0):
                exit_signal = True
                exit_reason = "MACD bearish crossover"
            
            if exit_signal:
                pnl = position_size * (price - entry_price) / entry_price
                capital += pnl
                
                trades.append({
                    'entry_date': str(data.index[max(0, i-10)]),
                    'exit_date': str(current.name),
                    'type': 'LONG',
                    'entry_price': round(entry_price, 2),
                    'exit_price': round(price, 2),
                    'pnl': round(pnl, 2),
                    'return_pct': round(current_profit * 100, 2),
                    'position_size': round(position_size, 2),
                    'trailing_stop': round(trailing_stop, 2),
                    'entry_volume': round(entry_volume, 2),
                    'exit_volume': round(volume_ratio, 2),
                    'exit_reason': exit_reason
                })
                
                position = 0
                trailing_stop = 0
        
        # Track equity
        equity_curve.append({
            'date': str(current.name),
            'equity': round(capital, 2),
            'position': position,
            'trailing_stop': round(trailing_stop, 2) if trailing_stop > 0 else 0
        })
    
    # Calculate advanced metrics
    daily_returns = pd.Series([point['equity'] for point in equity_curve]).pct_change().dropna()
    
    risk_metrics = {
        'max_drawdown': calculate_max_drawdown([point['equity'] for point in equity_curve]),
        'sharpe_ratio': calculate_sharpe_ratio(daily_returns),
        'sortino_ratio': calculate_sortino_ratio(daily_returns),
        'volatility': daily_returns.std() * np.sqrt(252) if len(daily_returns) > 0 else 0,
        'calmar_ratio': calculate_calmar_ratio(daily_returns, [point['equity'] for point in equity_curve])
    }
    
    performance_attribution = {
        'total_trades': len(trades),
        'win_rate': len([t for t in trades if t['return_pct'] > 0]) / len(trades) * 100 if trades else 0,
        'avg_win': np.mean([t['return_pct'] for t in trades if t['return_pct'] > 0]) if trades else 0,
        'avg_loss': np.mean([t['return_pct'] for t in trades if t['return_pct'] < 0]) if trades else 0,
        'profit_factor': calculate_profit_factor(trades),
        'expectancy': sum(t['pnl'] for t in trades) / len(trades) if trades else 0
    }
    
    return {
        'trades': trades,
        'equity_curve': equity_curve,
        'risk_metrics': risk_metrics,
        'performance_attribution': performance_attribution,
        'strategy_type': 'custom_advanced'
    }

def calculate_max_drawdown(equity_curve):
    if not equity_curve:
        return 0
    peak = equity_curve[0]
    max_dd = 0
    for value in equity_curve:
        if value > peak:
            peak = value
        max_dd = max(max_dd, (peak - value) / peak * 100)
    return max_dd

def calculate_sharpe_ratio(returns):
    return (returns.mean() / returns.std()) * np.sqrt(252) if len(returns) > 0 and returns.std() > 0 else 0

def calculate_sortino_ratio(returns):
    if len(returns) == 0:
        return 0.0
    downside = returns[returns < 0]
    return min((returns.mean() / downside.std()) * np.sqrt(252), 99.0) if len(downside) > 0 else 99.0

def calculate_calmar_ratio(returns, equity_curve):
    if len(returns) == 0:
        return 0.0
    annual_return = returns.mean() * 252
    max_dd = calculate_max_drawdown(equity_curve)
    return annual_return / max_dd if max_dd > 0 else 0.0

def calculate_profit_factor(trades):
    if not trades:
        return 0.0
    gross_profit = sum(t['pnl'] for t in trades if t['pnl'] > 0)
    gross_loss = sum(abs(t['pnl']) for t in trades if t['pnl'] < 0)
    return min(gross_profit / gross_loss, 999.0) if gross_loss > 0 else (999.0 if gross_profit > 0 else 0.0)