"""
Advanced Signal Engine - Professional Trading Signals with Execution
Combines multiple advanced analysis techniques for high-probability trades
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SignalStrength(Enum):
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4

class SignalType(Enum):
    ENTRY_LONG = "ENTRY_LONG"
    ENTRY_SHORT = "ENTRY_SHORT" 
    EXIT_LONG = "EXIT_LONG"
    EXIT_SHORT = "EXIT_SHORT"
    TAKE_PARTIAL = "TAKE_PARTIAL"
    TRAIL_STOP = "TRAIL_STOP"

@dataclass
class TradingSignal:
    symbol: str
    signal_type: SignalType
    strength: SignalStrength
    confidence: float  # 0.0 to 1.0
    entry_price: float
    stop_loss: float
    take_profit_levels: List[float]
    risk_reward_ratio: float
    position_size: float  # percentage of portfolio
    reasoning: List[str]
    technical_indicators: Dict[str, float]
    chart_patterns: List[str]
    liquidity_score: float
    unusual_activity: bool
    fibonacci_levels: Dict[str, float]
    timestamp: datetime

class AdvancedSignalEngine:
    """
    Professional-grade signal engine with advanced technical analysis
    """
    
    def __init__(self):
        self.active_positions = {}
        self.signal_history = []
        self.fibonacci_calculator = FibonacciAnalyzer()
        self.pattern_detector = ChartPatternDetector()
        self.liquidity_analyzer = LiquidityAnalyzer()
        self.unusual_activity_detector = UnusualActivityDetector()
        
    # =============================================================================
    # 1. ADVANCED TECHNICAL ANALYSIS ENGINE
    # =============================================================================
    
    async def analyze_comprehensive_signals(self, symbol: str, timeframes: List[str] = ['1h', '4h', '1d']) -> List[TradingSignal]:
        """
        Generate comprehensive trading signals using advanced multi-timeframe analysis
        """
        logger.info(f"🔍 Running comprehensive analysis for {symbol}")
        
        signals = []
        
        for timeframe in timeframes:
            try:
                # Get OHLCV data
                ohlcv_data = await self._get_ohlcv_data(symbol, timeframe, 500)
                
                if ohlcv_data is None or len(ohlcv_data) < 100:
                    continue
                    
                # 1. Technical Indicators Analysis
                technical_indicators = await self._calculate_advanced_indicators(ohlcv_data)
                
                # 2. Chart Pattern Recognition
                chart_patterns = await self.pattern_detector.detect_patterns(ohlcv_data)
                
                # 3. Fibonacci Analysis
                fibonacci_levels = await self.fibonacci_calculator.calculate_levels(ohlcv_data)
                
                # 4. Liquidity Analysis
                liquidity_score = await self.liquidity_analyzer.analyze_liquidity(symbol, ohlcv_data)
                
                # 5. Unusual Activity Detection
                unusual_activity = await self.unusual_activity_detector.detect_anomalies(symbol, ohlcv_data)
                
                # 6. Generate Signals
                timeframe_signals = await self._generate_signals_from_analysis(
                    symbol=symbol,
                    timeframe=timeframe,
                    ohlcv_data=ohlcv_data,
                    technical_indicators=technical_indicators,
                    chart_patterns=chart_patterns,
                    fibonacci_levels=fibonacci_levels,
                    liquidity_score=liquidity_score,
                    unusual_activity=unusual_activity
                )
                
                signals.extend(timeframe_signals)
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol} on {timeframe}: {e}")
                
        # Rank and filter signals by strength
        ranked_signals = self._rank_and_filter_signals(signals)
        
        logger.info(f"✅ Generated {len(ranked_signals)} high-probability signals for {symbol}")
        return ranked_signals
    
    async def _calculate_advanced_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate comprehensive technical indicators
        """
        indicators = {}
        
        try:
            # Price action indicators
            indicators['current_price'] = df['close'].iloc[-1]
            indicators['price_change_1h'] = (df['close'].iloc[-1] / df['close'].iloc[-2] - 1) * 100
            indicators['price_change_24h'] = (df['close'].iloc[-1] / df['close'].iloc[-24] - 1) * 100
            
            # Moving Averages
            indicators['sma_20'] = df['close'].rolling(20).mean().iloc[-1]
            indicators['sma_50'] = df['close'].rolling(50).mean().iloc[-1]
            indicators['sma_200'] = df['close'].rolling(200).mean().iloc[-1]
            indicators['ema_12'] = df['close'].ewm(span=12).mean().iloc[-1]
            indicators['ema_26'] = df['close'].ewm(span=26).mean().iloc[-1]
            
            # MACD
            macd_line = indicators['ema_12'] - indicators['ema_26']
            macd_signal = df['close'].ewm(span=9).mean().iloc[-1]
            indicators['macd'] = macd_line
            indicators['macd_signal'] = macd_signal
            indicators['macd_histogram'] = macd_line - macd_signal
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            indicators['rsi'] = 100 - (100 / (1 + rs)).iloc[-1]
            
            # Bollinger Bands
            bb_period = 20
            bb_std = 2
            sma = df['close'].rolling(bb_period).mean()
            std = df['close'].rolling(bb_period).std()
            indicators['bb_upper'] = (sma + (std * bb_std)).iloc[-1]
            indicators['bb_lower'] = (sma - (std * bb_std)).iloc[-1]
            indicators['bb_middle'] = sma.iloc[-1]
            indicators['bb_position'] = (indicators['current_price'] - indicators['bb_lower']) / (indicators['bb_upper'] - indicators['bb_lower'])
            
            # Volume indicators
            indicators['volume_sma'] = df['volume'].rolling(20).mean().iloc[-1]
            indicators['volume_ratio'] = df['volume'].iloc[-1] / indicators['volume_sma']
            
            # Volatility
            indicators['atr'] = self._calculate_atr(df)
            indicators['volatility'] = df['close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(365) * 100
            
            # Support/Resistance levels
            support_resistance = self._find_support_resistance(df)
            indicators.update(support_resistance)
            
            # Momentum indicators
            indicators['momentum'] = df['close'].iloc[-1] / df['close'].iloc[-10] - 1
            indicators['rate_of_change'] = (df['close'].iloc[-1] / df['close'].iloc[-12] - 1) * 100
            
            logger.info(f"📊 Calculated {len(indicators)} technical indicators")
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            high_low = df['high'] - df['low']
            high_close_prev = np.abs(df['high'] - df['close'].shift())
            low_close_prev = np.abs(df['low'] - df['close'].shift())
            
            true_range = np.maximum(high_low, np.maximum(high_close_prev, low_close_prev))
            atr = true_range.rolling(period).mean().iloc[-1]
            
            return atr
        except Exception:
            return 0.0
    
    def _find_support_resistance(self, df: pd.DataFrame, window: int = 20) -> Dict[str, float]:
        """Find key support and resistance levels"""
        try:
            # Find local highs and lows
            highs = df['high'].rolling(window=window, center=True).max()
            lows = df['low'].rolling(window=window, center=True).min()
            
            # Resistance levels (local highs)
            resistance_levels = df[df['high'] == highs]['high'].tail(5).values
            
            # Support levels (local lows)
            support_levels = df[df['low'] == lows]['low'].tail(5).values
            
            current_price = df['close'].iloc[-1]
            
            return {
                'nearest_resistance': min([r for r in resistance_levels if r > current_price], default=current_price * 1.05),
                'nearest_support': max([s for s in support_levels if s < current_price], default=current_price * 0.95),
                'resistance_strength': len([r for r in resistance_levels if abs(r - current_price) / current_price < 0.02]),
                'support_strength': len([s for s in support_levels if abs(s - current_price) / current_price < 0.02])
            }
        except Exception:
            current_price = df['close'].iloc[-1]
            return {
                'nearest_resistance': current_price * 1.05,
                'nearest_support': current_price * 0.95,
                'resistance_strength': 0,
                'support_strength': 0
            }
    
    async def _generate_signals_from_analysis(
        self, 
        symbol: str,
        timeframe: str,
        ohlcv_data: pd.DataFrame,
        technical_indicators: Dict[str, float],
        chart_patterns: List[str],
        fibonacci_levels: Dict[str, float],
        liquidity_score: float,
        unusual_activity: bool
    ) -> List[TradingSignal]:
        """
        Generate trading signals from comprehensive analysis
        """
        signals = []
        current_price = technical_indicators.get('current_price', 0)
        
        if current_price == 0:
            return signals
        
        # BULLISH SIGNAL DETECTION
        bullish_score = 0
        bullish_reasons = []
        
        # Technical Analysis Signals
        if technical_indicators.get('rsi', 50) < 30:
            bullish_score += 2
            bullish_reasons.append("RSI oversold (<30)")
            
        if technical_indicators.get('macd_histogram', 0) > 0:
            bullish_score += 1
            bullish_reasons.append("MACD histogram positive")
            
        if current_price > technical_indicators.get('sma_20', current_price):
            bullish_score += 1
            bullish_reasons.append("Price above SMA20")
            
        if technical_indicators.get('bb_position', 0.5) < 0.2:
            bullish_score += 2
            bullish_reasons.append("Near Bollinger Band lower bound")
            
        # Chart Pattern Signals
        bullish_patterns = ['double_bottom', 'cup_and_handle', 'ascending_triangle', 'bullish_flag']
        for pattern in chart_patterns:
            if pattern in bullish_patterns:
                bullish_score += 3
                bullish_reasons.append(f"Bullish pattern: {pattern}")
        
        # Fibonacci Signals
        if fibonacci_levels:
            fib_618 = fibonacci_levels.get('0.618', 0)
            if fib_618 and abs(current_price - fib_618) / current_price < 0.01:
                bullish_score += 2
                bullish_reasons.append("Near Fibonacci 61.8% retracement")
        
        # Volume/Liquidity Signals
        if technical_indicators.get('volume_ratio', 1) > 1.5:
            bullish_score += 1
            bullish_reasons.append("High volume confirmation")
            
        if liquidity_score > 0.7:
            bullish_score += 1
            bullish_reasons.append("High liquidity environment")
        
        # Unusual Activity
        if unusual_activity:
            bullish_score += 2
            bullish_reasons.append("Unusual buying activity detected")
        
        # Generate LONG signal if bullish score is high enough
        if bullish_score >= 6:
            confidence = min(bullish_score / 12.0, 0.95)
            strength = SignalStrength.VERY_STRONG if bullish_score >= 10 else SignalStrength.STRONG
            
            # Calculate position sizing based on confidence and volatility
            volatility = technical_indicators.get('volatility', 20)
            base_position_size = min(0.1, 0.05 / (volatility / 100))  # Risk-adjusted sizing
            position_size = base_position_size * confidence
            
            # Calculate stop loss and take profit levels
            atr = technical_indicators.get('atr', current_price * 0.02)
            stop_loss = current_price - (2 * atr)
            
            take_profit_levels = [
                current_price + (1.5 * atr),  # First target
                current_price + (3 * atr),    # Second target  
                current_price + (5 * atr)     # Moon target
            ]
            
            risk_reward = (take_profit_levels[0] - current_price) / (current_price - stop_loss)
            
            signal = TradingSignal(
                symbol=symbol,
                signal_type=SignalType.ENTRY_LONG,
                strength=strength,
                confidence=confidence,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit_levels=take_profit_levels,
                risk_reward_ratio=risk_reward,
                position_size=position_size,
                reasoning=bullish_reasons,
                technical_indicators=technical_indicators,
                chart_patterns=chart_patterns,
                liquidity_score=liquidity_score,
                unusual_activity=unusual_activity,
                fibonacci_levels=fibonacci_levels,
                timestamp=datetime.now()
            )
            
            signals.append(signal)
            logger.info(f"🚀 LONG signal generated for {symbol}: {confidence:.1%} confidence, {bullish_score} score")
        
        # BEARISH SIGNAL DETECTION (similar logic, inverted)
        bearish_score = 0
        bearish_reasons = []
        
        if technical_indicators.get('rsi', 50) > 70:
            bearish_score += 2
            bearish_reasons.append("RSI overbought (>70)")
            
        if technical_indicators.get('macd_histogram', 0) < 0:
            bearish_score += 1
            bearish_reasons.append("MACD histogram negative")
            
        if current_price < technical_indicators.get('sma_20', current_price):
            bearish_score += 1
            bearish_reasons.append("Price below SMA20")
            
        if technical_indicators.get('bb_position', 0.5) > 0.8:
            bearish_score += 2
            bearish_reasons.append("Near Bollinger Band upper bound")
        
        # Bearish patterns
        bearish_patterns = ['double_top', 'head_and_shoulders', 'descending_triangle', 'bearish_flag']
        for pattern in chart_patterns:
            if pattern in bearish_patterns:
                bearish_score += 3
                bearish_reasons.append(f"Bearish pattern: {pattern}")
        
        # Generate SHORT signal
        if bearish_score >= 6:
            confidence = min(bearish_score / 12.0, 0.95)
            strength = SignalStrength.VERY_STRONG if bearish_score >= 10 else SignalStrength.STRONG
            
            volatility = technical_indicators.get('volatility', 20)
            base_position_size = min(0.1, 0.05 / (volatility / 100))
            position_size = base_position_size * confidence
            
            atr = technical_indicators.get('atr', current_price * 0.02)
            stop_loss = current_price + (2 * atr)
            
            take_profit_levels = [
                current_price - (1.5 * atr),
                current_price - (3 * atr),
                current_price - (5 * atr)
            ]
            
            risk_reward = (current_price - take_profit_levels[0]) / (stop_loss - current_price)
            
            signal = TradingSignal(
                symbol=symbol,
                signal_type=SignalType.ENTRY_SHORT,
                strength=strength,
                confidence=confidence,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit_levels=take_profit_levels,
                risk_reward_ratio=risk_reward,
                position_size=position_size,
                reasoning=bearish_reasons,
                technical_indicators=technical_indicators,
                chart_patterns=chart_patterns,
                liquidity_score=liquidity_score,
                unusual_activity=unusual_activity,
                fibonacci_levels=fibonacci_levels,
                timestamp=datetime.now()
            )
            
            signals.append(signal)
            logger.info(f"📉 SHORT signal generated for {symbol}: {confidence:.1%} confidence, {bearish_score} score")
        
        return signals
    
    def _rank_and_filter_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """
        Rank signals by quality and filter out weak ones
        """
        if not signals:
            return []
        
        # Calculate composite score for each signal
        for signal in signals:
            composite_score = (
                signal.confidence * 0.4 +
                signal.strength.value / 4.0 * 0.3 +
                min(signal.risk_reward_ratio / 3.0, 1.0) * 0.2 +
                signal.liquidity_score * 0.1
            )
            signal.composite_score = composite_score
        
        # Sort by composite score
        ranked_signals = sorted(signals, key=lambda s: s.composite_score, reverse=True)
        
        # Filter: only keep signals with decent quality
        filtered_signals = [s for s in ranked_signals if s.composite_score >= 0.6]
        
        return filtered_signals[:10]  # Top 10 signals max
    
    async def _get_ohlcv_data(self, symbol: str, timeframe: str, limit: int = 500) -> Optional[pd.DataFrame]:
        """
        Get OHLCV data for analysis
        Mock implementation - replace with real data source
        """
        try:
            # Mock data generation for now
            # In production, fetch from Bybit/Binance/etc
            dates = pd.date_range(start=datetime.now() - timedelta(days=limit), periods=limit, freq='H')
            
            # Generate realistic OHLCV data with some patterns
            base_price = 50000 if 'BTC' in symbol else 3000 if 'ETH' in symbol else 200
            
            prices = []
            volumes = []
            
            for i in range(limit):
                # Add some trending and noise
                trend = (i - limit/2) * 0.001
                noise = np.random.normal(0, 0.02)
                price = base_price * (1 + trend + noise)
                prices.append(price)
                
                volume = np.random.exponential(1000) + 500
                volumes.append(volume)
            
            # Create OHLC from prices
            df = pd.DataFrame({
                'timestamp': dates,
                'close': prices
            })
            
            # Generate OHLC from close prices
            df['open'] = df['close'].shift(1).fillna(df['close'])
            df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.random.uniform(0, 0.01, len(df)))
            df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.random.uniform(0, 0.01, len(df)))
            df['volume'] = volumes
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting OHLCV data: {e}")
            return None

