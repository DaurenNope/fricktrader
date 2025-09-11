"""
Multi-Strategy Manager - Combines multiple strategies with detailed logging
Rotates between different strategies based on market conditions
"""

import talib.abstract as ta
from freqtrade.strategy import IStrategy, DecimalParameter
from pandas import DataFrame
import logging
import random

logger = logging.getLogger(__name__)

class MultiStrategy(IStrategy):
    INTERFACE_VERSION = 3
    
    # Strategy parameters
    minimal_roi = {
        "60": 0.01,
        "30": 0.02,
        "0": 0.04
    }
    
    stoploss = -0.08
    timeframe = '15m'
    
    # Market condition parameters
    volatility_threshold = DecimalParameter(0.02, 0.08, default=0.04, space="buy")
    trend_strength = DecimalParameter(0.5, 2.0, default=1.0, space="buy")
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # RSI for mean reversion
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        # MACD for momentum
        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']
        
        # Bollinger Bands for mean reversion
        bb = ta.BBANDS(dataframe, timeperiod=20)
        dataframe['bb_upper'] = bb['upperband']
        dataframe['bb_middle'] = bb['middleband']
        dataframe['bb_lower'] = bb['lowerband']
        
        # ATR for volatility
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        dataframe['volatility'] = dataframe['atr'] / dataframe['close']
        
        # Support/Resistance for breakouts
        dataframe['resistance'] = dataframe['high'].rolling(20).max()
        dataframe['support'] = dataframe['low'].rolling(20).min()
        
        # Volume
        dataframe['volume_sma'] = ta.SMA(dataframe['volume'], timeperiod=20)
        dataframe['volume_ratio'] = dataframe['volume'] / dataframe['volume_sma']
        
        # Market condition detection
        sma_20 = ta.SMA(dataframe['close'], timeperiod=20)
        dataframe['sma_20'] = sma_20
        dataframe['trend_direction'] = dataframe['sma_20'].pct_change(periods=5)
        dataframe['market_state'] = self.detect_market_state(dataframe)
        
        return dataframe
    
    def detect_market_state(self, dataframe: DataFrame) -> str:
        """Detect current market conditions"""
        if len(dataframe) < 20:
            return 'neutral'
            
        current_volatility = dataframe['volatility'].iloc[-1]
        trend_direction = dataframe['trend_direction'].iloc[-1]
        rsi = dataframe['rsi'].iloc[-1]
        
        if current_volatility > self.volatility_threshold.value:
            if abs(trend_direction) > 0.02:
                return 'trending_volatile'  # Good for momentum
            else:
                return 'choppy_volatile'    # Good for mean reversion
        else:
            if abs(trend_direction) > 0.01:
                return 'trending_calm'      # Good for breakout
            else:
                return 'consolidating'      # Good for mean reversion
    
    def get_active_strategy(self, dataframe: DataFrame) -> str:
        """Select strategy based on market conditions"""
        if len(dataframe) < 20:
            return 'sample'
            
        market_state = dataframe['market_state'].iloc[-1] if 'market_state' in dataframe.columns else 'neutral'
        
        if market_state == 'trending_volatile':
            return 'momentum'
        elif market_state in ['choppy_volatile', 'consolidating']:
            return 'mean_reversion'
        elif market_state == 'trending_calm':
            return 'breakout'
        else:
            return 'sample'  # Default fallback
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata.get('pair', 'Unknown')
        active_strategy = self.get_active_strategy(dataframe)
        
        if active_strategy == 'momentum':
            entry_signal = self.momentum_entry(dataframe, pair)
        elif active_strategy == 'mean_reversion':
            entry_signal = self.mean_reversion_entry(dataframe, pair)
        elif active_strategy == 'breakout':
            entry_signal = self.breakout_entry(dataframe, pair)
        else:
            entry_signal = self.sample_entry(dataframe, pair)
        
        dataframe['enter_long'] = entry_signal
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata.get('pair', 'Unknown')
        active_strategy = self.get_active_strategy(dataframe)
        
        if active_strategy == 'momentum':
            exit_signal = self.momentum_exit(dataframe, pair)
        elif active_strategy == 'mean_reversion':
            exit_signal = self.mean_reversion_exit(dataframe, pair)
        elif active_strategy == 'breakout':
            exit_signal = self.breakout_exit(dataframe, pair)
        else:
            exit_signal = self.sample_exit(dataframe, pair)
        
        dataframe['exit_long'] = exit_signal
        return dataframe
    
    def momentum_entry(self, dataframe: DataFrame, pair: str) -> int:
        """Momentum strategy entry logic"""
        condition = (
            (dataframe['macd'] > dataframe['macdsignal']) &
            (dataframe['macd'].shift(1) <= dataframe['macdsignal'].shift(1)) &
            (dataframe['volume_ratio'] > 1.2) &
            (dataframe['rsi'] > 40) & (dataframe['rsi'] < 70)
        )
        
        if condition.iloc[-1]:
            logger.info(f"🚀 MOMENTUM ENTRY for {pair}: MACD Bullish Crossover, "
                       f"RSI={dataframe['rsi'].iloc[-1]:.1f}, Volume={dataframe['volume_ratio'].iloc[-1]:.1f}x")
            return 1
        return 0
    
    def mean_reversion_entry(self, dataframe: DataFrame, pair: str) -> int:
        """Mean reversion strategy entry logic"""
        condition = (
            (dataframe['rsi'] <= 30) &
            (dataframe['close'] <= dataframe['bb_lower'] * 1.01) &
            (dataframe['volatility'] > 0.01)
        )
        
        if condition.iloc[-1]:
            logger.info(f"📈 MEAN REVERSION ENTRY for {pair}: RSI Oversold={dataframe['rsi'].iloc[-1]:.1f}, "
                       f"Near BB Lower, Volatility={dataframe['volatility'].iloc[-1]:.3f}")
            return 1
        return 0
    
    def breakout_entry(self, dataframe: DataFrame, pair: str) -> int:
        """Breakout strategy entry logic"""
        condition = (
            (dataframe['close'] > dataframe['resistance'].shift(1)) &
            (dataframe['close'].shift(1) <= dataframe['resistance'].shift(1)) &
            (dataframe['volume_ratio'] >= 1.5)
        )
        
        if condition.iloc[-1]:
            logger.info(f"⚡ BREAKOUT ENTRY for {pair}: Price={dataframe['close'].iloc[-1]:.4f} "
                       f"broke Resistance={dataframe['resistance'].iloc[-1]:.4f}, "
                       f"Volume={dataframe['volume_ratio'].iloc[-1]:.1f}x")
            return 1
        return 0
    
    def sample_entry(self, dataframe: DataFrame, pair: str) -> int:
        """Default sample strategy entry logic"""
        condition = (
            (dataframe['rsi'] <= 35) &
            (dataframe['volume'] > dataframe['volume_sma'])
        )
        
        if condition.iloc[-1]:
            logger.info(f"🎯 SAMPLE ENTRY for {pair}: RSI={dataframe['rsi'].iloc[-1]:.1f}, "
                       f"Volume Above Average")
            return 1
        return 0
    
    def momentum_exit(self, dataframe: DataFrame, pair: str) -> int:
        """Momentum strategy exit logic"""
        condition = (
            (dataframe['macd'] < dataframe['macdsignal']) &
            (dataframe['macd'].shift(1) >= dataframe['macdsignal'].shift(1))
        )
        
        if condition.iloc[-1]:
            logger.info(f"🛑 MOMENTUM EXIT for {pair}: MACD Bearish Crossover")
            return 1
        return 0
    
    def mean_reversion_exit(self, dataframe: DataFrame, pair: str) -> int:
        """Mean reversion strategy exit logic"""
        condition = (
            (dataframe['rsi'] >= 70) |
            (dataframe['close'] >= dataframe['bb_upper'] * 0.99)
        )
        
        if condition.iloc[-1]:
            reason = "RSI Overbought" if dataframe['rsi'].iloc[-1] >= 70 else "BB Upper Touch"
            logger.info(f"📉 MEAN REVERSION EXIT for {pair}: {reason}")
            return 1
        return 0
    
    def breakout_exit(self, dataframe: DataFrame, pair: str) -> int:
        """Breakout strategy exit logic"""
        condition = (
            dataframe['close'] < dataframe['support'] * 1.005
        )
        
        if condition.iloc[-1]:
            logger.info(f"🔻 BREAKOUT EXIT for {pair}: Support Break")
            return 1
        return 0
    
    def sample_exit(self, dataframe: DataFrame, pair: str) -> int:
        """Default sample strategy exit logic"""
        condition = dataframe['rsi'] >= 75
        
        if condition.iloc[-1]:
            logger.info(f"🔄 SAMPLE EXIT for {pair}: RSI Overbought={dataframe['rsi'].iloc[-1]:.1f}")
            return 1
        return 0
    
    def custom_entry_price(self, pair: str, current_time, proposed_rate: float, **kwargs) -> float:
        logger.info(f"💰 MULTI-STRATEGY ENTRY for {pair} at {proposed_rate:.4f}")
        return proposed_rate
    
    def custom_exit_price(self, pair: str, trade, current_time, proposed_rate: float, **kwargs) -> float:
        profit_ratio = trade.calc_profit_ratio(proposed_rate)
        logger.info(f"💸 MULTI-STRATEGY EXIT for {pair} at {proposed_rate:.4f} "
                   f"(Profit: {profit_ratio*100:.2f}%)")
        return proposed_rate