"""
Mean Reversion Strategy - Buys oversold and sells overbought conditions
Entry: RSI oversold + Bollinger Band bounce
Exit: RSI overbought or price target
"""

import talib.abstract as ta
from freqtrade.strategy import IStrategy, DecimalParameter
from pandas import DataFrame
import logging

logger = logging.getLogger(__name__)

class MeanReversionStrategy(IStrategy):
    INTERFACE_VERSION = 3
    
    # Strategy parameters
    minimal_roi = {
        "120": 0.01,
        "60": 0.03,
        "0": 0.06
    }
    
    stoploss = -0.05
    timeframe = '1h'
    
    # Hyperparameters
    rsi_period = DecimalParameter(10, 20, default=14, space="buy")
    rsi_oversold = DecimalParameter(20, 35, default=30, space="buy")
    rsi_overbought = DecimalParameter(65, 80, default=70, space="sell")
    bb_period = DecimalParameter(15, 25, default=20, space="buy")
    bb_std = DecimalParameter(1.8, 2.5, default=2.0, space="buy")
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=int(self.rsi_period.value))
        
        # Bollinger Bands
        bb = ta.BBANDS(dataframe, 
                      timeperiod=int(self.bb_period.value),
                      nbdevup=self.bb_std.value,
                      nbdevdn=self.bb_std.value)
        dataframe['bb_upper'] = bb['upperband']
        dataframe['bb_middle'] = bb['middleband']
        dataframe['bb_lower'] = bb['lowerband']
        dataframe['bb_width'] = (dataframe['bb_upper'] - dataframe['bb_lower']) / dataframe['bb_middle']
        
        # Support/Resistance levels
        dataframe['support'] = dataframe['low'].rolling(10).min()
        dataframe['resistance'] = dataframe['high'].rolling(10).max()
        
        # Distance from bands
        dataframe['price_vs_lower'] = (dataframe['close'] - dataframe['bb_lower']) / dataframe['bb_lower'] * 100
        dataframe['price_vs_upper'] = (dataframe['close'] - dataframe['bb_upper']) / dataframe['bb_upper'] * 100
        
        return dataframe
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = [
            # RSI oversold
            (dataframe['rsi'] <= self.rsi_oversold.value),
            (dataframe['rsi'] > dataframe['rsi'].shift(1)),  # RSI turning up
            
            # Price near or below lower Bollinger Band
            (dataframe['close'] <= dataframe['bb_lower'] * 1.02),
            
            # Bollinger Bands not too narrow (avoid low volatility)
            (dataframe['bb_width'] > 0.02),
            
            # Price above recent support
            (dataframe['close'] > dataframe['support'] * 0.995)
        ]
        
        if all(conditions):
            pair = metadata.get('pair', 'Unknown')
            rsi_val = dataframe['rsi'].iloc[-1]
            price = dataframe['close'].iloc[-1]
            bb_lower = dataframe['bb_lower'].iloc[-1]
            distance_from_band = dataframe['price_vs_lower'].iloc[-1]
            
            logger.info(f"📈 MEAN REVERSION ENTRY for {pair}: "
                       f"RSI={rsi_val:.1f} (oversold), Price={price:.4f}, "
                       f"BB Lower={bb_lower:.4f}, Distance={distance_from_band:.2f}%")
        
        dataframe.loc[
            (dataframe['rsi'] <= self.rsi_oversold.value) &
            (dataframe['rsi'] > dataframe['rsi'].shift(1)) &
            (dataframe['close'] <= dataframe['bb_lower'] * 1.02) &
            (dataframe['bb_width'] > 0.02) &
            (dataframe['close'] > dataframe['support'] * 0.995),
            'enter_long'] = 1
            
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        exit_conditions = [
            # RSI overbought OR
            (dataframe['rsi'] >= self.rsi_overbought.value),
            # Price reached upper Bollinger Band
            (dataframe['close'] >= dataframe['bb_upper'] * 0.98)
        ]
        
        # Use OR logic for exit conditions
        rsi_exit = dataframe['rsi'] >= self.rsi_overbought.value
        bb_exit = dataframe['close'] >= dataframe['bb_upper'] * 0.98
        
        if rsi_exit.iloc[-1] or bb_exit.iloc[-1]:
            pair = metadata.get('pair', 'Unknown')
            rsi_val = dataframe['rsi'].iloc[-1]
            price = dataframe['close'].iloc[-1]
            bb_upper = dataframe['bb_upper'].iloc[-1]
            
            exit_reason = "RSI Overbought" if rsi_exit.iloc[-1] else "BB Upper Touch"
            logger.info(f"📉 MEAN REVERSION EXIT for {pair}: "
                       f"{exit_reason} - RSI={rsi_val:.1f}, "
                       f"Price={price:.4f}, BB Upper={bb_upper:.4f}")
        
        dataframe.loc[
            (dataframe['rsi'] >= self.rsi_overbought.value) |
            (dataframe['close'] >= dataframe['bb_upper'] * 0.98),
            'exit_long'] = 1
            
        return dataframe
    
    def custom_entry_price(self, pair: str, current_time, proposed_rate: float, **kwargs) -> float:
        logger.info(f"🎯 MEAN REVERSION ENTRY for {pair} at {proposed_rate:.4f} "
                   f"(Expecting bounce from oversold)")
        return proposed_rate
    
    def custom_exit_price(self, pair: str, trade, current_time, proposed_rate: float, **kwargs) -> float:
        profit_ratio = trade.calc_profit_ratio(proposed_rate)
        logger.info(f"🎯 MEAN REVERSION EXIT for {pair} at {proposed_rate:.4f} "
                   f"(Profit: {profit_ratio*100:.2f}% - Mean reversion complete)")
        return proposed_rate