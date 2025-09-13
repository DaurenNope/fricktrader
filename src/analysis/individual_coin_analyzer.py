"""
Individual Coin Market Regime Analyzer

Unlike the BTC-only approach, this analyzer evaluates each coin's unique market conditions:
- ATH/ATL distance analysis
- Individual coin market phases
- Sector-specific patterns
- Independent regime classification

Key insight: A coin at -90% from ATH might be in accumulation zone 
while BTC is in a bull market - they need different strategies.
"""

import pandas as pd
from typing import Dict, List
import logging
from dataclasses import dataclass
from enum import Enum

class CoinRegime(Enum):
    """Individual coin market regimes"""
    BULL_STRONG = "bull_strong"          # Near ATH, strong uptrend
    BULL_MODERATE = "bull_moderate"      # Moderate uptrend
    ACCUMULATION = "accumulation"        # Deep discount, potential bottom
    DISTRIBUTION = "distribution"        # High levels, potential top
    BEAR_WEAK = "bear_weak"             # Mild downtrend
    BEAR_STRONG = "bear_strong"         # Strong downtrend
    SIDEWAYS = "sideways"               # Range-bound
    RECOVERY = "recovery"               # Bouncing from lows
    BREAKDOWN = "breakdown"             # Breaking key support

class TrendStrength(Enum):
    """Trend strength classification"""
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    VERY_WEAK = "very_weak"

@dataclass
class CoinAnalysis:
    """Individual coin analysis result"""
    pair: str
    regime: CoinRegime
    trend_strength: TrendStrength
    distance_from_ath: float
    distance_from_atl: float
    price_percentile: float  # noqa: F821  # noqa: F821
    trade_permission: bool
    position_multiplier: float
    confidence: float
    key_levels: Dict
    risk_factors: List[str]
    opportunities: List[str]

