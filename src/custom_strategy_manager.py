"""
Custom Strategy Manager
Allows users to create, test, and manage their own trading strategies
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Callable
import importlib.util
import os

class CustomStrategyManager:
    """
    Manager for user-created custom trading strategies
    """
    
    def __init__(self):
        self.custom_strategies = {}
        self.strategy_directory = "custom_strategies"
        self.ensure_strategy_directory()
        
    def ensure_strategy_directory(self):
        """Create custom strategies directory if it doesn't exist"""
        if not os.path.exists(self.strategy_directory):
            os.makedirs(self.strategy_directory)
            
        # Create __init__.py file
        init_file = os.path.join(self.strategy_directory, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write("# Custom strategies directory\n")
    
    def create_strategy_template(self, strategy_name: str) -> str:
        """Create a template file for a new strategy"""
        template = f'''"""
Custom Strategy: {strategy_name}
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is your custom trading strategy template.
Implement your logic in the execute_strategy function below.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

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
                trades.append({{
                    'entry_date': data.index[i-10].strftime('%Y-%m-%d %H:%M'),
                    'exit_date': current.name.strftime('%Y-%m-%d %H:%M'),
                    'type': 'LONG' if position == 1 else 'SHORT',
                    'entry_price': round(entry_price, 2),
                    'exit_price': round(price, 2),
                    'pnl': round(pnl, 2),
                    'return_pct': round(pnl / position_size * 100, 2) if position_size > 0 else 0,
                    'exit_reason': exit_reason
                }})
                
                # Reset position
                position = 0
                entry_price = 0
        
        # Track equity curve
        equity_curve.append({{
            'date': current.name.strftime('%Y-%m-%d'),
            'equity': round(capital, 2)
        }})
    
    # Calculate performance metrics
    daily_returns = pd.Series([point['equity'] for point in equity_curve]).pct_change().dropna()
    
    # Risk metrics calculation
    risk_metrics = {{
        'max_drawdown': calculate_max_drawdown([point['equity'] for point in equity_curve]),
        'sharpe_ratio': calculate_sharpe_ratio(daily_returns),
        'sortino_ratio': calculate_sortino_ratio(daily_returns),
        'volatility': daily_returns.std() * np.sqrt(252) if len(daily_returns) > 0 else 0,
        'var_95': np.percentile(daily_returns, 5) if len(daily_returns) > 0 else 0
    }}
    
    # Performance attribution
    performance_attribution = {{
        'strategy_alpha': daily_returns.mean() * 252 if len(daily_returns) > 0 else 0,
        'win_streak': calculate_win_streak(trades),
        'loss_streak': calculate_loss_streak(trades),
        'profit_factor': calculate_profit_factor(trades)
    }}
    
    return {{
        'trades': trades,
        'equity_curve': equity_curve,
        'risk_metrics': risk_metrics,
        'performance_attribution': performance_attribution
    }}

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
'''
        
        # Write template file
        file_path = os.path.join(self.strategy_directory, f"{strategy_name}.py")
        with open(file_path, 'w') as f:
            f.write(template)
            
        return file_path
    
    def load_custom_strategy(self, strategy_name: str) -> Optional[Callable]:
        """Load a custom strategy from file"""
        file_path = os.path.join(self.strategy_directory, f"{strategy_name}.py")
        
        if not os.path.exists(file_path):
            return None
            
        try:
            # Load the module
            spec = importlib.util.spec_from_file_location(strategy_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get the execute_strategy function
            if hasattr(module, 'execute_strategy'):
                return module.execute_strategy
            else:
                print(f"Strategy {strategy_name} missing execute_strategy function")
                return None
                
        except Exception as e:
            print(f"Error loading strategy {strategy_name}: {e}")
            return None
    
    def list_custom_strategies(self) -> List[str]:
        """List all available custom strategies"""
        strategies = []
        if os.path.exists(self.strategy_directory):
            for file in os.listdir(self.strategy_directory):
                if file.endswith('.py') and file != '__init__.py':
                    strategies.append(file[:-3])  # Remove .py extension
        return strategies
    
    def execute_custom_strategy(self, strategy_name: str, data: pd.DataFrame, 
                              initial_capital: float, **params) -> Dict:
        """Execute a custom strategy"""
        strategy_func = self.load_custom_strategy(strategy_name)
        if strategy_func is None:
            return {
                'status': 'error',
                'error': f'Custom strategy "{strategy_name}" not found or invalid'
            }
        
        try:
            results = strategy_func(data, initial_capital, **params)
            return {
                'status': 'success',
                'results': results,
                'strategy_type': 'custom'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Error executing custom strategy: {str(e)}'
            }
    
    def validate_strategy(self, strategy_name: str) -> Dict:
        """Validate a custom strategy file"""
        strategy_func = self.load_custom_strategy(strategy_name)
        if strategy_func is None:
            return {'valid': False, 'error': 'Strategy not found or cannot be loaded'}
        
        # Basic validation - check if function signature is correct
        import inspect
        sig = inspect.signature(strategy_func)
        
        required_params = ['data', 'initial_capital']
        missing_params = [param for param in required_params if param not in sig.parameters]
        
        if missing_params:
            return {
                'valid': False, 
                'error': f'Missing required parameters: {missing_params}'
            }
        
        return {'valid': True, 'message': 'Strategy validated successfully'}

# Global instance
custom_strategy_manager = CustomStrategyManager()

# Export functions
def create_custom_strategy_template(name: str) -> str:
    return custom_strategy_manager.create_strategy_template(name)

def load_custom_strategy(name: str):
    return custom_strategy_manager.load_custom_strategy(name)

def list_custom_strategies() -> List[str]:
    return custom_strategy_manager.list_custom_strategies()

def execute_custom_strategy(name: str, data: pd.DataFrame, capital: float, **params) -> Dict:
    return custom_strategy_manager.execute_custom_strategy(name, data, capital, **params)