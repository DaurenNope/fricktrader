"""
Breakout Strategy - Trades breakouts from consolidation ranges
Entry: Price breaks above resistance with volume
Exit: Momentum fades or support breaks
"""

import talib.abstract as ta
from freqtrade.strategy import IStrategy, DecimalParameter
from pandas import DataFrame
import logging

logger = logging.getLogger(__name__)

class BreakoutStrategy(IStrategy):
    INTERFACE_VERSION = 3
    
    # Strategy parameters
    minimal_roi = {
        "40": 0.02,
        "20": 0.04,
        "0": 0.08
    }
    
    stoploss = -0.06
    timeframe = '1h'
    
    # Hyperparameters
    atr_period = DecimalParameter(10, 20, default=14, space="buy")
    volume_factor = DecimalParameter(1.2, 2.0, default=1.5, space="buy")
    resistance_lookback = DecimalParameter(15, 25, default=20, space="buy")
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # ATR for volatility
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=int(self.atr_period.value))
        
        # Support and Resistance
        dataframe['resistance'] = dataframe['high'].rolling(int(self.resistance_lookback.value)).max()
        dataframe['support'] = dataframe['low'].rolling(int(self.resistance_lookback.value)).min()
        
        # Range size
        dataframe['range_size'] = (dataframe['resistance'] - dataframe['support']) / dataframe['close'] * 100
        
        # Volume indicators
        dataframe['volume_sma'] = ta.SMA(dataframe['volume'], timeperiod=20)
        dataframe['volume_ratio'] = dataframe['volume'] / dataframe['volume_sma']
        
        # Consolidation detection
        dataframe['consolidation'] = (dataframe['range_size'] < 5.0) & (dataframe['range_size'] > 1.0)
        
        # Price position in range
        dataframe['price_position'] = (dataframe['close'] - dataframe['support']) / (dataframe['resistance'] - dataframe['support']) * 100
        
        # Momentum after breakout
        dataframe['breakout_momentum'] = dataframe['close'].pct_change(periods=3) * 100
        
        return dataframe
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = [
            # Price breaks above resistance
            (dataframe['close'] > dataframe['resistance'].shift(1)),
            (dataframe['close'].shift(1) <= dataframe['resistance'].shift(1)),
            
            # Was in consolidation recently
            (dataframe['consolidation'].shift(1) == True),
            
            # Strong volume on breakout
            (dataframe['volume_ratio'] >= self.volume_factor.value),
            
            # Sufficient range size (not micro-breakout)
            (dataframe['range_size'] >= 2.0),
            
            # Strong momentum
            (dataframe['breakout_momentum'] > 0.5)
        ]
        
        if all(conditions):
            pair = metadata.get('pair', 'Unknown')
            price = dataframe['close'].iloc[-1]
            resistance = dataframe['resistance'].iloc[-1]
            volume_ratio = dataframe['volume_ratio'].iloc[-1]
            range_size = dataframe['range_size'].iloc[-1]
            momentum = dataframe['breakout_momentum'].iloc[-1]
            
            logger.info(f"⚡ BREAKOUT ENTRY for {pair}: "
                       f"Price={price:.4f} broke Resistance={resistance:.4f}, "
                       f"Volume={volume_ratio:.1f}x, Range={range_size:.2f}%, "
                       f"Momentum={momentum:.2f}%")
        
        dataframe.loc[
            (dataframe['close'] > dataframe['resistance'].shift(1)) &
            (dataframe['close'].shift(1) <= dataframe['resistance'].shift(1)) &
            (dataframe['consolidation'].shift(1) == True) &
            (dataframe['volume_ratio'] >= self.volume_factor.value) &
            (dataframe['range_size'] >= 2.0) &
            (dataframe['breakout_momentum'] > 0.5),
            'enter_long'] = 1
            
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        exit_conditions = [
            # Price falls back below previous resistance (now support)
            (dataframe['close'] < dataframe['resistance'].shift(5) * 0.995),
            # OR momentum turns significantly negative
            (dataframe['breakout_momentum'] < -1.0)
        ]
        
        # Use OR logic for exit conditions
        support_break = dataframe['close'] < dataframe['resistance'].shift(5) * 0.995
        momentum_fade = dataframe['breakout_momentum'] < -1.0
        
        if support_break.iloc[-1] or momentum_fade.iloc[-1]:
            pair = metadata.get('pair', 'Unknown')
            price = dataframe['close'].iloc[-1]
            prev_resistance = dataframe['resistance'].shift(5).iloc[-1]
            momentum = dataframe['breakout_momentum'].iloc[-1]
            
            exit_reason = "Support Break" if support_break.iloc[-1] else "Momentum Fade"
            logger.info(f"🔻 BREAKOUT EXIT for {pair}: "
                       f"{exit_reason} - Price={price:.4f}, "
                       f"Prev Resistance={prev_resistance:.4f}, "
                       f"Momentum={momentum:.2f}%")
        
        dataframe.loc[
            (dataframe['close'] < dataframe['resistance'].shift(5) * 0.995) |
            (dataframe['breakout_momentum'] < -1.0),
            'exit_long'] = 1
            
        return dataframe
    
    def custom_entry_price(self, pair: str, current_time, proposed_rate: float, **kwargs) -> float:
        logger.info(f"🚀 BREAKOUT ENTRY for {pair} at {proposed_rate:.4f} "
                   f"(Riding momentum breakout)")
        return proposed_rate
    
    def custom_exit_price(self, pair: str, trade, current_time, proposed_rate: float, **kwargs) -> float:
        profit_ratio = trade.calc_profit_ratio(proposed_rate)
        logger.info(f"🚀 BREAKOUT EXIT for {pair} at {proposed_rate:.4f} "
                   f"(Profit: {profit_ratio*100:.2f}% - Breakout complete)")
        return proposed_rate