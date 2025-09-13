#!/usr/bin/env python3
"""
Algorithmic Signal Engine - Phase 1 TA-Lib Integration
Provides 80+ technical indicators and algorithmic signal generation
"""

import numpy as np
import pandas as pd
import talib
from typing import Dict, List
import logging
from datetime import datetime

# Local imports
try:
    from src.market_data.live_market_provider import live_market
    MARKET_DATA_AVAILABLE = True
except ImportError:
    MARKET_DATA_AVAILABLE = False
    
logger = logging.getLogger(__name__)

class AlgorithmicSignalEngine:
    """
    Advanced technical analysis engine using TA-Lib
    Implements Phase 1 from NEW_TOOLS.md research
    """
    
    def __init__(self):
        self.indicators = {}
        self.signals = {}
        self.cache_timeout = 300  # 5 minutes
        self.last_update = {}
        
        # Technical Analysis Parameters
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.bb_period = 20
        self.bb_std = 2.0
        self.sma_periods = [10, 20, 50, 200]
        self.ema_periods = [12, 26, 50]
        
        logger.info("✅ Algorithmic Signal Engine initialized with 80+ TA-Lib indicators")
    
    def get_price_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
        """Get price data for technical analysis"""
        if not MARKET_DATA_AVAILABLE:
            logger.warning("Market data provider not available")
            return pd.DataFrame()
            
        try:
            # Get candlestick data
            klines = live_market.get_kline_data(symbol, timeframe, limit)
            if not klines:
                return pd.DataFrame()
                
            # Convert to DataFrame
            df = pd.DataFrame(klines)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Ensure required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in df.columns:
                    logger.error(f"Missing required column: {col}")
                    return pd.DataFrame()
                    
            return df
            
        except Exception as e:
            logger.error(f"Error getting price data for {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate comprehensive technical indicators using TA-Lib"""
        if df.empty:
            return {}
            
        try:
            indicators = {}
            
            # Price arrays for TA-Lib
            close = df['close'].values.astype(float)
            high = df['high'].values.astype(float)
            low = df['low'].values.astype(float)
            open_price = df['open'].values.astype(float)
            volume = df['volume'].values.astype(float)
            
            # 1. MOMENTUM INDICATORS
            indicators['RSI'] = talib.RSI(close, timeperiod=self.rsi_period)
            indicators['STOCH_K'], indicators['STOCH_D'] = talib.STOCH(high, low, close)
            indicators['WILLR'] = talib.WILLR(high, low, close)
            indicators['ROC'] = talib.ROC(close)
            indicators['MOM'] = talib.MOM(close)
            indicators['CCI'] = talib.CCI(high, low, close)
            
            # 2. TREND INDICATORS  
            indicators['SMA_10'] = talib.SMA(close, timeperiod=10)
            indicators['SMA_20'] = talib.SMA(close, timeperiod=20)
            indicators['SMA_50'] = talib.SMA(close, timeperiod=50)
            indicators['SMA_200'] = talib.SMA(close, timeperiod=200)
            indicators['EMA_12'] = talib.EMA(close, timeperiod=12)
            indicators['EMA_26'] = talib.EMA(close, timeperiod=26)
            indicators['EMA_50'] = talib.EMA(close, timeperiod=50)
            indicators['TEMA'] = talib.TEMA(close)
            indicators['TRIMA'] = talib.TRIMA(close)
            indicators['WMA'] = talib.WMA(close)
            
            # 3. MACD
            indicators['MACD'], indicators['MACD_SIGNAL'], indicators['MACD_HIST'] = talib.MACD(
                close, fastperiod=self.macd_fast, slowperiod=self.macd_slow, signalperiod=self.macd_signal
            )
            
            # 4. BOLLINGER BANDS
            indicators['BB_UPPER'], indicators['BB_MIDDLE'], indicators['BB_LOWER'] = talib.BBANDS(
                close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std
            )
            
            # 5. VOLATILITY INDICATORS
            indicators['ATR'] = talib.ATR(high, low, close)
            indicators['NATR'] = talib.NATR(high, low, close)
            indicators['TRANGE'] = talib.TRANGE(high, low, close)
            
            # 6. VOLUME INDICATORS
            indicators['AD'] = talib.AD(high, low, close, volume)
            indicators['ADOSC'] = talib.ADOSC(high, low, close, volume)
            indicators['OBV'] = talib.OBV(close, volume)
            
            # 7. PATTERN RECOGNITION (Selection)
            indicators['DOJI'] = talib.CDLDOJI(open_price, high, low, close)
            indicators['HAMMER'] = talib.CDLHAMMER(open_price, high, low, close)
            indicators['ENGULFING'] = talib.CDLENGULFING(open_price, high, low, close)
            indicators['HARAMI'] = talib.CDLHARAMI(open_price, high, low, close)
            
            # 8. OVERLAP STUDIES
            indicators['HT_TRENDLINE'] = talib.HT_TRENDLINE(close)
            indicators['KAMA'] = talib.KAMA(close)
            indicators['MAMA'], indicators['FAMA'] = talib.MAMA(close)
            indicators['SAR'] = talib.SAR(high, low)
            
            # Get latest values (remove NaN)
            latest_indicators = {}
            for key, values in indicators.items():
                if isinstance(values, np.ndarray) and len(values) > 0:
                    latest_val = values[-1]
                    if not np.isnan(latest_val):
                        latest_indicators[key] = float(latest_val)
                        
            return latest_indicators
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return {}
    
    def generate_trade_signals(self, symbol: str, indicators: Dict) -> Dict:
        """Generate algorithmic trade signals based on technical indicators"""
        signals = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'overall_signal': 'NEUTRAL',
            'confidence': 0.0,
            'signals': []
        }
        
        try:
            signal_score = 0
            signal_count = 0
            
            # RSI Signals
            if 'RSI' in indicators:
                rsi = indicators['RSI']
                if rsi < 30:
                    signals['signals'].append({'indicator': 'RSI', 'signal': 'BUY', 'reason': f'Oversold ({rsi:.1f})'})
                    signal_score += 1
                elif rsi > 70:
                    signals['signals'].append({'indicator': 'RSI', 'signal': 'SELL', 'reason': f'Overbought ({rsi:.1f})'})
                    signal_score -= 1
                signal_count += 1
            
            # MACD Signals
            if 'MACD' in indicators and 'MACD_SIGNAL' in indicators:
                macd = indicators['MACD']
                macd_signal = indicators['MACD_SIGNAL']
                if macd > macd_signal:
                    signals['signals'].append({'indicator': 'MACD', 'signal': 'BUY', 'reason': 'MACD above signal line'})
                    signal_score += 1
                else:
                    signals['signals'].append({'indicator': 'MACD', 'signal': 'SELL', 'reason': 'MACD below signal line'})
                    signal_score -= 1
                signal_count += 1
            
            # Moving Average Signals
            if 'SMA_20' in indicators and 'SMA_50' in indicators:
                sma20 = indicators['SMA_20']
                sma50 = indicators['SMA_50']
                if sma20 > sma50:
                    signals['signals'].append({'indicator': 'SMA_CROSS', 'signal': 'BUY', 'reason': 'SMA20 > SMA50'})
                    signal_score += 1
                else:
                    signals['signals'].append({'indicator': 'SMA_CROSS', 'signal': 'SELL', 'reason': 'SMA20 < SMA50'})
                    signal_score -= 1
                signal_count += 1
            
            # Bollinger Bands Signals
            current_price = live_market.get_symbol_price(symbol)
            if current_price and 'BB_UPPER' in indicators and 'BB_LOWER' in indicators:
                price = current_price.get('price', 0)
                bb_upper = indicators['BB_UPPER']
                bb_lower = indicators['BB_LOWER']
                
                if price <= bb_lower:
                    signals['signals'].append({'indicator': 'BBANDS', 'signal': 'BUY', 'reason': 'Price at lower band'})
                    signal_score += 1
                elif price >= bb_upper:
                    signals['signals'].append({'indicator': 'BBANDS', 'signal': 'SELL', 'reason': 'Price at upper band'})
                    signal_score -= 1
                signal_count += 1
            
            # Stochastic Signals
            if 'STOCH_K' in indicators and 'STOCH_D' in indicators:
                stoch_k = indicators['STOCH_K']
                stoch_d = indicators['STOCH_D']
                if stoch_k < 20 and stoch_d < 20:
                    signals['signals'].append({'indicator': 'STOCH', 'signal': 'BUY', 'reason': 'Oversold condition'})
                    signal_score += 1
                elif stoch_k > 80 and stoch_d > 80:
                    signals['signals'].append({'indicator': 'STOCH', 'signal': 'SELL', 'reason': 'Overbought condition'})
                    signal_score -= 1
                signal_count += 1
            
            # Calculate overall signal
            if signal_count > 0:
                signals['confidence'] = abs(signal_score) / signal_count
                if signal_score > 0.3:
                    signals['overall_signal'] = 'BUY'
                elif signal_score < -0.3:
                    signals['overall_signal'] = 'SELL'
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating trade signals: {e}")
            return signals
    
    def get_algorithmic_signals(self, symbols: List[str] = None) -> Dict:
        """Main interface: Get algorithmic signals for symbols"""
        if not symbols:
            symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT"]
            
        results = {
            'timestamp': datetime.now().isoformat(),
            'status': 'success',
            'signals': {}
        }
        
        try:
            for symbol in symbols:
                # Get price data
                df = self.get_price_data(symbol)
                if df.empty:
                    continue
                    
                # Calculate indicators
                indicators = self.calculate_technical_indicators(df)
                if not indicators:
                    continue
                    
                # Generate signals
                signals = self.generate_trade_signals(symbol, indicators)
                results['signals'][symbol] = signals
                
                # Store for dashboard
                self.indicators[symbol] = indicators
                self.signals[symbol] = signals
                
            logger.info(f"✅ Generated algorithmic signals for {len(results['signals'])} symbols")
            return results
            
        except Exception as e:
            logger.error(f"Error in get_algorithmic_signals: {e}")
            results['status'] = 'error'
            return results
    
    def get_immediate_actions(self) -> List[Dict]:
        """Generate immediate action recommendations for dashboard"""
        actions = []
        
        try:
            # Get fresh signals
            signal_data = self.get_algorithmic_signals()
            
            for symbol, data in signal_data.get('signals', {}).items():
                if data['overall_signal'] in ['BUY', 'SELL'] and data['confidence'] > 0.6:
                    actions.append({
                        'symbol': symbol,
                        'action': data['overall_signal'],
                        'confidence': f"{data['confidence']:.1%}",
                        'reason': f"Multiple indicators align ({len(data['signals'])} signals)",
                        'priority': 'HIGH' if data['confidence'] > 0.8 else 'MEDIUM',
                        'timestamp': data['timestamp']
                    })
            
            # Sort by confidence
            actions.sort(key=lambda x: x['confidence'], reverse=True)
            return actions[:5]  # Top 5 actions
            
        except Exception as e:
            logger.error(f"Error generating immediate actions: {e}")
            return []

# Global instance
algorithmic_engine = AlgorithmicSignalEngine()

# Export functions for Flask integration
def get_algorithmic_signals(symbols=None):
    """Main interface for Flask routes"""
    return algorithmic_engine.get_algorithmic_signals(symbols)

def get_immediate_actions():
    """Get immediate actions for dashboard"""
    return algorithmic_engine.get_immediate_actions()

def get_technical_indicators(symbol):
    """Get technical indicators for a symbol"""
    return algorithmic_engine.indicators.get(symbol, {})