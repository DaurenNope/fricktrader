"""
Custom Strategy: my_rsi_strategy
Created: 2025-09-06 16:33:12

This is your custom trading strategy template.
Implement your logic in the execute_strategy function below.
"""

import pandas as pd
import numpy as np
from typing import Dict, List

def execute_strategy(data: pd.DataFrame, initial_capital: float, **params) -> Dict:
    """
    Your custom trading strategy implementation
    
    Args:
        data: DataFrame with OHLCV data and technical indicators
        initial_capital: Starting capital amount
        **params: Custom parameters for your strategy
    
    Available data columns include:
        - Basic OHLCV: open, high, low, close, volume
        - Moving Averages: sma_10, sma_20, sma_50, ema_12, ema_26
        - MACD: macd, macd_signal, macd_histogram  
        - RSI: rsi, rsi_7
        - Bollinger Bands: bb_upper, bb_lower, bb_middle, bb_width, bb_position
        - ATR: atr, atr_pct
        - Stochastic: stoch_k, stoch_d
        - Williams %R: williams_r
        - CCI: cci
        - Volume: volume_sma, volume_ratio
        - Momentum: roc_10, roc_20
        - Support/Resistance: resistance, support, mid_point
        - Volatility: vol_10, vol_20, vol_ratio
        - Patterns: higher_high, lower_low, doji, gap_up, gap_down
    
    Returns:
        Dict containing:
            - trades: List of trade dictionaries
            - equity_curve: List of equity points over time
            - risk_metrics: Dictionary of risk metrics
            - performance_attribution: Dictionary of performance stats
    """
    
    # Example strategy parameters (customize these!)
    entry_rsi_threshold = params.get('entry_rsi', 30)
    exit_rsi_threshold = params.get('exit_rsi', 70)
    stop_loss_pct = params.get('stop_loss', 0.02)
    take_profit_pct = params.get('take_profit', 0.05)
    
    # Initialize tracking variables
    trades = []
    equity_curve = []
    position = 0  # 0 = no position, 1 = long, -1 = short
    entry_price = 0
    capital = initial_capital
    
    # Strategy loop through historical data
    for i in range(50, len(data)):  # Start after indicators are calculated
        current = data.iloc[i]
        price = current['close']
        rsi = current['rsi']
        
        # === ENTRY LOGIC (CUSTOMIZE THIS!) ===
        if position == 0:  # No position
            # Example: Long entry when RSI oversold and price above SMA
            if (rsi <= entry_rsi_threshold and 
                price > current['sma_20'] and
                current['volume_ratio'] > 1.2):  # High volume confirmation
                
                position = 1
                entry_price = price
                position_size = capital * 0.1  # Risk 10% of capital
                
        # === EXIT LOGIC (CUSTOMIZE THIS!) ===
        elif position != 0:
            exit_signal = False
            exit_reason = ""
            
            if position == 1:  # Long position
                # Take profit
                if price >= entry_price * (1 + take_profit_pct):
                    exit_signal = True
                    exit_reason = "Take profit"
                # Stop loss
                elif price <= entry_price * (1 - stop_loss_pct):
                    exit_signal = True
                    exit_reason = "Stop loss"
                # Technical exit
                elif rsi >= exit_rsi_threshold:
                    exit_signal = True
                    exit_reason = "RSI overbought"
            
            if exit_signal:
                # Calculate P&L
                if position == 1:
                    pnl = position_size * (price - entry_price) / entry_price
                else:
                    pnl = position_size * (entry_price - price) / entry_price
                
                capital += pnl
                
                # Record trade
                trades.append({
                    'entry_date': data.index[i-10].strftime('%Y-%m-%d %H:%M'),
                    'exit_date': current.name.strftime('%Y-%m-%d %H:%M'),
                    'type': 'LONG' if position == 1 else 'SHORT',
                    'entry_price': round(entry_price, 2),
                    'exit_price': round(price, 2),
                    'pnl': round(pnl, 2),
                    'return_pct': round(pnl / position_size * 100, 2) if position_size > 0 else 0,
                    'exit_reason': exit_reason
                })
                
                # Reset position
                position = 0
                entry_price = 0
        
        # Track equity curve
        equity_curve.append({
            'date': current.name.strftime('%Y-%m-%d'),
            'equity': round(capital, 2)
        })
    
    # Calculate performance metrics
    daily_returns = pd.Series([point['equity'] for point in equity_curve]).pct_change().dropna()
    
    # Risk metrics calculation
    risk_metrics = {
        'max_drawdown': calculate_max_drawdown([point['equity'] for point in equity_curve]),
        'sharpe_ratio': calculate_sharpe_ratio(daily_returns),
        'sortino_ratio': calculate_sortino_ratio(daily_returns),
        'volatility': daily_returns.std() * np.sqrt(252) if len(daily_returns) > 0 else 0,
        'var_95': np.percentile(daily_returns, 5) if len(daily_returns) > 0 else 0
    }
    
    # Performance attribution
    performance_attribution = {
        'strategy_alpha': daily_returns.mean() * 252 if len(daily_returns) > 0 else 0,
        'win_streak': calculate_win_streak(trades),
        'loss_streak': calculate_loss_streak(trades),
        'profit_factor': calculate_profit_factor(trades)
    }
    
    return {
        'trades': trades,
        'equity_curve': equity_curve,
        'risk_metrics': risk_metrics,
        'performance_attribution': performance_attribution
    }

# Helper functions for metrics calculation
def calculate_max_drawdown(equity_curve: List[float]) -> float:
    if not equity_curve:
        return 0
    peak = equity_curve[0]
    max_dd = 0
    for value in equity_curve:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak * 100
        max_dd = max(max_dd, drawdown)
    return max_dd

def calculate_sharpe_ratio(returns: pd.Series) -> float:
    if len(returns) == 0 or returns.std() == 0:
        return 0
    return (returns.mean() / returns.std()) * np.sqrt(252)

def calculate_sortino_ratio(returns: pd.Series) -> float:
    if len(returns) == 0:
        return 0.0
    downside_returns = returns[returns < 0]
    if len(downside_returns) == 0:
        return 99.0 if returns.mean() > 0 else 0.0
    downside_std = downside_returns.std()
    if downside_std == 0:
        return 0.0
    return min((returns.mean() / downside_std) * np.sqrt(252), 99.0)

def calculate_win_streak(trades: List[Dict]) -> int:
    if not trades:
        return 0
    max_streak = current_streak = 0
    for trade in trades:
        if trade['return_pct'] > 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    return max_streak

def calculate_loss_streak(trades: List[Dict]) -> int:
    if not trades:
        return 0
    max_streak = current_streak = 0
    for trade in trades:
        if trade['return_pct'] <= 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    return max_streak

def calculate_profit_factor(trades: List[Dict]) -> float:
    if not trades:
        return 0.0
    gross_profit = sum(t['pnl'] for t in trades if t['pnl'] > 0)
    gross_loss = sum(abs(t['pnl']) for t in trades if t['pnl'] < 0)
    if gross_loss == 0:
        return 999.0 if gross_profit > 0 else 0.0
    return min(gross_profit / gross_loss, 999.0)
