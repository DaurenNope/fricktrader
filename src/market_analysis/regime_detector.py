"""
Advanced Market Regime Detection System
Identifies bull/bear/sideways markets using multiple sophisticated indicators
The foundation for intelligent multi-bot trading allocation
"""

import numpy as np
import pandas as pd
import talib.abstract as ta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    TRANSITION = "transition"

@dataclass
class RegimeSignal:
    regime: MarketRegime
    confidence: float  # 0-1
    strength: float    # 0-1
    duration: int      # periods in current regime
    signals: Dict[str, float]  # individual indicator signals
    recommendations: Dict[str, str]  # bot allocation recommendations

class AdvancedRegimeDetector:
    """
    Sophisticated market regime detection using:
    - Trend Analysis (multiple timeframes)
    - Volatility Regime Detection
    - Market Structure Analysis
    - Volume Profile Analysis
    - Smart Money Flow Detection
    """
    
    def __init__(self):
        self.regime_history = []
        self.current_regime = None
        self.regime_start_time = None
        
        # Regime detection parameters
        self.trend_lookback = 50
        self.volatility_lookback = 20
        self.regime_confirmation_periods = 3
        
        # Bot allocation weights per regime
        self.bot_allocations = {
            MarketRegime.BULL: {
                "momentum_bots": 0.4,      # Elliott Wave, Breakout Bots
                "smart_money_bots": 0.3,    # Smart Money Tracker
                "volatility_bots": 0.2,     # Volatility Surfer
                "mean_reversion_bots": 0.1  # Counter-trend (minimal)
            },
            MarketRegime.BEAR: {
                "momentum_bots": 0.2,       # Reduced momentum trading
                "smart_money_bots": 0.4,     # Follow smart money exits
                "volatility_bots": 0.1,      # Reduced vol trading
                "mean_reversion_bots": 0.3   # More counter-trend opportunities
            },
            MarketRegime.SIDEWAYS: {
                "momentum_bots": 0.1,       # Minimal breakout attempts
                "smart_money_bots": 0.2,     # Watch for accumulation
                "volatility_bots": 0.3,      # Range volatility
                "mean_reversion_bots": 0.4   # Range trading dominant
            },
            MarketRegime.TRANSITION: {
                "momentum_bots": 0.3,       # Catch potential breakouts
                "smart_money_bots": 0.5,     # Follow smart money lead
                "volatility_bots": 0.2,      # Prepare for vol expansion
                "mean_reversion_bots": 0.0   # Avoid counter-trend
            }
        }
    
    def analyze_market_regime(self, data: pd.DataFrame, pair: str = "BTC/USDT") -> RegimeSignal:
        """
        Comprehensive market regime analysis
        """
        try:
            # Calculate all regime indicators
            signals = {}
            
            # 1. Trend Analysis (multiple timeframes)
            signals['trend'] = self._analyze_trend_regime(data)
            
            # 2. Volatility Regime
            signals['volatility'] = self._analyze_volatility_regime(data)
            
            # 3. Market Structure
            signals['structure'] = self._analyze_market_structure(data)
            
            # 4. Volume Profile
            signals['volume'] = self._analyze_volume_regime(data)
            
            # 5. Smart Money Flow
            signals['smart_money'] = self._analyze_smart_money_regime(data)
            
            # 6. Momentum Regime
            signals['momentum'] = self._analyze_momentum_regime(data)
            
            # Composite regime determination
            regime, confidence, strength = self._determine_composite_regime(signals)
            
            # Calculate regime duration
            duration = self._calculate_regime_duration(regime)
            
            # Generate bot recommendations
            recommendations = self._generate_bot_recommendations(regime, signals)
            
            regime_signal = RegimeSignal(
                regime=regime,
                confidence=confidence,
                strength=strength,
                duration=duration,
                signals=signals,
                recommendations=recommendations
            )
            
            # Update regime history
            self._update_regime_history(regime_signal)
            
            logger.info(f"🌊 REGIME DETECTED for {pair}: {regime.value.upper()} "
                       f"(Confidence: {confidence:.2f}, Strength: {strength:.2f}, "
                       f"Duration: {duration} periods)")
            
            return regime_signal
            
        except Exception as e:
            logger.error(f"Error in regime analysis: {e}")
            return self._get_default_regime_signal()
    
    def _analyze_trend_regime(self, data: pd.DataFrame) -> float:
        """Trend analysis using multiple EMAs and slope detection"""
        try:
            # Multiple timeframe EMAs
            ema_8 = ta.EMA(data['close'], timeperiod=8)
            ema_21 = ta.EMA(data['close'], timeperiod=21)
            ema_50 = ta.EMA(data['close'], timeperiod=50)
            ema_200 = ta.EMA(data['close'], timeperiod=200)
            
            # Current price relative to EMAs
            current_price = data['close'].iloc[-1]
            
            # Trend alignment score
            trend_score = 0
            if current_price > ema_8.iloc[-1]: trend_score += 0.25
            if current_price > ema_21.iloc[-1]: trend_score += 0.25
            if current_price > ema_50.iloc[-1]: trend_score += 0.25
            if current_price > ema_200.iloc[-1]: trend_score += 0.25
            
            # EMA slope analysis
            ema_slope_21 = (ema_21.iloc[-1] - ema_21.iloc[-5]) / ema_21.iloc[-5]
            ema_slope_50 = (ema_50.iloc[-1] - ema_50.iloc[-10]) / ema_50.iloc[-10]
            
            # Adjust score based on slopes
            if ema_slope_21 > 0.02: trend_score += 0.1  # Strong uptrend
            elif ema_slope_21 < -0.02: trend_score -= 0.1  # Strong downtrend
            
            if ema_slope_50 > 0.01: trend_score += 0.05
            elif ema_slope_50 < -0.01: trend_score -= 0.05
            
            # Normalize to -1 to 1 (bull to bear)
            return np.clip(trend_score * 2 - 1, -1, 1)
            
        except Exception as e:
            logger.error(f"Error in trend analysis: {e}")
            return 0
    
    def _analyze_volatility_regime(self, data: pd.DataFrame) -> float:
        """Volatility regime detection"""
        try:
            # ATR-based volatility
            atr = ta.ATR(data, timeperiod=14)
            atr_pct = atr / data['close'] * 100
            
            # Rolling volatility percentiles
            vol_percentile = atr_pct.rolling(50).rank(pct=True).iloc[-1]
            
            # High vol = transition/bear, Low vol = sideways, Med vol = bull
            if vol_percentile > 0.8:
                return -0.5  # High vol (bearish/transition)
            elif vol_percentile < 0.2:
                return 0.0   # Low vol (sideways)
            else:
                return 0.3   # Medium vol (bullish)
                
        except Exception as e:
            logger.error(f"Error in volatility analysis: {e}")
            return 0
    
    def _analyze_market_structure(self, data: pd.DataFrame) -> float:
        """Market structure analysis (higher highs, higher lows)"""
        try:
            highs = data['high'].rolling(5).max()
            lows = data['low'].rolling(5).min()
            
            # Recent structure (last 10 periods)
            recent_highs = highs.tail(10)
            recent_lows = lows.tail(10)
            
            # Count higher highs and higher lows
            higher_highs = sum(recent_highs.diff() > 0)
            higher_lows = sum(recent_lows.diff() > 0)
            lower_highs = sum(recent_highs.diff() < 0)
            lower_lows = sum(recent_lows.diff() < 0)
            
            # Structure score
            bull_structure = (higher_highs + higher_lows) / 20
            bear_structure = (lower_highs + lower_lows) / 20
            
            return bull_structure - bear_structure
            
        except Exception as e:
            logger.error(f"Error in structure analysis: {e}")
            return 0
    
    def _analyze_volume_regime(self, data: pd.DataFrame) -> float:
        """Volume profile and flow analysis"""
        try:
            volume_sma = ta.SMA(data['volume'], timeperiod=20)
            volume_ratio = data['volume'] / volume_sma
            
            # Price-volume relationship
            price_change = data['close'].pct_change()
            volume_weighted_returns = (price_change * volume_ratio).rolling(10).mean()
            
            # Positive = accumulation, Negative = distribution
            return np.clip(volume_weighted_returns.iloc[-1] * 10, -1, 1)
            
        except Exception as e:
            logger.error(f"Error in volume analysis: {e}")
            return 0
    
    def _analyze_smart_money_regime(self, data: pd.DataFrame) -> float:
        """Smart money flow detection"""
        try:
            # VWAP analysis
            typical_price = (data['high'] + data['low'] + data['close']) / 3
            volume_price = typical_price * data['volume']
            vwap = volume_price.rolling(20).sum() / data['volume'].rolling(20).sum()
            
            # Price relative to VWAP
            vwap_distance = (data['close'] - vwap) / vwap
            
            # Smart money accumulation/distribution
            large_volume = data['volume'] > data['volume'].rolling(20).quantile(0.8)
            price_efficiency = (data['high'] - data['low']) / data['close'] < 0.02
            
            smart_money_activity = (large_volume & price_efficiency).rolling(10).mean()
            vwap_strength = vwap_distance.rolling(5).mean()
            
            return np.clip(vwap_strength.iloc[-1] + smart_money_activity.iloc[-1], -1, 1)
            
        except Exception as e:
            logger.error(f"Error in smart money analysis: {e}")
            return 0
    
    def _analyze_momentum_regime(self, data: pd.DataFrame) -> float:
        """Momentum regime analysis"""
        try:
            # RSI momentum
            rsi = ta.RSI(data['close'], timeperiod=14)
            rsi_normalized = (rsi.iloc[-1] - 50) / 50
            
            # Price momentum
            price_momentum = data['close'].pct_change(10).iloc[-1]
            
            # Combined momentum score
            momentum_score = (rsi_normalized + price_momentum * 10) / 2
            
            return np.clip(momentum_score, -1, 1)
            
        except Exception as e:
            logger.error(f"Error in momentum analysis: {e}")
            return 0
    
    def _determine_composite_regime(self, signals: Dict[str, float]) -> Tuple[MarketRegime, float, float]:
        """Determine overall regime from individual signals"""
        try:
            # Weighted composite score
            weights = {
                'trend': 0.3,
                'structure': 0.25,
                'smart_money': 0.2,
                'momentum': 0.15,
                'volume': 0.1,
                'volatility': 0.1
            }
            
            composite_score = sum(signals[key] * weights[key] for key in weights if key in signals)
            
            # Determine regime based on composite score
            if composite_score > 0.3:
                regime = MarketRegime.BULL
                confidence = min(composite_score, 0.95)
            elif composite_score < -0.3:
                regime = MarketRegime.BEAR
                confidence = min(abs(composite_score), 0.95)
            elif abs(composite_score) < 0.15:
                regime = MarketRegime.SIDEWAYS
                confidence = 1 - abs(composite_score) * 3
            else:
                regime = MarketRegime.TRANSITION
                confidence = 0.6
            
            # Calculate strength based on signal agreement
            signal_agreement = 1 - np.std(list(signals.values())) / 2
            strength = confidence * signal_agreement
            
            return regime, confidence, strength
            
        except Exception as e:
            logger.error(f"Error determining composite regime: {e}")
            return MarketRegime.SIDEWAYS, 0.5, 0.5
    
    def _calculate_regime_duration(self, current_regime: MarketRegime) -> int:
        """Calculate how long we've been in the current regime"""
        if self.current_regime != current_regime:
            self.current_regime = current_regime
            self.regime_start_time = 0
            return 0
        else:
            self.regime_start_time += 1
            return self.regime_start_time
    
    def _generate_bot_recommendations(self, regime: MarketRegime, signals: Dict[str, float]) -> Dict[str, str]:
        """Generate specific recommendations for bot allocation"""
        allocations = self.bot_allocations.get(regime, self.bot_allocations[MarketRegime.SIDEWAYS])
        
        recommendations = {
            "primary_strategy": regime.value,
            "momentum_allocation": f"{allocations['momentum_bots']:.1%}",
            "smart_money_allocation": f"{allocations['smart_money_bots']:.1%}",
            "volatility_allocation": f"{allocations['volatility_bots']:.1%}",
            "mean_reversion_allocation": f"{allocations['mean_reversion_bots']:.1%}",
            "focus_bots": self._get_focus_bots(regime, signals)
        }
        
        return recommendations
    
    def _get_focus_bots(self, regime: MarketRegime, signals: Dict[str, float]) -> str:
        """Determine which specific bots should be most active"""
        if regime == MarketRegime.BULL:
            if signals.get('momentum', 0) > 0.5:
                return "Elliott Wave Bot, Breakout Bot"
            else:
                return "Smart Money Tracker, Volatility Surfer"
        elif regime == MarketRegime.BEAR:
            return "Smart Money Tracker, Mean Reversion Bot"
        elif regime == MarketRegime.SIDEWAYS:
            return "Support/Resistance Bot, Mean Reversion Bot"
        else:  # TRANSITION
            return "Smart Money Tracker, Order Book Predator"
    
    def _update_regime_history(self, regime_signal: RegimeSignal):
        """Update regime history for learning"""
        self.regime_history.append({
            'timestamp': pd.Timestamp.now(),
            'regime': regime_signal.regime,
            'confidence': regime_signal.confidence,
            'strength': regime_signal.strength
        })
        
        # Keep only last 100 regime readings
        if len(self.regime_history) > 100:
            self.regime_history = self.regime_history[-100:]
    
    def _get_default_regime_signal(self) -> RegimeSignal:
        """Default regime signal in case of errors"""
        return RegimeSignal(
            regime=MarketRegime.SIDEWAYS,
            confidence=0.5,
            strength=0.5,
            duration=0,
            signals={},
            recommendations={"primary_strategy": "conservative"}
        )
    
    def get_regime_summary(self) -> Dict:
        """Get current regime summary for dashboard"""
        if not self.regime_history:
            return {"status": "No regime data available"}
        
        latest = self.regime_history[-1]
        
        return {
            "current_regime": latest['regime'].value,
            "confidence": f"{latest['confidence']:.2%}",
            "strength": f"{latest['strength']:.2%}",
            "duration": f"{self.regime_start_time} periods",
            "regime_changes_last_24h": len([r for r in self.regime_history[-24:] 
                                          if r['regime'] != latest['regime']])
        }