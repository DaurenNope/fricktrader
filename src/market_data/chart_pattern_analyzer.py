"""
Advanced Chart Pattern Recognition System
Detects double tops, head & shoulders, RSI divergences, Elliott waves, etc.
"""

import numpy as np
import pandas as pd
import talib.abstract as ta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from scipy.signal import find_peaks, find_peaks_cwt
from scipy.stats import linregress

logger = logging.getLogger(__name__)

@dataclass
class PatternResult:
    """Chart pattern detection result"""
    pattern_type: str
    confidence: float  # 0.0 to 1.0
    description: str
    start_index: int
    end_index: int
    key_levels: List[float]
    signal: str  # 'bullish', 'bearish', 'neutral'
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None

class ChartPatternAnalyzer:
    """
    Advanced chart pattern recognition system
    Like TradingView's pattern recognition but custom-built
    """
    
    def __init__(self):
        self.min_pattern_length = 10  # Minimum candles for pattern
        self.max_pattern_length = 100  # Maximum candles for pattern
        
    def analyze_patterns(self, df: pd.DataFrame) -> List[PatternResult]:
        """
        Analyze all chart patterns in the dataframe
        Returns list of detected patterns
        """
        patterns = []
        
        if len(df) < self.min_pattern_length:
            return patterns
        
        try:
            # Add technical indicators needed for pattern detection
            df = self._add_indicators(df)
            
            # Detect various patterns
            patterns.extend(self._detect_double_tops_bottoms(df))
            patterns.extend(self._detect_head_shoulders(df))
            patterns.extend(self._detect_rsi_divergences(df))
            patterns.extend(self._detect_macd_divergences(df))
            patterns.extend(self._detect_triangles(df))
            patterns.extend(self._detect_flags_pennants(df))
            patterns.extend(self._detect_wedges(df))
            patterns.extend(self._detect_channels(df))
            patterns.extend(self._detect_cup_handle(df))
            patterns.extend(self._detect_inverse_head_shoulders(df))
            patterns.extend(self._detect_triple_tops_bottoms(df))
            patterns.extend(self._detect_breakouts(df))
            patterns.extend(self._detect_elliott_waves(df))
            patterns.extend(self._detect_fibonacci_retracements(df))
            patterns.extend(self._detect_gann_levels(df))
            patterns.extend(self._detect_harmonic_patterns(df))
            patterns.extend(self._detect_support_resistance(df))
            
            # Sort by confidence
            patterns.sort(key=lambda x: x.confidence, reverse=True)
            
            logger.info(f"🔍 Detected {len(patterns)} chart patterns")
            
        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
        
        return patterns
    
    def _add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators needed for pattern detection"""
        
        # RSI for divergence detection
        df['rsi'] = ta.RSI(df, timeperiod=14)
        
        # MACD for momentum
        macd = ta.MACD(df)
        df['macd'] = macd['macd']
        df['macd_signal'] = macd['macdsignal']
        df['macd_hist'] = macd['macdhist']
        
        # Moving averages
        df['sma_20'] = ta.SMA(df, timeperiod=20)
        df['sma_50'] = ta.SMA(df, timeperiod=50)
        df['ema_12'] = ta.EMA(df, timeperiod=12)
        df['ema_26'] = ta.EMA(df, timeperiod=26)
        
        # Bollinger Bands
        bb = ta.BBANDS(df)
        df['bb_upper'] = bb['upperband']
        df['bb_middle'] = bb['middleband']
        df['bb_lower'] = bb['lowerband']
        
        # ATR for volatility
        df['atr'] = ta.ATR(df, timeperiod=14)
        
        # Volume indicators
        df['volume_sma'] = ta.SMA(df['volume'], timeperiod=20)
        
        return df
    
    def _detect_double_tops_bottoms(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect double top and double bottom patterns"""
        patterns = []
        
        try:
            # Find peaks and troughs
            peaks, _ = find_peaks(df['high'].values, distance=5, prominence=df['atr'].mean())
            troughs, _ = find_peaks(-df['low'].values, distance=5, prominence=df['atr'].mean())
            
            # Double tops
            for i in range(len(peaks) - 1):
                peak1_idx = peaks[i]
                peak2_idx = peaks[i + 1]
                
                if peak2_idx - peak1_idx < 50:  # Within reasonable distance
                    peak1_price = df.iloc[peak1_idx]['high']
                    peak2_price = df.iloc[peak2_idx]['high']
                    
                    # Check if peaks are similar height (within 2%)
                    if abs(peak1_price - peak2_price) / peak1_price < 0.02:
                        # Find the valley between peaks
                        valley_idx = df.iloc[peak1_idx:peak2_idx]['low'].idxmin()
                        valley_price = df.iloc[valley_idx]['low']
                        
                        # Validate pattern
                        if (peak1_price - valley_price) / peak1_price > 0.03:  # At least 3% retracement
                            confidence = 0.8 - abs(peak1_price - peak2_price) / peak1_price * 10
                            
                            patterns.append(PatternResult(
                                pattern_type="Double Top",
                                confidence=max(0.5, confidence),
                                description=f"Double top at ${peak1_price:.2f} and ${peak2_price:.2f}",
                                start_index=peak1_idx,
                                end_index=peak2_idx,
                                key_levels=[peak1_price, peak2_price, valley_price],
                                signal="bearish",
                                target_price=valley_price - (peak1_price - valley_price) * 0.5,
                                stop_loss=max(peak1_price, peak2_price) * 1.02
                            ))
            
            # Double bottoms
            for i in range(len(troughs) - 1):
                trough1_idx = troughs[i]
                trough2_idx = troughs[i + 1]
                
                if trough2_idx - trough1_idx < 50:
                    trough1_price = df.iloc[trough1_idx]['low']
                    trough2_price = df.iloc[trough2_idx]['low']
                    
                    if abs(trough1_price - trough2_price) / trough1_price < 0.02:
                        # Find peak between troughs
                        peak_idx = df.iloc[trough1_idx:trough2_idx]['high'].idxmax()
                        peak_price = df.iloc[peak_idx]['high']
                        
                        if (peak_price - trough1_price) / trough1_price > 0.03:
                            confidence = 0.8 - abs(trough1_price - trough2_price) / trough1_price * 10
                            
                            patterns.append(PatternResult(
                                pattern_type="Double Bottom",
                                confidence=max(0.5, confidence),
                                description=f"Double bottom at ${trough1_price:.2f} and ${trough2_price:.2f}",
                                start_index=trough1_idx,
                                end_index=trough2_idx,
                                key_levels=[trough1_price, trough2_price, peak_price],
                                signal="bullish",
                                target_price=peak_price + (peak_price - trough1_price) * 0.5,
                                stop_loss=min(trough1_price, trough2_price) * 0.98
                            ))
                            
        except Exception as e:
            logger.error(f"Error detecting double tops/bottoms: {e}")
        
        return patterns
    
    def _detect_head_shoulders(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect head and shoulders patterns"""
        patterns = []
        
        try:
            peaks, _ = find_peaks(df['high'].values, distance=8, prominence=df['atr'].mean())
            
            # Need at least 3 peaks for head and shoulders
            if len(peaks) < 3:
                return patterns
            
            for i in range(len(peaks) - 2):
                left_shoulder = peaks[i]
                head = peaks[i + 1]
                right_shoulder = peaks[i + 2]
                
                ls_price = df.iloc[left_shoulder]['high']
                head_price = df.iloc[head]['high']
                rs_price = df.iloc[right_shoulder]['high']
                
                # Head should be higher than both shoulders
                if head_price > ls_price and head_price > rs_price:
                    # Shoulders should be roughly equal (within 3%)
                    if abs(ls_price - rs_price) / ls_price < 0.03:
                        # Find neckline (lows between shoulders and head)
                        left_low_idx = df.iloc[left_shoulder:head]['low'].idxmin()
                        right_low_idx = df.iloc[head:right_shoulder]['low'].idxmin()
                        
                        left_low = df.iloc[left_low_idx]['low']
                        right_low = df.iloc[right_low_idx]['low']
                        neckline = (left_low + right_low) / 2
                        
                        # Validate pattern strength
                        if (head_price - neckline) / neckline > 0.05:  # At least 5% head above neckline
                            confidence = 0.75
                            
                            patterns.append(PatternResult(
                                pattern_type="Head and Shoulders",
                                confidence=confidence,
                                description=f"H&S: Head ${head_price:.2f}, Shoulders ${ls_price:.2f}/${rs_price:.2f}",
                                start_index=left_shoulder,
                                end_index=right_shoulder,
                                key_levels=[ls_price, head_price, rs_price, neckline],
                                signal="bearish",
                                target_price=neckline - (head_price - neckline),
                                stop_loss=head_price * 1.02
                            ))
                            
        except Exception as e:
            logger.error(f"Error detecting head and shoulders: {e}")
        
        return patterns    

    def _detect_rsi_divergences(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect RSI divergences - very powerful signals"""
        patterns = []
        
        try:
            # Find price peaks and RSI peaks
            price_peaks, _ = find_peaks(df['high'].values, distance=10)
            price_troughs, _ = find_peaks(-df['low'].values, distance=10)
            
            # Bullish divergence: Price makes lower lows, RSI makes higher lows
            if len(price_troughs) >= 2:
                for i in range(len(price_troughs) - 1):
                    trough1_idx = price_troughs[i]
                    trough2_idx = price_troughs[i + 1]
                    
                    if trough2_idx - trough1_idx < 50:  # Within reasonable distance
                        price1 = df.iloc[trough1_idx]['low']
                        price2 = df.iloc[trough2_idx]['low']
                        rsi1 = df.iloc[trough1_idx]['rsi']
                        rsi2 = df.iloc[trough2_idx]['rsi']
                        
                        # Price lower low, RSI higher low
                        if price2 < price1 and rsi2 > rsi1 and rsi1 < 40:
                            confidence = 0.85 + (rsi2 - rsi1) / 100  # Higher confidence for stronger divergence
                            
                            patterns.append(PatternResult(
                                pattern_type="Bullish RSI Divergence",
                                confidence=min(0.95, confidence),
                                description=f"Price: ${price1:.2f}→${price2:.2f}, RSI: {rsi1:.1f}→{rsi2:.1f}",
                                start_index=trough1_idx,
                                end_index=trough2_idx,
                                key_levels=[price1, price2],
                                signal="bullish",
                                target_price=price2 * 1.05,  # 5% target
                                stop_loss=price2 * 0.97
                            ))
            
            # Bearish divergence: Price makes higher highs, RSI makes lower highs
            if len(price_peaks) >= 2:
                for i in range(len(price_peaks) - 1):
                    peak1_idx = price_peaks[i]
                    peak2_idx = price_peaks[i + 1]
                    
                    if peak2_idx - peak1_idx < 50:
                        price1 = df.iloc[peak1_idx]['high']
                        price2 = df.iloc[peak2_idx]['high']
                        rsi1 = df.iloc[peak1_idx]['rsi']
                        rsi2 = df.iloc[peak2_idx]['rsi']
                        
                        # Price higher high, RSI lower high
                        if price2 > price1 and rsi2 < rsi1 and rsi1 > 60:
                            confidence = 0.85 + (rsi1 - rsi2) / 100
                            
                            patterns.append(PatternResult(
                                pattern_type="Bearish RSI Divergence",
                                confidence=min(0.95, confidence),
                                description=f"Price: ${price1:.2f}→${price2:.2f}, RSI: {rsi1:.1f}→{rsi2:.1f}",
                                start_index=peak1_idx,
                                end_index=peak2_idx,
                                key_levels=[price1, price2],
                                signal="bearish",
                                target_price=price2 * 0.95,  # 5% target down
                                stop_loss=price2 * 1.03
                            ))
                            
        except Exception as e:
            logger.error(f"Error detecting RSI divergences: {e}")
        
        return patterns
    
    def _detect_triangles(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect triangle patterns (ascending, descending, symmetrical)"""
        patterns = []
        
        try:
            if len(df) < 30:
                return patterns
            
            # Look for converging trend lines
            recent_data = df.tail(30)  # Last 30 candles
            
            # Find highs and lows
            highs = recent_data['high'].values
            lows = recent_data['low'].values
            x = np.arange(len(recent_data))
            
            # Fit trend lines to highs and lows
            high_slope, high_intercept, high_r, _, _ = linregress(x, highs)
            low_slope, low_intercept, low_r, _, _ = linregress(x, lows)
            
            # Check if lines are converging and have good fit
            if abs(high_r) > 0.7 and abs(low_r) > 0.7:  # Good correlation
                if abs(high_slope - low_slope) > 0.1:  # Lines are converging
                    
                    # Determine triangle type
                    if abs(high_slope) < 0.1 and low_slope > 0.1:
                        # Ascending triangle (flat top, rising bottom)
                        pattern_type = "Ascending Triangle"
                        signal = "bullish"
                        confidence = 0.7
                    elif high_slope < -0.1 and abs(low_slope) < 0.1:
                        # Descending triangle (falling top, flat bottom)
                        pattern_type = "Descending Triangle"
                        signal = "bearish"
                        confidence = 0.7
                    elif high_slope < -0.1 and low_slope > 0.1:
                        # Symmetrical triangle
                        pattern_type = "Symmetrical Triangle"
                        signal = "neutral"
                        confidence = 0.6
                    else:
                        return patterns
                    
                    current_price = df.iloc[-1]['close']
                    resistance = highs[-1]
                    support = lows[-1]
                    
                    patterns.append(PatternResult(
                        pattern_type=pattern_type,
                        confidence=confidence,
                        description=f"{pattern_type}: Support ${support:.2f}, Resistance ${resistance:.2f}",
                        start_index=len(df) - 30,
                        end_index=len(df) - 1,
                        key_levels=[support, resistance],
                        signal=signal,
                        target_price=resistance + (resistance - support) if signal == "bullish" else support - (resistance - support),
                        stop_loss=support * 0.98 if signal == "bullish" else resistance * 1.02
                    ))
                    
        except Exception as e:
            logger.error(f"Error detecting triangles: {e}")
        
        return patterns
    
    def _detect_flags_pennants(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect flag and pennant continuation patterns"""
        patterns = []
        
        try:
            # Look for strong moves followed by consolidation
            if len(df) < 20:
                return patterns
            
            # Calculate price change over different periods
            df['price_change_5'] = df['close'].pct_change(5)
            df['price_change_10'] = df['close'].pct_change(10)
            
            # Look for strong initial move (>3% in 5-10 candles)
            strong_moves = df[abs(df['price_change_10']) > 0.03].index
            
            for move_idx in strong_moves:
                if move_idx < len(df) - 10:  # Need space for consolidation
                    move_direction = 1 if df.loc[move_idx, 'price_change_10'] > 0 else -1
                    
                    # Check for consolidation after the move
                    consolidation = df.loc[move_idx:move_idx+10]
                    if len(consolidation) >= 8:
                        volatility = consolidation['close'].std() / consolidation['close'].mean()
                        
                        # Low volatility indicates consolidation
                        if volatility < 0.02:  # Less than 2% volatility
                            pattern_type = "Bull Flag" if move_direction > 0 else "Bear Flag"
                            signal = "bullish" if move_direction > 0 else "bearish"
                            
                            patterns.append(PatternResult(
                                pattern_type=pattern_type,
                                confidence=0.65,
                                description=f"{pattern_type} after {df.loc[move_idx, 'price_change_10']*100:.1f}% move",
                                start_index=move_idx,
                                end_index=move_idx + 10,
                                key_levels=[consolidation['low'].min(), consolidation['high'].max()],
                                signal=signal,
                                target_price=df.iloc[-1]['close'] * (1.05 if move_direction > 0 else 0.95),
                                stop_loss=consolidation['low'].min() if move_direction > 0 else consolidation['high'].max()
                            ))
                            
        except Exception as e:
            logger.error(f"Error detecting flags/pennants: {e}")
        
        return patterns
    
    def _detect_support_resistance(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect key support and resistance levels"""
        patterns = []
        
        try:
            # Find significant price levels that have been tested multiple times
            price_levels = []
            
            # Get recent highs and lows
            recent_highs = df['high'].tail(50).values
            recent_lows = df['low'].tail(50).values
            
            # Find levels that appear multiple times (within 1% tolerance)
            all_levels = np.concatenate([recent_highs, recent_lows])
            
            for level in all_levels:
                # Count how many times this level was touched
                touches = 0
                for price in all_levels:
                    if abs(price - level) / level < 0.01:  # Within 1%
                        touches += 1
                
                if touches >= 3:  # Level touched at least 3 times
                    current_price = df.iloc[-1]['close']
                    
                    if level > current_price:
                        # Resistance level
                        patterns.append(PatternResult(
                            pattern_type="Resistance Level",
                            confidence=min(0.9, 0.5 + touches * 0.1),
                            description=f"Resistance at ${level:.2f} (tested {touches} times)",
                            start_index=len(df) - 50,
                            end_index=len(df) - 1,
                            key_levels=[level],
                            signal="bearish",
                            target_price=current_price * 0.98,
                            stop_loss=level * 1.01
                        ))
                    else:
                        # Support level
                        patterns.append(PatternResult(
                            pattern_type="Support Level",
                            confidence=min(0.9, 0.5 + touches * 0.1),
                            description=f"Support at ${level:.2f} (tested {touches} times)",
                            start_index=len(df) - 50,
                            end_index=len(df) - 1,
                            key_levels=[level],
                            signal="bullish",
                            target_price=current_price * 1.02,
                            stop_loss=level * 0.99
                        ))
                        
        except Exception as e:
            logger.error(f"Error detecting support/resistance: {e}")
        
        return patterns
    
    def _detect_macd_divergences(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect MACD divergences"""
        patterns = []
        try:
            price_peaks, _ = find_peaks(df['high'].values, distance=10)
            price_troughs, _ = find_peaks(-df['low'].values, distance=10)
            
            # Bullish MACD divergence
            if len(price_troughs) >= 2:
                for i in range(len(price_troughs) - 1):
                    trough1_idx = price_troughs[i]
                    trough2_idx = price_troughs[i + 1]
                    
                    if trough2_idx - trough1_idx < 50:
                        price1 = df.iloc[trough1_idx]['low']
                        price2 = df.iloc[trough2_idx]['low']
                        macd1 = df.iloc[trough1_idx]['macd']
                        macd2 = df.iloc[trough2_idx]['macd']
                        
                        if price2 < price1 and macd2 > macd1:
                            patterns.append(PatternResult(
                                pattern_type="Bullish MACD Divergence",
                                confidence=0.8,
                                description=f"MACD divergence: Price ${price1:.2f}→${price2:.2f}",
                                start_index=trough1_idx,
                                end_index=trough2_idx,
                                key_levels=[price1, price2],
                                signal="bullish",
                                target_price=price2 * 1.05,
                                stop_loss=price2 * 0.97
                            ))
        except Exception as e:
            logger.error(f"Error detecting MACD divergences: {e}")
        return patterns
    
    def _detect_wedges(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect rising and falling wedge patterns"""
        patterns = []
        try:
            if len(df) < 30:
                return patterns
            
            recent_data = df.tail(30)
            highs = recent_data['high'].values
            lows = recent_data['low'].values
            x = np.arange(len(recent_data))
            
            high_slope, _, high_r, _, _ = linregress(x, highs)
            low_slope, _, low_r, _, _ = linregress(x, lows)
            
            if abs(high_r) > 0.6 and abs(low_r) > 0.6:
                if high_slope > 0 and low_slope > 0 and high_slope < low_slope:
                    # Rising wedge (bearish)
                    patterns.append(PatternResult(
                        pattern_type="Rising Wedge",
                        confidence=0.7,
                        description="Rising wedge - bearish reversal pattern",
                        start_index=len(df) - 30,
                        end_index=len(df) - 1,
                        key_levels=[lows[-1], highs[-1]],
                        signal="bearish",
                        target_price=df.iloc[-1]['close'] * 0.95,
                        stop_loss=highs[-1] * 1.02
                    ))
                elif high_slope < 0 and low_slope < 0 and high_slope > low_slope:
                    # Falling wedge (bullish)
                    patterns.append(PatternResult(
                        pattern_type="Falling Wedge",
                        confidence=0.7,
                        description="Falling wedge - bullish reversal pattern",
                        start_index=len(df) - 30,
                        end_index=len(df) - 1,
                        key_levels=[lows[-1], highs[-1]],
                        signal="bullish",
                        target_price=df.iloc[-1]['close'] * 1.05,
                        stop_loss=lows[-1] * 0.98
                    ))
        except Exception as e:
            logger.error(f"Error detecting wedges: {e}")
        return patterns
    
    def _detect_channels(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect price channels"""
        patterns = []
        try:
            if len(df) < 40:
                return patterns
            
            recent_data = df.tail(40)
            highs = recent_data['high'].values
            lows = recent_data['low'].values
            x = np.arange(len(recent_data))
            
            high_slope, _, high_r, _, _ = linregress(x, highs)
            low_slope, _, low_r, _, _ = linregress(x, lows)
            
            # Parallel lines indicate channel
            if abs(high_r) > 0.7 and abs(low_r) > 0.7 and abs(high_slope - low_slope) < 0.05:
                if high_slope > 0.05:
                    pattern_type = "Ascending Channel"
                    signal = "bullish"
                elif high_slope < -0.05:
                    pattern_type = "Descending Channel"
                    signal = "bearish"
                else:
                    pattern_type = "Horizontal Channel"
                    signal = "neutral"
                
                patterns.append(PatternResult(
                    pattern_type=pattern_type,
                    confidence=0.65,
                    description=f"{pattern_type} - trend continuation",
                    start_index=len(df) - 40,
                    end_index=len(df) - 1,
                    key_levels=[lows[-1], highs[-1]],
                    signal=signal,
                    target_price=df.iloc[-1]['close'] * (1.03 if signal == "bullish" else 0.97 if signal == "bearish" else 1.0),
                    stop_loss=lows[-1] * 0.98 if signal == "bullish" else highs[-1] * 1.02
                ))
        except Exception as e:
            logger.error(f"Error detecting channels: {e}")
        return patterns
    
    def _detect_cup_handle(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect cup and handle patterns"""
        patterns = []
        try:
            if len(df) < 50:
                return patterns
            
            # Look for U-shaped pattern followed by small consolidation
            data = df.tail(50)
            prices = data['close'].values
            
            # Find the cup (U-shape)
            mid_point = len(prices) // 2
            left_high = np.max(prices[:10])
            right_high = np.max(prices[-10:])
            cup_low = np.min(prices[10:mid_point+10])
            
            # Cup criteria
            if (abs(left_high - right_high) / left_high < 0.05 and  # Similar highs
                (left_high - cup_low) / left_high > 0.15):  # Deep enough cup
                
                # Look for handle (small pullback)
                handle_data = prices[-15:]
                handle_high = np.max(handle_data[:5])
                handle_low = np.min(handle_data[-5:])
                
                if (handle_high - handle_low) / handle_high < 0.08:  # Small handle
                    patterns.append(PatternResult(
                        pattern_type="Cup and Handle",
                        confidence=0.75,
                        description=f"Cup and handle - bullish continuation",
                        start_index=len(df) - 50,
                        end_index=len(df) - 1,
                        key_levels=[cup_low, left_high, right_high],
                        signal="bullish",
                        target_price=right_high * 1.1,
                        stop_loss=handle_low * 0.95
                    ))
        except Exception as e:
            logger.error(f"Error detecting cup and handle: {e}")
        return patterns
    
    def _detect_inverse_head_shoulders(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect inverse head and shoulders (bullish reversal)"""
        patterns = []
        try:
            troughs, _ = find_peaks(-df['low'].values, distance=8, prominence=df['atr'].mean())
            
            if len(troughs) < 3:
                return patterns
            
            for i in range(len(troughs) - 2):
                left_shoulder = troughs[i]
                head = troughs[i + 1]
                right_shoulder = troughs[i + 2]
                
                ls_price = df.iloc[left_shoulder]['low']
                head_price = df.iloc[head]['low']
                rs_price = df.iloc[right_shoulder]['low']
                
                # Head should be lower than both shoulders
                if head_price < ls_price and head_price < rs_price:
                    if abs(ls_price - rs_price) / ls_price < 0.03:
                        patterns.append(PatternResult(
                            pattern_type="Inverse Head and Shoulders",
                            confidence=0.75,
                            description=f"Inverse H&S: Head ${head_price:.2f}, Shoulders ${ls_price:.2f}/${rs_price:.2f}",
                            start_index=left_shoulder,
                            end_index=right_shoulder,
                            key_levels=[ls_price, head_price, rs_price],
                            signal="bullish",
                            target_price=ls_price * 1.1,
                            stop_loss=head_price * 0.98
                        ))
        except Exception as e:
            logger.error(f"Error detecting inverse head and shoulders: {e}")
        return patterns
    
    def _detect_triple_tops_bottoms(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect triple top and triple bottom patterns"""
        patterns = []
        try:
            peaks, _ = find_peaks(df['high'].values, distance=5, prominence=df['atr'].mean())
            troughs, _ = find_peaks(-df['low'].values, distance=5, prominence=df['atr'].mean())
            
            # Triple tops
            if len(peaks) >= 3:
                for i in range(len(peaks) - 2):
                    peak1_idx, peak2_idx, peak3_idx = peaks[i], peaks[i+1], peaks[i+2]
                    if peak3_idx - peak1_idx < 80:  # Within reasonable distance
                        p1, p2, p3 = df.iloc[peak1_idx]['high'], df.iloc[peak2_idx]['high'], df.iloc[peak3_idx]['high']
                        if abs(p1 - p2) / p1 < 0.02 and abs(p2 - p3) / p2 < 0.02:
                            patterns.append(PatternResult(
                                pattern_type="Triple Top",
                                confidence=0.8,
                                description=f"Triple top at ${p1:.2f}, ${p2:.2f}, ${p3:.2f}",
                                start_index=peak1_idx,
                                end_index=peak3_idx,
                                key_levels=[p1, p2, p3],
                                signal="bearish",
                                target_price=p3 * 0.9,
                                stop_loss=p3 * 1.02
                            ))
            
            # Triple bottoms
            if len(troughs) >= 3:
                for i in range(len(troughs) - 2):
                    t1_idx, t2_idx, t3_idx = troughs[i], troughs[i+1], troughs[i+2]
                    if t3_idx - t1_idx < 80:
                        t1, t2, t3 = df.iloc[t1_idx]['low'], df.iloc[t2_idx]['low'], df.iloc[t3_idx]['low']
                        if abs(t1 - t2) / t1 < 0.02 and abs(t2 - t3) / t2 < 0.02:
                            patterns.append(PatternResult(
                                pattern_type="Triple Bottom",
                                confidence=0.8,
                                description=f"Triple bottom at ${t1:.2f}, ${t2:.2f}, ${t3:.2f}",
                                start_index=t1_idx,
                                end_index=t3_idx,
                                key_levels=[t1, t2, t3],
                                signal="bullish",
                                target_price=t3 * 1.1,
                                stop_loss=t3 * 0.98
                            ))
        except Exception as e:
            logger.error(f"Error detecting triple tops/bottoms: {e}")
        return patterns
    
    def _detect_breakouts(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect breakout patterns from consolidation"""
        patterns = []
        try:
            if len(df) < 20:
                return patterns
            
            # Look for consolidation followed by breakout
            recent_data = df.tail(20)
            consolidation = recent_data.iloc[:-5]  # First 15 candles
            breakout = recent_data.iloc[-5:]       # Last 5 candles
            
            # Check for consolidation (low volatility)
            cons_high = consolidation['high'].max()
            cons_low = consolidation['low'].min()
            cons_range = (cons_high - cons_low) / cons_low
            
            if cons_range < 0.05:  # Tight consolidation
                breakout_high = breakout['high'].max()
                breakout_low = breakout['low'].min()
                
                if breakout_high > cons_high * 1.02:  # Upward breakout
                    patterns.append(PatternResult(
                        pattern_type="Bullish Breakout",
                        confidence=0.7,
                        description=f"Breakout above ${cons_high:.2f}",
                        start_index=len(df) - 20,
                        end_index=len(df) - 1,
                        key_levels=[cons_low, cons_high],
                        signal="bullish",
                        target_price=cons_high * 1.05,
                        stop_loss=cons_low * 0.98
                    ))
                elif breakout_low < cons_low * 0.98:  # Downward breakout
                    patterns.append(PatternResult(
                        pattern_type="Bearish Breakout",
                        confidence=0.7,
                        description=f"Breakdown below ${cons_low:.2f}",
                        start_index=len(df) - 20,
                        end_index=len(df) - 1,
                        key_levels=[cons_low, cons_high],
                        signal="bearish",
                        target_price=cons_low * 0.95,
                        stop_loss=cons_high * 1.02
                    ))
        except Exception as e:
            logger.error(f"Error detecting breakouts: {e}")
        return patterns
    
    def _detect_elliott_waves(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect Elliott Wave patterns"""
        patterns = []
        try:
            if len(df) < 50:
                return patterns
            
            # Find significant peaks and troughs for wave analysis
            peaks, _ = find_peaks(df['high'].values, distance=8, prominence=df['atr'].mean())
            troughs, _ = find_peaks(-df['low'].values, distance=8, prominence=df['atr'].mean())
            
            # Combine and sort by index
            all_points = []
            for peak in peaks:
                all_points.append((peak, df.iloc[peak]['high'], 'peak'))
            for trough in troughs:
                all_points.append((trough, df.iloc[trough]['low'], 'trough'))
            
            all_points.sort(key=lambda x: x[0])
            
            # Look for 5-wave impulse patterns
            if len(all_points) >= 5:
                for i in range(len(all_points) - 4):
                    wave_points = all_points[i:i+5]
                    
                    # Check for alternating peaks and troughs
                    if (wave_points[0][2] != wave_points[1][2] and 
                        wave_points[1][2] != wave_points[2][2] and
                        wave_points[2][2] != wave_points[3][2] and
                        wave_points[3][2] != wave_points[4][2]):
                        
                        # Extract prices
                        prices = [point[1] for point in wave_points]
                        
                        # Check Elliott Wave rules (simplified)
                        if wave_points[0][2] == 'trough':  # Bullish impulse
                            if (prices[2] > prices[0] and  # Wave 3 > Wave 1
                                prices[4] > prices[2] and  # Wave 5 > Wave 3
                                prices[1] > prices[0] * 0.95 and  # Wave 2 doesn't retrace too much
                                prices[3] > prices[2] * 0.95):   # Wave 4 doesn't retrace too much
                                
                                patterns.append(PatternResult(
                                    pattern_type="Elliott Wave Impulse (Bullish)",
                                    confidence=0.7,
                                    description=f"5-wave bullish impulse pattern",
                                    start_index=wave_points[0][0],
                                    end_index=wave_points[4][0],
                                    key_levels=prices,
                                    signal="bullish",
                                    target_price=prices[4] * 1.1,
                                    stop_loss=prices[3] * 0.95
                                ))
                        
                        else:  # Bearish impulse
                            if (prices[2] < prices[0] and  # Wave 3 < Wave 1
                                prices[4] < prices[2] and  # Wave 5 < Wave 3
                                prices[1] < prices[0] * 1.05 and  # Wave 2 doesn't retrace too much
                                prices[3] < prices[2] * 1.05):   # Wave 4 doesn't retrace too much
                                
                                patterns.append(PatternResult(
                                    pattern_type="Elliott Wave Impulse (Bearish)",
                                    confidence=0.7,
                                    description=f"5-wave bearish impulse pattern",
                                    start_index=wave_points[0][0],
                                    end_index=wave_points[4][0],
                                    key_levels=prices,
                                    signal="bearish",
                                    target_price=prices[4] * 0.9,
                                    stop_loss=prices[3] * 1.05
                                ))
                                
        except Exception as e:
            logger.error(f"Error detecting Elliott waves: {e}")
        return patterns
    
    def _detect_fibonacci_retracements(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect Fibonacci retracement levels"""
        patterns = []
        try:
            if len(df) < 30:
                return patterns
            
            # Find recent significant high and low
            recent_data = df.tail(50)
            high_idx = recent_data['high'].idxmax()
            low_idx = recent_data['low'].idxmin()
            
            high_price = recent_data.loc[high_idx, 'high']
            low_price = recent_data.loc[low_idx, 'low']
            current_price = df.iloc[-1]['close']
            
            # Calculate Fibonacci levels
            price_range = high_price - low_price
            fib_levels = {
                '23.6%': high_price - (price_range * 0.236),
                '38.2%': high_price - (price_range * 0.382),
                '50.0%': high_price - (price_range * 0.500),
                '61.8%': high_price - (price_range * 0.618),
                '78.6%': high_price - (price_range * 0.786)
            }
            
            # Check if current price is near a Fibonacci level
            for level_name, level_price in fib_levels.items():
                if abs(current_price - level_price) / current_price < 0.02:  # Within 2%
                    
                    # Determine if it's support or resistance
                    if current_price < (high_price + low_price) / 2:
                        signal = "bullish"
                        description = f"Fibonacci support at {level_name} (${level_price:.2f})"
                    else:
                        signal = "bearish"
                        description = f"Fibonacci resistance at {level_name} (${level_price:.2f})"
                    
                    patterns.append(PatternResult(
                        pattern_type=f"Fibonacci {level_name} Level",
                        confidence=0.75,
                        description=description,
                        start_index=len(df) - 30,
                        end_index=len(df) - 1,
                        key_levels=[level_price, high_price, low_price],
                        signal=signal,
                        target_price=level_price * (1.03 if signal == "bullish" else 0.97),
                        stop_loss=level_price * (0.98 if signal == "bullish" else 1.02)
                    ))
                    
        except Exception as e:
            logger.error(f"Error detecting Fibonacci retracements: {e}")
        return patterns
    
    def _detect_gann_levels(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect Gann angle and time/price relationships"""
        patterns = []
        try:
            if len(df) < 40:
                return patterns
            
            # Find significant swing points
            recent_data = df.tail(40)
            peaks, _ = find_peaks(recent_data['high'].values, distance=5)
            troughs, _ = find_peaks(-recent_data['low'].values, distance=5)
            
            if len(peaks) >= 2 and len(troughs) >= 2:
                # Get most recent significant high and low
                last_peak_idx = peaks[-1]
                last_trough_idx = troughs[-1]
                
                peak_price = recent_data.iloc[last_peak_idx]['high']
                trough_price = recent_data.iloc[last_trough_idx]['low']
                
                # Calculate Gann angles (simplified)
                time_diff = abs(last_peak_idx - last_trough_idx)
                price_diff = abs(peak_price - trough_price)
                
                if time_diff > 0:
                    # Gann 1x1 angle (45 degrees)
                    gann_angle = price_diff / time_diff
                    current_price = df.iloc[-1]['close']
                    
                    # Project Gann levels
                    if last_peak_idx > last_trough_idx:  # Uptrend
                        projected_price = trough_price + (gann_angle * (len(recent_data) - 1 - last_trough_idx))
                        
                        if abs(current_price - projected_price) / current_price < 0.03:
                            patterns.append(PatternResult(
                                pattern_type="Gann 1x1 Angle Support",
                                confidence=0.65,
                                description=f"Price following Gann 1x1 uptrend line",
                                start_index=len(df) - 40,
                                end_index=len(df) - 1,
                                key_levels=[projected_price, peak_price, trough_price],
                                signal="bullish",
                                target_price=projected_price * 1.05,
                                stop_loss=projected_price * 0.97
                            ))
                    
                    else:  # Downtrend
                        projected_price = peak_price - (gann_angle * (len(recent_data) - 1 - last_peak_idx))
                        
                        if abs(current_price - projected_price) / current_price < 0.03:
                            patterns.append(PatternResult(
                                pattern_type="Gann 1x1 Angle Resistance",
                                confidence=0.65,
                                description=f"Price following Gann 1x1 downtrend line",
                                start_index=len(df) - 40,
                                end_index=len(df) - 1,
                                key_levels=[projected_price, peak_price, trough_price],
                                signal="bearish",
                                target_price=projected_price * 0.95,
                                stop_loss=projected_price * 1.03
                            ))
                            
        except Exception as e:
            logger.error(f"Error detecting Gann levels: {e}")
        return patterns
    
    def _detect_harmonic_patterns(self, df: pd.DataFrame) -> List[PatternResult]:
        """Detect harmonic patterns (Gartley, Butterfly, Bat, Crab)"""
        patterns = []
        try:
            if len(df) < 50:
                return patterns
            
            # Find significant peaks and troughs
            peaks, _ = find_peaks(df['high'].values, distance=8, prominence=df['atr'].mean())
            troughs, _ = find_peaks(-df['low'].values, distance=8, prominence=df['atr'].mean())
            
            # Combine and sort
            all_points = []
            for peak in peaks:
                all_points.append((peak, df.iloc[peak]['high'], 'peak'))
            for trough in troughs:
                all_points.append((trough, df.iloc[trough]['low'], 'trough'))
            
            all_points.sort(key=lambda x: x[0])
            
            # Look for ABCD patterns (simplified harmonic)
            if len(all_points) >= 4:
                for i in range(len(all_points) - 3):
                    points = all_points[i:i+4]
                    
                    # Check for alternating pattern
                    if (points[0][2] != points[1][2] and 
                        points[1][2] != points[2][2] and
                        points[2][2] != points[3][2]):
                        
                        # Extract prices and calculate ratios
                        A, B, C, D = [point[1] for point in points]
                        
                        # ABCD pattern ratios
                        AB = abs(B - A)
                        BC = abs(C - B)
                        CD = abs(D - C)
                        
                        if AB > 0 and BC > 0:
                            BC_AB_ratio = BC / AB
                            CD_AB_ratio = CD / AB if AB > 0 else 0
                            
                            # Check for harmonic ratios (simplified)
                            if (0.6 <= BC_AB_ratio <= 0.8 and  # BC retracement
                                1.2 <= CD_AB_ratio <= 1.6):   # CD extension
                                
                                signal = "bullish" if points[3][2] == 'trough' else "bearish"
                                
                                patterns.append(PatternResult(
                                    pattern_type="ABCD Harmonic Pattern",
                                    confidence=0.7,
                                    description=f"ABCD harmonic pattern with {BC_AB_ratio:.2f} retracement",
                                    start_index=points[0][0],
                                    end_index=points[3][0],
                                    key_levels=[A, B, C, D],
                                    signal=signal,
                                    target_price=D * (1.05 if signal == "bullish" else 0.95),
                                    stop_loss=D * (0.97 if signal == "bullish" else 1.03)
                                ))
                                
        except Exception as e:
            logger.error(f"Error detecting harmonic patterns: {e}")
        return patterns


class MultiTimeframePatternAnalyzer:
    """
    Multi-timeframe chart pattern analyzer
    Analyzes patterns across multiple timeframes for comprehensive analysis
    """
    
    def __init__(self):
        self.timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
        self.analyzer = ChartPatternAnalyzer()
        
    async def analyze_multi_timeframe_patterns(self, symbol: str, timeframes: List[str] = None) -> Dict[str, List[PatternResult]]:
        """
        Analyze chart patterns across multiple timeframes
        Returns dict with timeframe as key and patterns as value
        """
        if timeframes is None:
            timeframes = self.timeframes
            
        results = {}
        
        for timeframe in timeframes:
            try:
                patterns = await analyze_chart_patterns(symbol, timeframe, 100)
                results[timeframe] = patterns
                logger.info(f"📊 {timeframe}: Found {len(patterns)} patterns for {symbol}")
            except Exception as e:
                logger.error(f"Error analyzing {timeframe} patterns for {symbol}: {e}")
                results[timeframe] = []
        
        return results
    
    def get_consensus_signals(self, multi_tf_patterns: Dict[str, List[PatternResult]]) -> Dict[str, float]:
        """
        Get consensus signals across timeframes
        Returns bullish/bearish/neutral scores weighted by timeframe importance
        """
        # Timeframe weights (higher timeframes get more weight)
        tf_weights = {
            '1m': 0.05,
            '5m': 0.10,
            '15m': 0.15,
            '1h': 0.20,
            '4h': 0.25,
            '1d': 0.25
        }
        
        bullish_score = 0.0
        bearish_score = 0.0
        neutral_score = 0.0
        total_weight = 0.0
        
        for timeframe, patterns in multi_tf_patterns.items():
            if timeframe not in tf_weights:
                continue
                
            weight = tf_weights[timeframe]
            tf_bullish = 0.0
            tf_bearish = 0.0
            tf_neutral = 0.0
            
            for pattern in patterns:
                if pattern.signal == 'bullish':
                    tf_bullish += pattern.confidence
                elif pattern.signal == 'bearish':
                    tf_bearish += pattern.confidence
                else:
                    tf_neutral += pattern.confidence
            
            # Normalize by number of patterns
            if patterns:
                tf_bullish /= len(patterns)
                tf_bearish /= len(patterns)
                tf_neutral /= len(patterns)
            
            bullish_score += tf_bullish * weight
            bearish_score += tf_bearish * weight
            neutral_score += tf_neutral * weight
            total_weight += weight
        
        # Normalize scores
        if total_weight > 0:
            bullish_score /= total_weight
            bearish_score /= total_weight
            neutral_score /= total_weight
        
        return {
            'bullish': bullish_score,
            'bearish': bearish_score,
            'neutral': neutral_score,
            'dominant_signal': max(['bullish', 'bearish', 'neutral'], 
                                 key=lambda x: {'bullish': bullish_score, 'bearish': bearish_score, 'neutral': neutral_score}[x])
        }
    
    def get_key_levels_consensus(self, multi_tf_patterns: Dict[str, List[PatternResult]]) -> Dict[str, List[float]]:
        """
        Get consensus support and resistance levels across timeframes
        """
        all_support_levels = []
        all_resistance_levels = []
        
        for timeframe, patterns in multi_tf_patterns.items():
            for pattern in patterns:
                if pattern.pattern_type == "Support Level":
                    all_support_levels.extend(pattern.key_levels)
                elif pattern.pattern_type == "Resistance Level":
                    all_resistance_levels.extend(pattern.key_levels)
        
        # Cluster similar levels (within 1% of each other)
        def cluster_levels(levels, tolerance=0.01):
            if not levels:
                return []
            
            levels = sorted(levels)
            clusters = []
            current_cluster = [levels[0]]
            
            for level in levels[1:]:
                if abs(level - current_cluster[-1]) / current_cluster[-1] <= tolerance:
                    current_cluster.append(level)
                else:
                    clusters.append(sum(current_cluster) / len(current_cluster))
                    current_cluster = [level]
            
            clusters.append(sum(current_cluster) / len(current_cluster))
            return clusters
        
        return {
            'support_levels': cluster_levels(all_support_levels),
            'resistance_levels': cluster_levels(all_resistance_levels)
        }


# Integration functions for easy use
async def analyze_chart_patterns(symbol: str, timeframe: str = '4h', periods: int = 100) -> List[PatternResult]:
    """
    Analyze chart patterns for a given symbol on a single timeframe
    Returns list of detected patterns
    """
    try:
        # Get OHLCV data (reuse from openbb_provider)
        from .openbb_provider import OpenBBMarketDataProvider
        
        provider = OpenBBMarketDataProvider()
        ohlcv_data = await provider._get_ohlcv_data(symbol, timeframe, periods)
        
        if not ohlcv_data:
            logger.error(f"No OHLCV data for {symbol}")
            return []
        
        # Convert to DataFrame
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # Analyze patterns
        analyzer = ChartPatternAnalyzer()
        patterns = analyzer.analyze_patterns(df)
        
        logger.info(f"🔍 Found {len(patterns)} patterns for {symbol} on {timeframe}")
        return patterns
        
    except Exception as e:
        logger.error(f"Error analyzing chart patterns for {symbol}: {e}")
        return []

async def analyze_multi_timeframe_patterns(symbol: str, timeframes: List[str] = None) -> Dict[str, any]:
    """
    Comprehensive multi-timeframe pattern analysis
    Returns patterns, consensus signals, and key levels
    """
    analyzer = MultiTimeframePatternAnalyzer()
    
    # Get patterns across all timeframes
    multi_tf_patterns = await analyzer.analyze_multi_timeframe_patterns(symbol, timeframes)
    
    # Get consensus signals
    consensus = analyzer.get_consensus_signals(multi_tf_patterns)
    
    # Get key levels consensus
    key_levels = analyzer.get_key_levels_consensus(multi_tf_patterns)
    
    return {
        'patterns_by_timeframe': multi_tf_patterns,
        'consensus_signals': consensus,
        'key_levels': key_levels,
        'summary': {
            'total_patterns': sum(len(patterns) for patterns in multi_tf_patterns.values()),
            'dominant_signal': consensus['dominant_signal'],
            'signal_strength': max(consensus['bullish'], consensus['bearish'], consensus['neutral']),
            'support_levels_count': len(key_levels['support_levels']),
            'resistance_levels_count': len(key_levels['resistance_levels'])
        }
    }