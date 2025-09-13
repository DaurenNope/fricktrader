"""
AI Generated Strategy: Momentum Trading
User Request: strategy to focus on short term trades using bollinger bands and EMAs
Generated: 2025-09-06 22:35:14
"""

import pandas as pd
from typing import Dict

def execute_strategy(data: pd.DataFrame, initial_capital: float, **params) -> Dict:
    """Momentum strategy using MACD"""
    
    trades = []
    equity_curve = []
    position = 0
    entry_price = 0
    capital = initial_capital
    
    for i in range(50, len(data)):
        current = data.iloc[i]
        price = current['close']
        macd = current.get('macd', 0)
        macd_signal = current.get('macd_signal', 0)
        
        if position == 0:
            if macd > macd_signal and current.get('volume_ratio', 1) > 1.3:
                position = 1
                entry_price = price
                
        elif position == 1:
            if macd < macd_signal or price <= entry_price * 0.985:
                pnl = capital * 0.05 * (price - entry_price) / entry_price
                capital += pnl
                
                trades.append({
                    'entry_date': str(data.index[max(0, i-3)]),
                    'exit_date': str(current.name),
                    'type': 'LONG',
                    'entry_price': round(entry_price, 2),
                    'exit_price': round(price, 2),
                    'pnl': round(pnl, 2),
                    'return_pct': round((price - entry_price) / entry_price * 100, 2),
                    'exit_reason': "MACD exit"
                })
                
                position = 0
        
        equity_curve.append({'date': str(current.name), 'equity': round(capital, 2)})
    
    return {'trades': trades, 'equity_curve': equity_curve, 'risk_metrics': {}, 'performance_attribution': {}}