# =============================================================================
# SPECIALIZED ANALYZERS
# =============================================================================

class FibonacciAnalyzer:
    """Advanced Fibonacci retracement and extension analysis"""
    
    async def calculate_levels(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate Fibonacci retracement levels"""
        try:
            # Find swing high and low over recent period
            recent_data = df.tail(100)
            swing_high = recent_data['high'].max()
            swing_low = recent_data['low'].min()
            
            diff = swing_high - swing_low
            
            levels = {
                '0.0': swing_high,
                '0.236': swing_high - (0.236 * diff),
                '0.382': swing_high - (0.382 * diff),
                '0.500': swing_high - (0.500 * diff),
                '0.618': swing_high - (0.618 * diff),
                '0.786': swing_high - (0.786 * diff),
                '1.0': swing_low,
                # Extensions
                '1.272': swing_low - (0.272 * diff),
                '1.618': swing_low - (0.618 * diff)
            }
            
            return levels
            
        except Exception as e:
            logger.error(f"Error calculating Fibonacci levels: {e}")
            return {}

class ChartPatternDetector:
    """Advanced chart pattern recognition"""
    
    async def detect_patterns(self, df: pd.DataFrame) -> List[str]:
        """Detect various chart patterns"""
        patterns = []
        
        try:
            recent_data = df.tail(50)
            
            # Double Bottom Detection
            if self._detect_double_bottom(recent_data):
                patterns.append('double_bottom')
                
            # Double Top Detection  
            if self._detect_double_top(recent_data):
                patterns.append('double_top')
                
            # Cup and Handle
            if self._detect_cup_and_handle(recent_data):
                patterns.append('cup_and_handle')
                
            # Triangles
            if self._detect_ascending_triangle(recent_data):
                patterns.append('ascending_triangle')
                
            if self._detect_descending_triangle(recent_data):
                patterns.append('descending_triangle')
                
            # Head and Shoulders
            if self._detect_head_and_shoulders(recent_data):
                patterns.append('head_and_shoulders')
            
            # Flags and Pennants
            if self._detect_bullish_flag(recent_data):
                patterns.append('bullish_flag')
                
            if self._detect_bearish_flag(recent_data):
                patterns.append('bearish_flag')
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
        
        return patterns
    
    def _detect_double_bottom(self, df: pd.DataFrame) -> bool:
        """Detect double bottom pattern"""
        try:
            lows = df['low'].values
            if len(lows) < 20:
                return False
                
            # Find two significant lows
            local_mins = []
            for i in range(5, len(lows) - 5):
                if all(lows[i] <= lows[i-j] for j in range(1, 6)) and all(lows[i] <= lows[i+j] for j in range(1, 6)):
                    local_mins.append((i, lows[i]))
            
            if len(local_mins) >= 2:
                # Check if the two lows are similar (within 2%)
                low1_price = local_mins[-2][1]
                low2_price = local_mins[-1][1]
                
                if abs(low1_price - low2_price) / min(low1_price, low2_price) < 0.02:
                    return True
                    
            return False
            
        except Exception:
            return False
    
    def _detect_double_top(self, df: pd.DataFrame) -> bool:
        """Detect double top pattern"""
        try:
            highs = df['high'].values
            if len(highs) < 20:
                return False
                
            local_maxs = []
            for i in range(5, len(highs) - 5):
                if all(highs[i] >= highs[i-j] for j in range(1, 6)) and all(highs[i] >= highs[i+j] for j in range(1, 6)):
                    local_maxs.append((i, highs[i]))
            
            if len(local_maxs) >= 2:
                high1_price = local_maxs[-2][1]
                high2_price = local_maxs[-1][1]
                
                if abs(high1_price - high2_price) / max(high1_price, high2_price) < 0.02:
                    return True
                    
            return False
            
        except Exception:
            return False
    
    def _detect_cup_and_handle(self, df: pd.DataFrame) -> bool:
        """Detect cup and handle pattern"""
        try:
            if len(df) < 30:
                return False
                
            prices = df['close'].values
            
            # Cup: U-shaped recovery
            mid_point = len(prices) // 2
            left_high = max(prices[:10])
            cup_low = min(prices[10:mid_point+10])
            right_high = max(prices[mid_point:])
            
            # Check for U-shape (symmetric recovery)
            if (left_high > cup_low * 1.1 and 
                right_high > cup_low * 1.1 and
                abs(left_high - right_high) / max(left_high, right_high) < 0.05):
                
                # Handle: slight pullback after cup
                handle_prices = prices[-10:]
                if max(handle_prices) < right_high and min(handle_prices) > cup_low:
                    return True
                    
            return False
            
        except Exception:
            return False
    
    def _detect_ascending_triangle(self, df: pd.DataFrame) -> bool:
        """Detect ascending triangle pattern"""
        try:
            if len(df) < 20:
                return False
                
            highs = df['high'].values[-20:]
            lows = df['low'].values[-20:]
            
            # Flat resistance line (highs around same level)
            recent_highs = highs[-10:]
            resistance_level = np.mean(recent_highs)
            resistance_consistent = np.std(recent_highs) / resistance_level < 0.02
            
            # Rising support line (higher lows)
            first_half_lows = lows[:10]
            second_half_lows = lows[10:]
            
            rising_support = np.mean(second_half_lows) > np.mean(first_half_lows)
            
            return resistance_consistent and rising_support
            
        except Exception:
            return False
    
    def _detect_descending_triangle(self, df: pd.DataFrame) -> bool:
        """Detect descending triangle pattern"""
        try:
            if len(df) < 20:
                return False
                
            highs = df['high'].values[-20:]
            lows = df['low'].values[-20:]
            
            # Flat support line
            recent_lows = lows[-10:]
            support_level = np.mean(recent_lows)
            support_consistent = np.std(recent_lows) / support_level < 0.02
            
            # Falling resistance line (lower highs)
            first_half_highs = highs[:10]
            second_half_highs = highs[10:]
            
            falling_resistance = np.mean(second_half_highs) < np.mean(first_half_highs)
            
            return support_consistent and falling_resistance
            
        except Exception:
            return False
    
    def _detect_head_and_shoulders(self, df: pd.DataFrame) -> bool:
        """Detect head and shoulders pattern"""
        try:
            if len(df) < 30:
                return False
                
            highs = df['high'].values
            
            # Find three peaks
            local_maxs = []
            for i in range(5, len(highs) - 5):
                if all(highs[i] >= highs[i-j] for j in range(1, 6)) and all(highs[i] >= highs[i+j] for j in range(1, 6)):
                    local_maxs.append((i, highs[i]))
            
            if len(local_maxs) >= 3:
                # Take last three peaks
                peaks = local_maxs[-3:]
                left_shoulder, head, right_shoulder = peaks
                
                # Head should be higher than both shoulders
                # Shoulders should be roughly equal
                if (head[1] > left_shoulder[1] and 
                    head[1] > right_shoulder[1] and
                    abs(left_shoulder[1] - right_shoulder[1]) / max(left_shoulder[1], right_shoulder[1]) < 0.05):
                    return True
                    
            return False
            
        except Exception:
            return False
    
    def _detect_bullish_flag(self, df: pd.DataFrame) -> bool:
        """Detect bullish flag pattern"""
        try:
            if len(df) < 20:
                return False
                
            prices = df['close'].values
            
            # Strong upward move (flagpole)
            flagpole_start = prices[-20]
            flagpole_end = prices[-10]
            
            strong_upward_move = (flagpole_end / flagpole_start) > 1.05
            
            # Slight downward consolidation (flag)
            flag_prices = prices[-10:]
            flag_trend = (flag_prices[-1] / flag_prices[0]) > 0.98  # Small pullback
            
            return strong_upward_move and flag_trend
            
        except Exception:
            return False
    
    def _detect_bearish_flag(self, df: pd.DataFrame) -> bool:
        """Detect bearish flag pattern"""
        try:
            if len(df) < 20:
                return False
                
            prices = df['close'].values
            
            # Strong downward move
            flagpole_start = prices[-20]
            flagpole_end = prices[-10]
            
            strong_downward_move = (flagpole_end / flagpole_start) < 0.95
            
            # Slight upward consolidation
            flag_prices = prices[-10:]
            flag_trend = (flag_prices[-1] / flag_prices[0]) < 1.02
            
            return strong_downward_move and flag_trend
            
        except Exception:
            return False

class LiquidityAnalyzer:
    """Analyze market liquidity conditions"""
    
    async def analyze_liquidity(self, symbol: str, df: pd.DataFrame) -> float:
        """
        Analyze liquidity score (0.0 to 1.0)
        """
        try:
            # Volume consistency
            volumes = df['volume'].tail(50).values
            avg_volume = np.mean(volumes)
            volume_std = np.std(volumes)
            volume_consistency = 1.0 - min(volume_std / avg_volume, 1.0) if avg_volume > 0 else 0.0
            
            # Bid-ask spread simulation (normally from orderbook)
            # Mock implementation based on volatility
            price_volatility = df['close'].pct_change().tail(20).std()
            spread_score = max(0, 1.0 - (price_volatility * 10))  # Lower volatility = tighter spreads
            
            # Volume trend
            recent_volume = np.mean(volumes[-10:])
            older_volume = np.mean(volumes[:10])
            volume_trend_score = min(recent_volume / older_volume if older_volume > 0 else 1.0, 2.0) / 2.0
            
            # Composite liquidity score
            liquidity_score = (volume_consistency * 0.4 + spread_score * 0.4 + volume_trend_score * 0.2)
            
            return min(max(liquidity_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error analyzing liquidity: {e}")
            return 0.5

class UnusualActivityDetector:
    """Detect unusual market activity"""
    
    async def detect_anomalies(self, symbol: str, df: pd.DataFrame) -> bool:
        """
        Detect unusual trading activity
        """
        try:
            # Volume spikes
            volumes = df['volume'].tail(50).values
            recent_volume = volumes[-1]
            avg_volume = np.mean(volumes[:-1])
            volume_spike = recent_volume > (avg_volume * 2.5)
            
            # Price gaps
            prices = df['close'].tail(10).values
            price_changes = np.abs(np.diff(prices) / prices[:-1])
            unusual_price_movement = np.any(price_changes > 0.05)  # >5% moves
            
            # Volatility clusters
            volatility = df['close'].pct_change().tail(20).rolling(5).std().values
            volatility_spike = volatility[-1] > np.mean(volatility[:-1]) * 2
            
            return volume_spike or unusual_price_movement or volatility_spike
            
        except Exception as e:
            logger.error(f"Error detecting unusual activity: {e}")
            return False