class IndividualCoinAnalyzer:
    """
    Analyzes each coin individually instead of using BTC as proxy
    """
    
    def __init__(self, lookback_periods: Dict = None):
        self.lookback_periods = lookback_periods or {
            'short': 20,
            'medium': 50,
            'long': 100,
            'ath_atl': 365  # 1 year for ATH/ATL analysis
        }
        self.logger = logging.getLogger(__name__)
        
    def analyze_coin(self, pair: str, dataframe: pd.DataFrame) -> CoinAnalysis:
        """
        Comprehensive analysis of individual coin market regime
        """
        if dataframe.empty or len(dataframe) < self.lookback_periods['long']:
            return self._insufficient_data_analysis(pair)
            
        try:
            # Price level analysis
            price_levels = self._analyze_price_levels(dataframe)
            
            # Trend analysis
            trend_analysis = self._analyze_trends(dataframe)
            
            # Market structure analysis
            structure_analysis = self._analyze_market_structure(dataframe)
            
            # Volume context
            volume_analysis = self._analyze_volume_context(dataframe)
            
            # Regime classification
            regime = self._classify_regime(price_levels, trend_analysis, structure_analysis, volume_analysis)
            
            # Trading permissions and position sizing
            trading_info = self._get_trading_permissions(regime, price_levels, trend_analysis)
            
            # Risk and opportunity assessment
            risk_factors = self._assess_risks(price_levels, trend_analysis, structure_analysis)
            opportunities = self._identify_opportunities(regime, price_levels, trend_analysis)
            
            return CoinAnalysis(
                pair=pair,
                regime=regime,
                trend_strength=trend_analysis['strength'],
                distance_from_ath=price_levels['distance_from_ath'],
                distance_from_atl=price_levels['distance_from_atl'], 
                price_percentile=price_levels['price_percentile'],
                trade_permission=trading_info['permission'],
                position_multiplier=trading_info['position_multiplier'],
                confidence=self._calculate_confidence(price_levels, trend_analysis, structure_analysis),
                key_levels=price_levels['key_levels'],
                risk_factors=risk_factors,
                opportunities=opportunities
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing {pair}: {e}")
            return self._insufficient_data_analysis(pair)
    
    def _analyze_price_levels(self, df: pd.DataFrame) -> Dict:
        """Analyze price positioning relative to historical levels"""
        
        # Current and historical prices
        current_price = df['close'].iloc[-1]
        
        # ATH/ATL analysis (last year)
        analysis_period = min(len(df), self.lookback_periods['ath_atl'])
        price_series = df['close'].tail(analysis_period)
        
        all_time_high = price_series.max()
        all_time_low = price_series.min()
        
        # Distance calculations
        distance_from_ath = (current_price - all_time_high) / all_time_high * 100
        distance_from_atl = (current_price - all_time_low) / all_time_low * 100
        
        # Price percentile (where current price ranks historically)\n        price_percentile = (current_price > price_series).sum() / len(price_series)
        
        # Key support/resistance levels
        key_levels = self._identify_key_levels(df, current_price)
        
        # Recent range analysis
        recent_high = df['high'].tail(50).max()
        recent_low = df['low'].tail(50).min()
        range_position = (current_price - recent_low) / (recent_high - recent_low) if recent_high != recent_low else 0.5
        
        return {
            'current_price': current_price,
            'all_time_high': all_time_high,
            'all_time_low': all_time_low,
            'distance_from_ath': distance_from_ath,
            'distance_from_atl': distance_from_atl,
            'price_percentile': price_percentile,
            'recent_high': recent_high,
            'recent_low': recent_low,
            'range_position': range_position,
            'key_levels': key_levels
        }
    
    def _analyze_trends(self, df: pd.DataFrame) -> Dict:
        """Analyze trend direction and strength"""
        
        # Multiple timeframe EMAs
        ema_9 = df['close'].ewm(span=9).mean()
        ema_21 = df['close'].ewm(span=21).mean()
        ema_50 = df['close'].ewm(span=50).mean()
        ema_100 = df['close'].ewm(span=100).mean()
        
        current_price = df['close'].iloc[-1]
        
        # Trend direction
        short_term_bullish = current_price > ema_9.iloc[-1] > ema_21.iloc[-1]
        medium_term_bullish = ema_21.iloc[-1] > ema_50.iloc[-1]
        long_term_bullish = ema_50.iloc[-1] > ema_100.iloc[-1]
        
        # Trend strength calculation
        price_above_emas = sum([
            current_price > ema_9.iloc[-1],
            current_price > ema_21.iloc[-1],
            current_price > ema_50.iloc[-1],
            current_price > ema_100.iloc[-1]
        ])
        
        ema_alignment = sum([
            ema_9.iloc[-1] > ema_21.iloc[-1],
            ema_21.iloc[-1] > ema_50.iloc[-1],
            ema_50.iloc[-1] > ema_100.iloc[-1]
        ])
        
        # Trend strength classification
        total_strength = price_above_emas + ema_alignment
        if total_strength >= 6:
            strength = TrendStrength.VERY_STRONG
        elif total_strength >= 5:
            strength = TrendStrength.STRONG
        elif total_strength >= 3:
            strength = TrendStrength.MODERATE
        elif total_strength >= 1:
            strength = TrendStrength.WEAK
        else:
            strength = TrendStrength.VERY_WEAK
        
        # Trend momentum
        price_momentum = (current_price - df['close'].iloc[-20]) / df['close'].iloc[-20] * 100
        ema_momentum = (ema_21.iloc[-1] - ema_21.iloc[-20]) / ema_21.iloc[-20] * 100
        
        return {
            'short_term_bullish': short_term_bullish,
            'medium_term_bullish': medium_term_bullish,
            'long_term_bullish': long_term_bullish,
            'strength': strength,
            'price_momentum': price_momentum,
            'ema_momentum': ema_momentum,
            'price_above_emas': price_above_emas,
            'ema_alignment': ema_alignment
        }
    
    def _analyze_market_structure(self, df: pd.DataFrame) -> Dict:
        """Analyze market structure patterns"""
        
        # Higher highs and higher lows (bullish structure)
        highs = df['high'].tail(50)
        lows = df['low'].tail(50)
        
        # Find swing points
        swing_highs = []
        swing_lows = []
        
        for i in range(2, len(highs) - 2):
            if highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i+1]:
                swing_highs.append((i, highs.iloc[i]))
            if lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i+1]:
                swing_lows.append((i, lows.iloc[i]))
        
        # Structure analysis
        bullish_structure = False
        bearish_structure = False
        
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            # Check for higher highs and higher lows
            recent_highs = sorted(swing_highs, key=lambda x: x[0])[-2:]
            recent_lows = sorted(swing_lows, key=lambda x: x[0])[-2:]
            
            if (recent_highs[1][1] > recent_highs[0][1] and 
                recent_lows[1][1] > recent_lows[0][1]):
                bullish_structure = True
            elif (recent_highs[1][1] < recent_highs[0][1] and 
                  recent_lows[1][1] < recent_lows[0][1]):
                bearish_structure = True
        
        # Support and resistance strength
        support_level = lows.tail(20).min()
        resistance_level = highs.tail(20).max()
        
        # Test counts (how many times price touched these levels)
        support_tests = (df['low'].tail(100) <= support_level * 1.01).sum()
        resistance_tests = (df['high'].tail(100) >= resistance_level * 0.99).sum()
        
        return {
            'bullish_structure': bullish_structure,
            'bearish_structure': bearish_structure,
            'swing_highs': len(swing_highs),
            'swing_lows': len(swing_lows),
            'support_level': support_level,
            'resistance_level': resistance_level,
            'support_tests': support_tests,
            'resistance_tests': resistance_tests
        }
    
    def _analyze_volume_context(self, df: pd.DataFrame) -> Dict:
        """Analyze volume patterns for regime context"""
        
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].tail(50).mean()
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # Volume trend
        recent_vol_trend = df['volume'].tail(20).mean() / df['volume'].tail(50).mean() if df['volume'].tail(50).mean() > 0 else 1
        
        # Price-volume relationship
        price_up_days = df['close'] > df['open']
        volume_on_up_days = df.loc[price_up_days, 'volume'].tail(20).mean()
        volume_on_down_days = df.loc[~price_up_days, 'volume'].tail(20).mean()
        
        volume_bias = 'bullish' if volume_on_up_days > volume_on_down_days else 'bearish'
        
        return {
            'volume_ratio': volume_ratio,
            'volume_trend': recent_vol_trend,
            'volume_bias': volume_bias,
            'avg_volume': avg_volume
        }
    
    def _identify_key_levels(self, df: pd.DataFrame, current_price: float) -> Dict:
        """Identify key support and resistance levels"""
        
        # Volume profile analysis (simplified)
        price_levels = {}
        
        # Recent significant levels
        recent_data = df.tail(100)
        
        # High volume areas
        volume_threshold = recent_data['volume'].quantile(0.8)
        high_volume_candles = recent_data[recent_data['volume'] > volume_threshold]
        
        if not high_volume_candles.empty:
            # Key support (high volume lows)
            support_candidates = high_volume_candles.nsmallest(3, 'low')['low'].tolist()
            price_levels['support'] = [level for level in support_candidates if level < current_price]
            
            # Key resistance (high volume highs)
            resistance_candidates = high_volume_candles.nlargest(3, 'high')['high'].tolist()
            price_levels['resistance'] = [level for level in resistance_candidates if level > current_price]
        else:
            price_levels['support'] = []
            price_levels['resistance'] = []
        
        # Psychological levels (round numbers)
        psychological_levels = []
        price_magnitude = 10 ** (len(str(int(current_price))) - 1)
        for multiplier in [1, 2, 5]:
            level = multiplier * price_magnitude
            if abs(level - current_price) / current_price < 0.1:  # Within 10%
                psychological_levels.append(level)
        
        price_levels['psychological'] = psychological_levels
        
        return price_levels
    
    def _classify_regime(self, price_levels: Dict, trend_analysis: Dict, 
                        structure_analysis: Dict, volume_analysis: Dict) -> CoinRegime:
        """Classify the coin's current market regime"""
        
        distance_from_ath = price_levels['distance_from_ath']
        price_percentile = price_levels['price_percentile']
        trend_strength = trend_analysis['strength']
        
        # Near all-time high (within 20%)
        if distance_from_ath > -20:
            if trend_strength in [TrendStrength.VERY_STRONG, TrendStrength.STRONG]:
                return CoinRegime.BULL_STRONG
            elif structure_analysis['bearish_structure'] and volume_analysis['volume_bias'] == 'bearish':
                return CoinRegime.DISTRIBUTION
            else:
                return CoinRegime.BULL_MODERATE
                
        # Deep discount (more than 70% from ATH)
        elif distance_from_ath < -70:
            if trend_analysis['short_term_bullish'] and volume_analysis['volume_trend'] > 1.2:
                return CoinRegime.RECOVERY
            elif price_percentile < 0.2:
                return CoinRegime.ACCUMULATION
            else:
                return CoinRegime.BEAR_STRONG
                
        # Moderate discount (20-70% from ATH)
        else:
            if trend_strength in [TrendStrength.VERY_STRONG, TrendStrength.STRONG]:
                if structure_analysis['bullish_structure']:
                    return CoinRegime.BULL_MODERATE
                else:
                    return CoinRegime.RECOVERY
            elif trend_strength in [TrendStrength.VERY_WEAK, TrendStrength.WEAK]:
                if structure_analysis['bearish_structure']:
                    return CoinRegime.BEAR_WEAK
                else:
                    return CoinRegime.BREAKDOWN
            else:
                return CoinRegime.SIDEWAYS
    
    def _get_trading_permissions(self, regime: CoinRegime, price_levels: Dict, 
                               trend_analysis: Dict) -> Dict:
        """Determine trading permissions and position sizing based on regime"""
        
        regime_settings = {
            CoinRegime.BULL_STRONG: {'permission': True, 'multiplier': 1.3},
            CoinRegime.BULL_MODERATE: {'permission': True, 'multiplier': 1.1},
            CoinRegime.ACCUMULATION: {'permission': True, 'multiplier': 1.2},  # Higher allocation for cheap coins
            CoinRegime.RECOVERY: {'permission': True, 'multiplier': 1.0},
            CoinRegime.DISTRIBUTION: {'permission': False, 'multiplier': 0.5},  # Reduced exposure
            CoinRegime.BEAR_WEAK: {'permission': True, 'multiplier': 0.7},
            CoinRegime.BEAR_STRONG: {'permission': False, 'multiplier': 0.3},
            CoinRegime.SIDEWAYS: {'permission': True, 'multiplier': 0.8},
            CoinRegime.BREAKDOWN: {'permission': False, 'multiplier': 0.4}
        }
        
        base_settings = regime_settings.get(regime, {'permission': True, 'multiplier': 1.0})
        
        # Adjust based on trend strength
        if trend_analysis['strength'] == TrendStrength.VERY_STRONG:
            base_settings['multiplier'] *= 1.2
        elif trend_analysis['strength'] == TrendStrength.VERY_WEAK:
            base_settings['multiplier'] *= 0.8
        
        return {
            'permission': base_settings['permission'],
            'position_multiplier': max(0.1, min(2.0, base_settings['multiplier']))  # Cap between 0.1x and 2.0x
        }
    
    def _assess_risks(self, price_levels: Dict, trend_analysis: Dict, 
                     structure_analysis: Dict) -> List[str]:
        """Assess risk factors for the current regime"""
        
        risks = []
        
        # Price level risks
        if price_levels['distance_from_ath'] > -10:
            risks.append("Near all-time high - distribution risk")
            
        if price_levels['range_position'] > 0.9:
            risks.append("Top of recent range - resistance overhead")
            
        # Trend risks
        if trend_analysis['strength'] == TrendStrength.VERY_WEAK:
            risks.append("Very weak trend - momentum exhaustion")
            
        if not trend_analysis['short_term_bullish'] and trend_analysis['medium_term_bullish']:
            risks.append("Short-term weakness in medium-term uptrend")
            
        # Structure risks
        if structure_analysis['bearish_structure']:
            risks.append("Bearish market structure - lower highs/lows")
            
        if structure_analysis['resistance_tests'] > 3:
            risks.append("Multiple resistance tests - overhead pressure")
        
        return risks
    
    def _identify_opportunities(self, regime: CoinRegime, price_levels: Dict, 
                              trend_analysis: Dict) -> List[str]:
        """Identify trading opportunities"""
        
        opportunities = []
        
        # Regime-based opportunities
        if regime == CoinRegime.ACCUMULATION:
            opportunities.append("Deep discount accumulation opportunity")
            
        if regime == CoinRegime.RECOVERY:
            opportunities.append("Early recovery from oversold levels")
            
        if regime in [CoinRegime.BULL_STRONG, CoinRegime.BULL_MODERATE]:
            opportunities.append("Momentum continuation opportunity")
        
        # Price level opportunities
        if price_levels['range_position'] < 0.3:
            opportunities.append("Bottom of range - potential bounce")
            
        if price_levels['distance_from_atl'] > 500:  # 5x from lows
            opportunities.append("Strong recovery from all-time lows")
        
        # Trend opportunities
        if (trend_analysis['strength'] == TrendStrength.STRONG and 
            trend_analysis['price_momentum'] > 10):
            opportunities.append("Strong momentum breakout")
            
        return opportunities
    
    def _calculate_confidence(self, price_levels: Dict, trend_analysis: Dict, 
                            structure_analysis: Dict) -> float:
        """Calculate confidence in the regime classification (0-1)"""
        
        confidence = 0.5  # Base confidence
        
        # Price level confidence
        if price_levels['distance_from_ath'] < -50 or price_levels['distance_from_ath'] > -20:
            confidence += 0.2  # Clear positioning
        
        # Trend confidence  
        if trend_analysis['strength'] in [TrendStrength.VERY_STRONG, TrendStrength.VERY_WEAK]:
            confidence += 0.2  # Clear trend
            
        # Structure confidence
        if structure_analysis['bullish_structure'] or structure_analysis['bearish_structure']:
            confidence += 0.1  # Clear structure
            
        return min(1.0, confidence)
    
    def _insufficient_data_analysis(self, pair: str) -> CoinAnalysis:
        """Return analysis for pairs with insufficient data"""
        return CoinAnalysis(
            pair=pair,
            regime=CoinRegime.SIDEWAYS,
            trend_strength=TrendStrength.MODERATE,
            distance_from_ath=-50.0,
            distance_from_atl=100.0,
            price_percentile=0.5,
            trade_permission=True,
            position_multiplier=1.0,
            confidence=0.1,
            key_levels={},
            risk_factors=["Insufficient data for analysis"],
            opportunities=[]
        )
    
    def analyze_multiple_coins(self, pairs_data: Dict[str, pd.DataFrame]) -> Dict[str, CoinAnalysis]:
        """Analyze multiple coins and return individual regime classifications"""
        
        results = {}
        
        for pair, dataframe in pairs_data.items():
            results[pair] = self.analyze_coin(pair, dataframe)
            
        return results
    
    def get_regime_summary(self, analyses: Dict[str, CoinAnalysis]) -> Dict:
        """Get summary of regime distribution across analyzed coins"""
        
        regime_counts = {}
        for analysis in analyses.values():
            regime = analysis.regime.value
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            
        total_coins = len(analyses)
        
        return {
            'regime_distribution': regime_counts,
            'total_coins_analyzed': total_coins,
            'high_confidence_analyses': [
                pair for pair, analysis in analyses.items() 
                if analysis.confidence > 0.8
            ],
            'trading_opportunities': [
                pair for pair, analysis in analyses.items()
                if analysis.trade_permission and len(analysis.opportunities) > 0
            ],
            'risk_warnings': [
                pair for pair, analysis in analyses.items()
                if len(analysis.risk_factors) > 2
            ]
        }