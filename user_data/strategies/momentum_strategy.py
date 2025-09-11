"""
Momentum Strategy - Rides trending moves with MACD and momentum indicators
Entry: MACD bullish crossover + strong momentum
Exit: MACD bearish crossover or trailing stop
"""

import talib.abstract as ta
from freqtrade.strategy import IStrategy, DecimalParameter
from pandas import DataFrame
import logging

logger = logging.getLogger(__name__)

class MomentumStrategy(IStrategy):
    INTERFACE_VERSION = 3
    
    # Strategy parameters
    minimal_roi = {
        "60": 0.01,
        "30": 0.02, 
        "0": 0.04
    }
    
    stoploss = -0.08
    timeframe = '1h'
    
    # Hyperparameters
    macd_fast = DecimalParameter(8, 16, default=12, space="buy")
    macd_slow = DecimalParameter(20, 30, default=26, space="buy")
    macd_signal = DecimalParameter(7, 12, default=9, space="buy")
    momentum_period = DecimalParameter(10, 20, default=14, space="buy")
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # MACD
        macd = ta.MACD(dataframe, 
                      fastperiod=int(self.macd_fast.value),
                      slowperiod=int(self.macd_slow.value), 
                      signalperiod=int(self.macd_signal.value))
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']
        
        # Momentum
        dataframe['momentum'] = ta.MOM(dataframe, timeperiod=int(self.momentum_period.value))
        
        # Volume
        dataframe['volume_sma'] = ta.SMA(dataframe['volume'], timeperiod=20)
        
        # Price action
        dataframe['price_change'] = dataframe['close'].pct_change(periods=4) * 100
        
        return dataframe
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = [
            # MACD bullish crossover
            (dataframe['macd'] > dataframe['macdsignal']),
            (dataframe['macd'].shift(1) <= dataframe['macdsignal'].shift(1)),
            
            # Strong momentum
            (dataframe['momentum'] > 0),
            (dataframe['momentum'] > dataframe['momentum'].shift(1)),
            
            # Volume confirmation
            (dataframe['volume'] > dataframe['volume_sma']),
            
            # Price moving up
            (dataframe['price_change'] > 1.0)
        ]
        
        if all(conditions):
            pair = metadata.get('pair', 'Unknown')
            macd_val = dataframe['macd'].iloc[-1]
            momentum_val = dataframe['momentum'].iloc[-1]
            price_change = dataframe['price_change'].iloc[-1]
            
            logger.info(f"🚀 MOMENTUM ENTRY SIGNAL for {pair}: "
                       f"MACD={macd_val:.4f}, Momentum={momentum_val:.2f}, "
                       f"Price Change={price_change:.2f}%, Volume Above Average")
        
        dataframe.loc[
            (dataframe['macd'] > dataframe['macdsignal']) &
            (dataframe['macd'].shift(1) <= dataframe['macdsignal'].shift(1)) &
            (dataframe['momentum'] > 0) &
            (dataframe['momentum'] > dataframe['momentum'].shift(1)) &
            (dataframe['volume'] > dataframe['volume_sma']) &
            (dataframe['price_change'] > 1.0),
            'enter_long'] = 1
            
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        exit_conditions = [
            # MACD bearish crossover
            (dataframe['macd'] < dataframe['macdsignal']),
            (dataframe['macd'].shift(1) >= dataframe['macdsignal'].shift(1))
        ]
        
        if all(exit_conditions):
            pair = metadata.get('pair', 'Unknown')
            macd_val = dataframe['macd'].iloc[-1]
            momentum_val = dataframe['momentum'].iloc[-1]
            
            logger.info(f"🛑 MOMENTUM EXIT SIGNAL for {pair}: "
                       f"MACD Bearish Crossover - MACD={macd_val:.4f}, "
                       f"Momentum={momentum_val:.2f}")
        
        dataframe.loc[
            (dataframe['macd'] < dataframe['macdsignal']) &
            (dataframe['macd'].shift(1) >= dataframe['macdsignal'].shift(1)),
            'exit_long'] = 1
            
        return dataframe
    
    def custom_entry_price(self, pair: str, current_time, proposed_rate: float, **kwargs) -> float:
        logger.info(f"💰 MOMENTUM ENTRY for {pair} at {proposed_rate:.4f}")
        return proposed_rate
    
    def custom_exit_price(self, pair: str, trade, current_time, proposed_rate: float, **kwargs) -> float:
        profit_ratio = trade.calc_profit_ratio(proposed_rate)
        logger.info(f"💸 MOMENTUM EXIT for {pair} at {proposed_rate:.4f} "
                   f"(Profit: {profit_ratio*100:.2f}%)")
        return proposed_rate