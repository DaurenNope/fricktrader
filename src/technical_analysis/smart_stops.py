#!/usr/bin/env python3
"""
Technical Analysis-Based Smart Stop Loss System

This module implements intelligent stop loss placement based on:
- Support/Resistance levels
- Market structure breaks
- Volume confirmation
- Multi-timeframe analysis
- ATR-based buffers

Replaces basic percentage stops with structure-aware logic.
"""

import pandas as pd
import numpy as np
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

class StopType(Enum):
    STRUCTURE = "structure"
    VOLUME = "volume"
    ATR = "atr"
    TIME = "time"
    HYBRID = "hybrid"

class TrendDirection(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"

@dataclass
class StopLevel:
    price: float
    stop_type: StopType
    confidence: float
    distance_pct: float
    reason: str
    timeframe: str

@dataclass
class StructureLevel:
    price: float
    level_type: str  # 'support', 'resistance', 'pivot'
    strength: float  # 0-1, based on touches and volume
    timeframe: str
    last_test: Optional[pd.Timestamp] = None
    volume_confirmation: bool = False

class TechnicalStopManager:
    """
    Advanced stop loss manager using technical analysis
    """
    
    def __init__(self, atr_multiplier: float = 1.5, min_stop_distance: float = 0.01):
        self.atr_multiplier = atr_multiplier
        self.min_stop_distance = min_stop_distance  # 1% minimum
        self.structure_levels = {}  # Cache structure levels by symbol
        
    def identify_structure_levels(self, 
                                data: pd.DataFrame,
                                symbol: str,
                                lookback_periods: int = 50) -> List[StructureLevel]:
        """
        Identify key support/resistance levels using multiple methods
        """
        
        levels = []
        
        # 1. Pivot point analysis
        pivot_levels = self._find_pivot_levels(data, lookback_periods)
        levels.extend(pivot_levels)
        
        # 2. Volume profile levels
        volume_levels = self._find_volume_levels(data, lookback_periods)
        levels.extend(volume_levels)
        
        # 3. Psychological levels (round numbers)
        psychological_levels = self._find_psychological_levels(data)
        levels.extend(psychological_levels)
        
        # 4. Moving average levels
        ma_levels = self._find_ma_levels(data)
        levels.extend(ma_levels)
        
        # Sort by strength and remove duplicates
        levels = self._consolidate_levels(levels)
        
        # Cache for later use
        self.structure_levels[symbol] = levels
        
        return levels
    
    def calculate_smart_stop(self,
                           entry_price: float,
                           position_side: str,  # 'long' or 'short'
                           data: pd.DataFrame,
                           symbol: str,
                           confidence_level: float = 0.8) -> StopLevel:
        """
        Calculate optimal stop loss based on technical analysis
        """
        
        # Get or calculate structure levels
        if symbol not in self.structure_levels:
            structure_levels = self.identify_structure_levels(data, symbol)
        else:
            structure_levels = self.structure_levels[symbol]
        
        # Calculate different stop options
        stop_options = []
        
        # 1. Structure-based stop
        structure_stop = self._calculate_structure_stop(
            entry_price, position_side, structure_levels, data
        )
        if structure_stop:
            stop_options.append(structure_stop)
        
        # 2. ATR-based stop (fallback)
        atr_stop = self._calculate_atr_stop(entry_price, position_side, data)
        stop_options.append(atr_stop)
        
        # 3. Volume-based stop
        volume_stop = self._calculate_volume_stop(entry_price, position_side, data)
        if volume_stop:
            stop_options.append(volume_stop)
        
        # 4. Hybrid approach
        hybrid_stop = self._calculate_hybrid_stop(entry_price, position_side, data, structure_levels)
        stop_options.append(hybrid_stop)
        
        # Select best stop based on confidence and risk/reward
        best_stop = self._select_optimal_stop(stop_options, confidence_level)
        
        return best_stop
    
    def _find_pivot_levels(self, data: pd.DataFrame, lookback: int) -> List[StructureLevel]:
        """Find pivot highs and lows as support/resistance"""
        
        levels = []
        
        # Calculate pivot points
        highs = data['high'].rolling(window=lookback, center=True).max()
        lows = data['low'].rolling(window=lookback, center=True).min()
        
        # Find significant pivots
        for i in range(lookback//2, len(data) - lookback//2):
            current_high = data['high'].iloc[i]
            current_low = data['low'].iloc[i]
            
            # Pivot high (resistance)
            if current_high == highs.iloc[i] and current_high > 0:
                # Calculate strength based on touches
                touches = self._count_level_touches(data, current_high, tolerance=0.002)
                volume_at_level = data['volume'].iloc[max(0, i-2):i+3].mean()
                
                strength = min(1.0, touches / 3.0 + volume_at_level / data['volume'].mean() * 0.3)
                
                levels.append(StructureLevel(
                    price=current_high,
                    level_type='resistance',
                    strength=strength,
                    timeframe='current',
                    last_test=data.index[i] if i < len(data) else None,
                    volume_confirmation=volume_at_level > data['volume'].mean() * 1.2
                ))
            
            # Pivot low (support)
            if current_low == lows.iloc[i] and current_low > 0:
                touches = self._count_level_touches(data, current_low, tolerance=0.002)
                volume_at_level = data['volume'].iloc[max(0, i-2):i+3].mean()
                
                strength = min(1.0, touches / 3.0 + volume_at_level / data['volume'].mean() * 0.3)
                
                levels.append(StructureLevel(
                    price=current_low,
                    level_type='support',
                    strength=strength,
                    timeframe='current',
                    last_test=data.index[i] if i < len(data) else None,
                    volume_confirmation=volume_at_level > data['volume'].mean() * 1.2
                ))
        
        return levels
    
    def _find_volume_levels(self, data: pd.DataFrame, lookback: int) -> List[StructureLevel]:
        """Find levels with high volume concentration"""
        
        levels = []
        
        # Create price bins and calculate volume at each level
        num_bins = min(50, len(data) // 10)  # Adaptive binning
        
        bins = np.linspace(data['low'].min(), data['high'].max(), num_bins)
        
        volume_profile = []
        for i in range(len(bins) - 1):
            low_bin = bins[i]
            high_bin = bins[i + 1]
            
            # Calculate volume in this price range
            mask = ((data['low'] <= high_bin) & (data['high'] >= low_bin))
            volume_in_range = data[mask]['volume'].sum()
            
            if volume_in_range > 0:
                volume_profile.append({
                    'price': (low_bin + high_bin) / 2,
                    'volume': volume_in_range
                })
        
        # Find high volume nodes (top 20%)
        if volume_profile:
            volumes = [vp['volume'] for vp in volume_profile]
            volume_threshold = np.percentile(volumes, 80)
            
            for vp in volume_profile:
                if vp['volume'] >= volume_threshold:
                    strength = min(1.0, vp['volume'] / max(volumes))
                    
                    # Determine if support or resistance based on current price
                    current_price = data['close'].iloc[-1]
                    level_type = 'support' if vp['price'] < current_price else 'resistance'
                    
                    levels.append(StructureLevel(
                        price=vp['price'],
                        level_type=level_type,
                        strength=strength,
                        timeframe='volume_profile',
                        volume_confirmation=True
                    ))
        
        return levels
    
    def _find_psychological_levels(self, data: pd.DataFrame) -> List[StructureLevel]:
        """Find psychological round number levels"""
        
        levels = []
        current_price = data['close'].iloc[-1]
        
        # Determine appropriate round number intervals based on price
        if current_price >= 100000:
            intervals = [10000, 5000]
        elif current_price >= 10000:
            intervals = [1000, 500]
        elif current_price >= 1000:
            intervals = [100, 50]
        elif current_price >= 100:
            intervals = [10, 5]
        else:
            intervals = [1, 0.5, 0.1]
        
        # Find nearby round numbers
        price_range = (data['high'].max(), data['low'].min())
        
        for interval in intervals:
            # Find round numbers within price range
            start_level = int(price_range[1] / interval) * interval
            end_level = int(price_range[0] / interval + 1) * interval
            
            level = start_level
            while level <= end_level:
                if price_range[1] <= level <= price_range[0]:
                    # Check if this level has been tested
                    touches = self._count_level_touches(data, level, tolerance=0.005)
                    
                    if touches >= 2:  # At least 2 touches to be significant
                        strength = min(0.7, touches / 5.0)  # Max 70% for psychological levels
                        level_type = 'support' if level < current_price else 'resistance'
                        
                        levels.append(StructureLevel(
                            price=level,
                            level_type=level_type,
                            strength=strength,
                            timeframe='psychological',
                            volume_confirmation=False
                        ))
                
                level += interval
        
        return levels
    
    def _find_ma_levels(self, data: pd.DataFrame) -> List[StructureLevel]:
        """Find moving average levels acting as support/resistance"""
        
        levels = []
        current_price = data['close'].iloc[-1]
        
        # Key moving averages that often act as S/R
        ma_periods = [20, 50, 100, 200]
        
        for period in ma_periods:
            if len(data) >= period:
                ma = data['close'].rolling(window=period).mean()
                current_ma = ma.iloc[-1]
                
                if not np.isnan(current_ma):
                    # Check how recently price interacted with this MA
                    recent_touches = 0
                    for i in range(max(0, len(data) - 20), len(data)):
                        if abs(data['close'].iloc[i] - ma.iloc[i]) / ma.iloc[i] < 0.01:  # Within 1%
                            recent_touches += 1
                    
                    if recent_touches >= 2:
                        strength = min(0.8, recent_touches / 10.0 + period / 500.0)
                        level_type = 'support' if current_ma < current_price else 'resistance'
                        
                        levels.append(StructureLevel(
                            price=current_ma,
                            level_type=level_type,
                            strength=strength,
                            timeframe=f'MA{period}',
                            volume_confirmation=False
                        ))
        
        return levels
    
    def _count_level_touches(self, data: pd.DataFrame, level: float, tolerance: float = 0.002) -> int:
        """Count how many times price touched a level"""
        
        touches = 0
        tolerance_abs = level * tolerance
        
        for i in range(len(data)):
            high = data['high'].iloc[i]
            low = data['low'].iloc[i]
            
            # Check if candle touched the level
            if low <= level + tolerance_abs and high >= level - tolerance_abs:
                touches += 1
        
        return touches
    
    def _consolidate_levels(self, levels: List[StructureLevel]) -> List[StructureLevel]:
        """Remove duplicate/close levels and sort by strength"""
        
        if not levels:
            return levels
        
        # Sort by price
        levels.sort(key=lambda x: x.price)
        
        consolidated = []
        
        for level in levels:
            # Check if we already have a similar level
            similar_found = False
            
            for existing in consolidated:
                price_diff = abs(level.price - existing.price) / existing.price
                if price_diff < 0.005:  # Within 0.5%
                    # Keep the stronger level
                    if level.strength > existing.strength:
                        consolidated.remove(existing)
                        consolidated.append(level)
                    similar_found = True
                    break
            
            if not similar_found:
                consolidated.append(level)
        
        # Sort by strength (strongest first)
        consolidated.sort(key=lambda x: x.strength, reverse=True)
        
        return consolidated[:10]  # Keep top 10 levels
    
    def _calculate_structure_stop(self,
                                entry_price: float,
                                position_side: str,
                                levels: List[StructureLevel],
                                data: pd.DataFrame) -> Optional[StopLevel]:
        """Calculate stop based on nearest structure level"""
        
        if not levels:
            return None
        
        atr = data['high'].subtract(data['low']).rolling(14).mean().iloc[-1]
        
        if position_side == 'long':
            # Find nearest support level below entry
            support_levels = [level for level in levels if level.level_type == 'support' and level.price < entry_price]
            
            if support_levels:
                # Get the strongest support level closest to entry
                best_support = max(support_levels, key=lambda x: x.strength * (1 - abs(x.price - entry_price) / entry_price))
                
                # Place stop slightly below support with ATR buffer
                buffer = min(atr * 0.5, entry_price * 0.01)  # Smaller of 0.5 ATR or 1%
                stop_price = best_support.price - buffer
                
                distance_pct = abs(entry_price - stop_price) / entry_price
                
                # Ensure minimum distance
                if distance_pct >= self.min_stop_distance:
                    return StopLevel(
                        price=stop_price,
                        stop_type=StopType.STRUCTURE,
                        confidence=best_support.strength,
                        distance_pct=distance_pct,
                        reason=f"Below {best_support.level_type} at {best_support.price:.2f}",
                        timeframe=best_support.timeframe
                    )
        
        else:  # short position
            # Find nearest resistance level above entry
            resistance_levels = [level for level in levels if level.level_type == 'resistance' and level.price > entry_price]
            
            if resistance_levels:
                best_resistance = max(resistance_levels, key=lambda x: x.strength * (1 - abs(x.price - entry_price) / entry_price))
                
                buffer = min(atr * 0.5, entry_price * 0.01)
                stop_price = best_resistance.price + buffer
                
                distance_pct = abs(stop_price - entry_price) / entry_price
                
                if distance_pct >= self.min_stop_distance:
                    return StopLevel(
                        price=stop_price,
                        stop_type=StopType.STRUCTURE,
                        confidence=best_resistance.strength,
                        distance_pct=distance_pct,
                        reason=f"Above {best_resistance.level_type} at {best_resistance.price:.2f}",
                        timeframe=best_resistance.timeframe
                    )
        
        return None
    
    def _calculate_atr_stop(self, entry_price: float, position_side: str, data: pd.DataFrame) -> StopLevel:
        """Calculate ATR-based stop as fallback"""
        
        atr = data['high'].subtract(data['low']).rolling(14).mean().iloc[-1]
        
        if position_side == 'long':
            stop_price = entry_price - (atr * self.atr_multiplier)
        else:
            stop_price = entry_price + (atr * self.atr_multiplier)
        
        distance_pct = abs(entry_price - stop_price) / entry_price
        
        return StopLevel(
            price=stop_price,
            stop_type=StopType.ATR,
            confidence=0.6,  # Medium confidence for ATR stops
            distance_pct=distance_pct,
            reason=f"ATR-based stop ({self.atr_multiplier:.1f}x ATR)",
            timeframe="14-period"
        )
    
    def _calculate_volume_stop(self, entry_price: float, position_side: str, data: pd.DataFrame) -> Optional[StopLevel]:
        """Calculate stop based on volume patterns"""
        
        # Look for volume spikes that might indicate support/resistance
        volume_sma = data['volume'].rolling(20).mean()
        volume_spikes = data[data['volume'] > volume_sma * 2.0]  # 2x average volume
        
        if len(volume_spikes) == 0:
            return None
        
        recent_spikes = volume_spikes.tail(10)  # Last 10 volume spikes
        
        if position_side == 'long':
            # Find volume spikes below entry price (potential support)
            support_spikes = recent_spikes[recent_spikes['low'] < entry_price]
            if not support_spikes.empty:
                stop_price = support_spikes['low'].max() * 0.995  # 0.5% below highest low with volume spike
                distance_pct = abs(entry_price - stop_price) / entry_price
                
                if distance_pct >= self.min_stop_distance:
                    return StopLevel(
                        price=stop_price,
                        stop_type=StopType.VOLUME,
                        confidence=0.7,
                        distance_pct=distance_pct,
                        reason="Below volume spike support",
                        timeframe="volume_analysis"
                    )
        else:
            # Find volume spikes above entry price (potential resistance)
            resistance_spikes = recent_spikes[recent_spikes['high'] > entry_price]
            if not resistance_spikes.empty:
                stop_price = resistance_spikes['high'].min() * 1.005
                distance_pct = abs(stop_price - entry_price) / entry_price
                
                if distance_pct >= self.min_stop_distance:
                    return StopLevel(
                        price=stop_price,
                        stop_type=StopType.VOLUME,
                        confidence=0.7,
                        distance_pct=distance_pct,
                        reason="Above volume spike resistance",
                        timeframe="volume_analysis"
                    )
        
        return None
    
    def _calculate_hybrid_stop(self,
                             entry_price: float,
                             position_side: str,
                             data: pd.DataFrame,
                             levels: List[StructureLevel]) -> StopLevel:
        """Calculate hybrid stop combining multiple methods"""
        
        # Get ATR stop as base
        atr_stop = self._calculate_atr_stop(entry_price, position_side, data)
        
        # Try to improve with structure
        structure_stop = self._calculate_structure_stop(entry_price, position_side, levels, data)
        
        if structure_stop and structure_stop.confidence > 0.7:
            # Use structure stop if high confidence and reasonable distance
            if 0.01 <= structure_stop.distance_pct <= 0.08:  # Between 1-8%
                return StopLevel(
                    price=structure_stop.price,
                    stop_type=StopType.HYBRID,
                    confidence=min(0.9, (structure_stop.confidence + atr_stop.confidence) / 2),
                    distance_pct=structure_stop.distance_pct,
                    reason=f"Hybrid: {structure_stop.reason} + ATR confirmation",
                    timeframe="multi_method"
                )
        
        # Otherwise, use ATR with slight improvement
        return StopLevel(
            price=atr_stop.price,
            stop_type=StopType.HYBRID,
            confidence=atr_stop.confidence,
            distance_pct=atr_stop.distance_pct,
            reason="Hybrid: ATR-based with structure analysis",
            timeframe="multi_method"
        )
    
    def _select_optimal_stop(self, stop_options: List[StopLevel], confidence_threshold: float) -> StopLevel:
        """Select the best stop from available options"""
        
        # Filter by confidence
        high_confidence_stops = [s for s in stop_options if s.confidence >= confidence_threshold]
        
        if high_confidence_stops:
            # Among high confidence stops, prefer structure-based, then hybrid
            structure_stops = [s for s in high_confidence_stops if s.stop_type == StopType.STRUCTURE]
            if structure_stops:
                return min(structure_stops, key=lambda x: x.distance_pct)
            
            hybrid_stops = [s for s in high_confidence_stops if s.stop_type == StopType.HYBRID]
            if hybrid_stops:
                return min(hybrid_stops, key=lambda x: x.distance_pct)
            
            # Otherwise, pick highest confidence
            return max(high_confidence_stops, key=lambda x: x.confidence)
        
        # If no high confidence stops, pick the best available
        return max(stop_options, key=lambda x: x.confidence)

def demo_smart_stops():
    """Demonstrate smart stop loss system"""
    print("🎯 TECHNICAL ANALYSIS SMART STOPS DEMO")
    print("=" * 45)
    
    # Generate sample data
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=720, freq='H')
    np.random.seed(42)
    
    # Simulate realistic price data
    base_price = 45000
    returns = np.random.normal(0.0001, 0.02, len(dates))
    prices = [base_price]
    
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    data = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.005))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.005))) for p in prices],
        'close': prices,
        'volume': np.random.normal(1000000, 200000, len(dates))
    }, index=dates)
    
    # Initialize smart stop manager
    stop_manager = TechnicalStopManager()
    
    # Simulate long position entry
    entry_price = data['close'].iloc[-1]
    print("\n📊 Position Analysis:")
    print(f"Current Price: ${entry_price:,.2f}")
    print("Position: LONG (simulated entry)")
    
    # Calculate smart stop
    smart_stop = stop_manager.calculate_smart_stop(
        entry_price=entry_price,
        position_side='long',
        data=data,
        symbol='BTC/USDT',
        confidence_level=0.7
    )
    
    print("\n🎯 Smart Stop Analysis:")
    print(f"Stop Price: ${smart_stop.price:,.2f}")
    print(f"Stop Type: {smart_stop.stop_type.value.upper()}")
    print(f"Distance: {smart_stop.distance_pct:.2%}")
    print(f"Confidence: {smart_stop.confidence:.1%}")
    print(f"Reason: {smart_stop.reason}")
    print(f"Timeframe: {smart_stop.timeframe}")
    
    # Show structure levels found
    if 'BTC/USDT' in stop_manager.structure_levels:
        levels = stop_manager.structure_levels['BTC/USDT']
        print("\n🏗️ Key Structure Levels Found:")
        for i, level in enumerate(levels[:5]):
            print(f"  {i+1}. ${level.price:,.2f} - {level.level_type.upper()} "
                  f"(Strength: {level.strength:.1%}, {level.timeframe})")
    
    # Compare with basic stop
    basic_stop = entry_price * 0.95  # 5% stop
    print("\n📈 Comparison:")
    print(f"Basic Stop (5%): ${basic_stop:,.2f}")
    print(f"Smart Stop: ${smart_stop.price:,.2f}")
    print(f"Improvement: {abs(smart_stop.distance_pct - 0.05) / 0.05:.1%} "
          f"{'better' if smart_stop.distance_pct < 0.05 else 'conservative'}")

if __name__ == "__main__":
    demo_smart_stops()