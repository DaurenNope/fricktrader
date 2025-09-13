"""
Crypto Market Regime Analyzer - Critical Component
Determines market regime, volatility regime, and risk environment
to enable/disable strategies dynamically based on market conditions.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    TRANSITIONAL = "transitional"

class VolatilityRegime(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXPLOSIVE = "explosive"

class RiskEnvironment(Enum):
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    NEUTRAL = "neutral"

class FundamentalHealth(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    DETERIORATING = "deteriorating"

@dataclass
class MarketRegimeResult:
    """Complete market analysis result"""
    market_regime: MarketRegime
    volatility_regime: VolatilityRegime
    risk_environment: RiskEnvironment
    fundamental_health: FundamentalHealth
    confidence_score: float
    regime_duration: int  # days in current regime
    signals: Dict[str, float]  # detailed signal breakdown
    timestamp: datetime

class CryptoMarketRegimeAnalyzer:
    """
    Master analyzer that determines:
    1. Market Regime: Bull/Bear/Sideways/Transitional
    2. Volatility Regime: High/Low/Normal/Explosive  
    3. Risk Environment: Risk-On/Risk-Off/Neutral
    4. Fundamental Health: Healthy/Warning/Deteriorating
    """
    
    def __init__(self, 
                 lookback_days: int = 30,
                 regime_confidence_threshold: float = 0.7):
        self.lookback_days = lookback_days
        self.regime_confidence_threshold = regime_confidence_threshold
        self._current_regime = None
        self._regime_start_date = None
        
    def analyze_market_regime(self, data: Dict[str, pd.DataFrame]) -> MarketRegimeResult:
        """
        Main analysis method that combines all signals to determine market regime
        
        Args:
            data: Dict containing 'BTC', 'ETH', 'total_market_cap' DataFrames
                  with OHLCV + volume data
        """
        try:
            # Extract key market data
            btc_data = data.get('BTC')
            eth_data = data.get('ETH')
            market_cap_data = data.get('total_market_cap')
            
            if btc_data is None or len(btc_data) < 50:
                raise ValueError("Insufficient BTC data for regime analysis")
            
            # 1. Analyze weekly/monthly trends (highest timeframes)
            higher_tf_signals = self._analyze_higher_timeframes(btc_data)
            
            # 2. Detect market structure (trend analysis)
            market_structure = self._analyze_market_structure(btc_data, eth_data)
            
            # 3. Analyze volatility regime
            volatility_analysis = self._analyze_volatility_regime(btc_data)
            
            # 4. Risk environment analysis
            risk_analysis = self._analyze_risk_environment(btc_data, market_cap_data)
            
            # 5. Volume and momentum analysis
            volume_momentum = self._analyze_volume_momentum(btc_data)
            
            # 6. Combine all signals
            combined_signals = {
                **higher_tf_signals,
                **market_structure,
                **volatility_analysis,
                **risk_analysis,
                **volume_momentum
            }
            
            # 7. Determine final regime
            market_regime = self._determine_market_regime(combined_signals)
            volatility_regime = self._determine_volatility_regime(combined_signals)
            risk_environment = self._determine_risk_environment(combined_signals)
            fundamental_health = self._determine_fundamental_health(combined_signals)
            
            # 8. Calculate confidence score
            confidence_score = self._calculate_confidence_score(combined_signals, market_regime)
            
            # 9. Track regime duration
            regime_duration = self._update_regime_duration(market_regime)
            
            return MarketRegimeResult(
                market_regime=market_regime,
                volatility_regime=volatility_regime,
                risk_environment=risk_environment,
                fundamental_health=fundamental_health,
                confidence_score=confidence_score,
                regime_duration=regime_duration,
                signals=combined_signals,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in market regime analysis: {e}")
            # Return conservative neutral state on error
            return self._get_neutral_regime()
    
    def _analyze_higher_timeframes(self, btc_data: pd.DataFrame) -> Dict[str, float]:
        """Analyze weekly/monthly trends from highest timeframes"""
        signals = {}
        
        # Resample to weekly data for higher timeframe analysis
        btc_weekly = btc_data.resample('1W').agg({
            'open': 'first',
            'high': 'max', 
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        if len(btc_weekly) < 12:  # Need at least 3 months of weekly data
            signals['higher_tf_trend'] = 0.0
            return signals
        
        # Weekly trend analysis
        
        # Higher highs, higher lows pattern
        highs = btc_weekly['high'].tail(8)
        lows = btc_weekly['low'].tail(8)
        
        # Count higher highs
        higher_highs = sum([highs.iloc[i] > highs.iloc[i-1] for i in range(1, len(highs))])
        higher_lows = sum([lows.iloc[i] > lows.iloc[i-1] for i in range(1, len(lows))])
        
        # Weekly EMA trend
        weekly_ema_21 = btc_weekly['close'].ewm(span=21).mean()
        weekly_ema_50 = btc_weekly['close'].ewm(span=50).mean()
        
        trend_alignment = 1.0 if weekly_ema_21.iloc[-1] > weekly_ema_50.iloc[-1] else -1.0
        
        # Weekly volume trend (increasing = bullish)
        volume_trend = btc_weekly['volume'].rolling(4).mean().pct_change().mean()
        
        # Combine weekly signals
        weekly_trend_score = (
            (higher_highs - 3.5) * 0.3 +  # Expect ~4 higher highs in uptrend
            (higher_lows - 3.5) * 0.3 +   # Expect ~4 higher lows in uptrend
            trend_alignment * 0.25 +
            np.clip(volume_trend * 10, -1, 1) * 0.15
        )
        
        signals['higher_tf_trend'] = np.clip(weekly_trend_score, -1.0, 1.0)
        signals['weekly_volume_trend'] = np.clip(volume_trend * 10, -1.0, 1.0)
        signals['weekly_ema_alignment'] = trend_alignment
        
        return signals
    
    def _analyze_market_structure(self, btc_data: pd.DataFrame, eth_data: Optional[pd.DataFrame]) -> Dict[str, float]:
        """Analyze market structure patterns"""
        signals = {}
        
        # BTC market structure
        
        # Swing highs and lows analysis  
        swing_period = 10
        
        # Find swing highs/lows
        highs = btc_data['high'].rolling(swing_period*2+1, center=True).max()
        lows = btc_data['low'].rolling(swing_period*2+1, center=True).min()
        
        swing_highs = (btc_data['high'] == highs).tail(20)
        swing_lows = (btc_data['low'] == lows).tail(20)
        
        # Count higher highs vs lower highs
        high_prices = btc_data['high'][swing_highs].dropna()
        low_prices = btc_data['low'][swing_lows].dropna()
        
        if len(high_prices) > 2 and len(low_prices) > 2:
            # Higher highs pattern
            hh_count = sum([high_prices.iloc[i] > high_prices.iloc[i-1] 
                           for i in range(1, min(6, len(high_prices)))])
            
            # Higher lows pattern  
            hl_count = sum([low_prices.iloc[i] > low_prices.iloc[i-1]
                           for i in range(1, min(6, len(low_prices)))])
            
            structure_bullish = (hh_count + hl_count) / 10.0  # Normalize
        else:
            structure_bullish = 0.0
        
        signals['market_structure'] = np.clip(structure_bullish, -1.0, 1.0)
        
        # Add ETH correlation analysis if available
        if eth_data is not None and len(eth_data) == len(btc_data):
            correlation = btc_data['close'].tail(30).corr(eth_data['close'].tail(30))
            signals['btc_eth_correlation'] = correlation
            
            # ETH/BTC ratio trend
            eth_btc_ratio = eth_data['close'] / btc_data['close']
            ratio_trend = eth_btc_ratio.tail(20).pct_change().mean()
            signals['eth_btc_ratio_trend'] = np.clip(ratio_trend * 100, -1.0, 1.0)
        
        return signals
    
    def _analyze_volatility_regime(self, btc_data: pd.DataFrame) -> Dict[str, float]:
        """Analyze volatility regime and patterns"""
        signals = {}
        
        # ATR analysis across multiple periods
        btc_data = btc_data.copy()
        btc_data['atr_14'] = self._calculate_atr(btc_data, 14)
        btc_data['atr_30'] = self._calculate_atr(btc_data, 30)
        
        # ATR percentile ranking (current vs historical)
        atr_current = btc_data['atr_14'].iloc[-1]
        atr_percentile = (btc_data['atr_14'].tail(100) <= atr_current).mean()
        
        # Volatility trend (increasing/decreasing)
        vol_trend = btc_data['atr_14'].tail(10).pct_change().mean()
        
        # Bollinger Band squeeze analysis
        bb_period = 20
        bb_std = 2
        
        bb_middle = btc_data['close'].rolling(bb_period).mean()
        bb_std_dev = btc_data['close'].rolling(bb_period).std()
        bb_upper = bb_middle + (bb_std_dev * bb_std)
        bb_lower = bb_middle - (bb_std_dev * bb_std)
        
        # Band width (measure of volatility)
        band_width = (bb_upper - bb_lower) / bb_middle
        band_width_percentile = (band_width.tail(100) <= band_width.iloc[-1]).mean()
        
        # Determine volatility regime signals
        if atr_percentile > 0.8:
            vol_regime_score = 1.0  # High volatility
        elif atr_percentile < 0.2:
            vol_regime_score = -1.0  # Low volatility
        else:
            vol_regime_score = 0.0  # Normal volatility
        
        signals['volatility_regime'] = vol_regime_score
        signals['volatility_trend'] = np.clip(vol_trend * 10, -1.0, 1.0)
        signals['bollinger_squeeze'] = -1.0 if band_width_percentile < 0.2 else 0.0
        signals['atr_percentile'] = atr_percentile
        
        return signals
    
    def _analyze_risk_environment(self, btc_data: pd.DataFrame, 
                                market_cap_data: Optional[pd.DataFrame]) -> Dict[str, float]:
        """Analyze risk-on vs risk-off environment"""
        signals = {}
        
        # BTC momentum as risk proxy
        btc_returns = btc_data['close'].pct_change()
        momentum_10d = btc_returns.tail(10).mean()
        momentum_30d = btc_returns.tail(30).mean()
        
        # Volume analysis (risk-on = higher volume)
        volume_ma = btc_data['volume'].rolling(20).mean()
        volume_current = btc_data['volume'].tail(5).mean()
        volume_ratio = volume_current / volume_ma.iloc[-1]
        
        # Price stability analysis
        price_stability = 1 - btc_data['close'].tail(7).std() / btc_data['close'].tail(7).mean()
        
        # Risk environment scoring
        risk_score = (
            np.clip(momentum_10d * 100, -1, 1) * 0.4 +
            np.clip(momentum_30d * 50, -1, 1) * 0.3 +
            np.clip((volume_ratio - 1), -1, 1) * 0.2 +
            np.clip((price_stability - 0.95) * 20, -1, 1) * 0.1
        )
        
        signals['risk_environment'] = risk_score
        signals['momentum_10d'] = momentum_10d
        signals['volume_relative'] = volume_ratio - 1
        
        return signals
    
    def _analyze_volume_momentum(self, btc_data: pd.DataFrame) -> Dict[str, float]:
        """Analyze volume and momentum patterns"""
        signals = {}
        
        # Volume trend analysis
        volume_ma_5 = btc_data['volume'].rolling(5).mean()
        volume_ma_20 = btc_data['volume'].rolling(20).mean()
        volume_trend = (volume_ma_5 / volume_ma_20 - 1).iloc[-1]
        
        # Price-volume relationship
        price_change = btc_data['close'].pct_change().tail(10)
        volume_change = btc_data['volume'].pct_change().tail(10)
        
        # Positive correlation = healthy (price up with volume up)
        pv_correlation = price_change.corr(volume_change)
        
        # RSI momentum
        rsi = self._calculate_rsi(btc_data['close'], 14)
        rsi_current = rsi.iloc[-1]
        rsi_trend = rsi.tail(5).mean() - rsi.tail(10).head(5).mean()
        
        signals['volume_trend'] = np.clip(volume_trend, -1.0, 1.0)
        signals['price_volume_correlation'] = pv_correlation if not np.isnan(pv_correlation) else 0.0
        signals['rsi_momentum'] = np.clip((rsi_current - 50) / 50, -1.0, 1.0)
        signals['rsi_trend'] = np.clip(rsi_trend / 10, -1.0, 1.0)
        
        return signals
    
    def _determine_market_regime(self, signals: Dict[str, float]) -> MarketRegime:
        """Determine overall market regime from combined signals"""
        
        # Key signals for regime determination
        trend_score = signals.get('higher_tf_trend', 0.0) * 0.3
        structure_score = signals.get('market_structure', 0.0) * 0.25
        momentum_score = signals.get('momentum_10d', 0.0) * 100 * 0.2
        volume_score = signals.get('volume_trend', 0.0) * 0.15
        risk_score = signals.get('risk_environment', 0.0) * 0.1
        
        total_score = trend_score + structure_score + momentum_score + volume_score + risk_score
        
        if total_score > 0.5:
            return MarketRegime.BULL
        elif total_score < -0.5:
            return MarketRegime.BEAR
        elif abs(total_score) < 0.2:
            return MarketRegime.SIDEWAYS
        else:
            return MarketRegime.TRANSITIONAL
    
    def _determine_volatility_regime(self, signals: Dict[str, float]) -> VolatilityRegime:
        """Determine volatility regime"""
        vol_score = signals.get('volatility_regime', 0.0)
        atr_percentile = signals.get('atr_percentile', 0.5)
        
        if atr_percentile > 0.9 or vol_score > 0.8:
            return VolatilityRegime.EXPLOSIVE
        elif atr_percentile > 0.7 or vol_score > 0.3:
            return VolatilityRegime.HIGH
        elif atr_percentile < 0.3 or vol_score < -0.3:
            return VolatilityRegime.LOW
        else:
            return VolatilityRegime.NORMAL
    
    def _determine_risk_environment(self, signals: Dict[str, float]) -> RiskEnvironment:
        """Determine risk environment"""
        risk_score = signals.get('risk_environment', 0.0)
        
        if risk_score > 0.3:
            return RiskEnvironment.RISK_ON
        elif risk_score < -0.3:
            return RiskEnvironment.RISK_OFF
        else:
            return RiskEnvironment.NEUTRAL
    
    def _determine_fundamental_health(self, signals: Dict[str, float]) -> FundamentalHealth:
        """Determine fundamental health (placeholder - would integrate on-chain data)"""
        # For now, base on technical health
        trend_health = signals.get('higher_tf_trend', 0.0)
        volume_health = signals.get('price_volume_correlation', 0.0)
        momentum_health = signals.get('momentum_30d', 0.0) * 100
        
        health_score = (trend_health * 0.4 + volume_health * 0.3 + momentum_health * 0.3)
        
        if health_score > 0.4:
            return FundamentalHealth.HEALTHY
        elif health_score < -0.4:
            return FundamentalHealth.DETERIORATING
        else:
            return FundamentalHealth.WARNING
    
    def _calculate_confidence_score(self, signals: Dict[str, float], regime: MarketRegime) -> float:
        """Calculate confidence in regime determination"""
        # Check signal alignment
        key_signals = [
            signals.get('higher_tf_trend', 0.0),
            signals.get('market_structure', 0.0),
            signals.get('risk_environment', 0.0),
            signals.get('volume_trend', 0.0)
        ]
        
        # Check if signals agree on direction
        positive_signals = sum([1 for s in key_signals if s > 0.2])
        negative_signals = sum([1 for s in key_signals if s < -0.2])
        
        agreement_score = max(positive_signals, negative_signals) / len(key_signals)
        
        # Penalize transitional regimes
        regime_penalty = 0.2 if regime == MarketRegime.TRANSITIONAL else 0.0
        
        confidence = max(0.3, agreement_score - regime_penalty)
        return round(confidence, 2)
    
    def _update_regime_duration(self, current_regime: MarketRegime) -> int:
        """Track how long we've been in current regime"""
        if self._current_regime != current_regime:
            self._current_regime = current_regime
            self._regime_start_date = datetime.now()
            return 1
        elif self._regime_start_date:
            days_in_regime = (datetime.now() - self._regime_start_date).days
            return max(1, days_in_regime)
        else:
            return 1
    
    def _get_neutral_regime(self) -> MarketRegimeResult:
        """Return neutral regime on error"""
        return MarketRegimeResult(
            market_regime=MarketRegime.SIDEWAYS,
            volatility_regime=VolatilityRegime.NORMAL,
            risk_environment=RiskEnvironment.NEUTRAL,
            fundamental_health=FundamentalHealth.WARNING,
            confidence_score=0.3,
            regime_duration=1,
            signals={},
            timestamp=datetime.now()
        )
    
    def _calculate_atr(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range"""
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        
        return true_range.rolling(period).mean()
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))


def get_strategy_permissions(regime_result: MarketRegimeResult) -> Dict[str, Dict[str, float]]:
    """
    Get strategy permissions and allocations based on market regime
    
    Returns:
        Dict with strategy names and their allowed allocations
    """
    
    market_regime = regime_result.market_regime
    confidence = regime_result.confidence_score
    
    # Base allocations on regime
    if market_regime == MarketRegime.BULL and confidence > 0.6:
        return {
            "MegaMomentumStrategy": {"allocation": 0.40, "enabled": True},
            "SmartLiquidityStrategy": {"allocation": 0.35, "enabled": True}, 
            "short_strategies": {"allocation": 0.0, "enabled": False},
            "mean_reversion": {"allocation": 0.25, "enabled": True}
        }
    
    elif market_regime == MarketRegime.BEAR and confidence > 0.6:
        return {
            "short_strategies": {"allocation": 0.50, "enabled": True},
            "oversold_bounce": {"allocation": 0.30, "enabled": True},
            "MegaMomentumStrategy": {"allocation": 0.0, "enabled": False},
            "SmartLiquidityStrategy": {"allocation": 0.20, "enabled": True}
        }
    
    elif market_regime == MarketRegime.SIDEWAYS:
        return {
            "SmartLiquidityStrategy": {"allocation": 0.60, "enabled": True},
            "mean_reversion": {"allocation": 0.25, "enabled": True},
            "volatility_breakout": {"allocation": 0.15, "enabled": True},
            "MegaMomentumStrategy": {"allocation": 0.0, "enabled": False}
        }
    
    else:  # TRANSITIONAL or low confidence
        return {
            "SmartLiquidityStrategy": {"allocation": 0.40, "enabled": True},
            "defensive": {"allocation": 0.60, "enabled": True},
            "MegaMomentumStrategy": {"allocation": 0.0, "enabled": False},
            "short_strategies": {"allocation": 0.0, "enabled": False}
        }