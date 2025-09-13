"""
Crypto Market Regime Analyzer
Analyzes market from higher timeframes (1W, 1M, 3M) to determine overall market conditions.
This is the master system that determines which strategies can operate.
"""

import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import requests
from enum import Enum
import talib.abstract as ta

logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    BULL_CONFIRMED = "BULL_CONFIRMED"
    BULL_WEAKENING = "BULL_WEAKENING" 
    BEAR_CONFIRMED = "BEAR_CONFIRMED"
    BEAR_WEAKENING = "BEAR_WEAKENING"
    SIDEWAYS_CONSOLIDATION = "SIDEWAYS_CONSOLIDATION"
    TRANSITIONAL_UNCERTAINTY = "TRANSITIONAL_UNCERTAINTY"

class VolatilityRegime(Enum):
    LOW_VOLATILITY = "LOW_VOLATILITY"
    NORMAL_VOLATILITY = "NORMAL_VOLATILITY"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    EXPLOSIVE_VOLATILITY = "EXPLOSIVE_VOLATILITY"

class RiskEnvironment(Enum):
    RISK_ON = "RISK_ON"
    RISK_OFF = "RISK_OFF" 
    NEUTRAL = "NEUTRAL"
    MIXED_SIGNALS = "MIXED_SIGNALS"

class FundamentalHealth(Enum):
    HEALTHY = "HEALTHY"
    WARNING_SIGNS = "WARNING_SIGNS"
    DETERIORATING = "DETERIORATING"
    CRITICAL = "CRITICAL"

class CryptoMarketRegimeAnalyzer:
    """
    Master Market Regime Analyzer for Crypto Markets
    Determines overall market conditions from higher timeframes
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.data_cache = {}
        self.last_analysis_time = None
        self.current_regime_state = {
            'market_regime': MarketRegime.TRANSITIONAL_UNCERTAINTY,
            'volatility_regime': VolatilityRegime.NORMAL_VOLATILITY,
            'risk_environment': RiskEnvironment.NEUTRAL,
            'fundamental_health': FundamentalHealth.WARNING_SIGNS,
            'confidence_score': 0.5,
            'key_levels': {},
            'strategy_permissions': {}
        }
        
    def get_price_data(self, symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
        """
        Get OHLCV data from Binance API
        """
        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'count', 'taker_buy_volume',
                'taker_buy_quote_volume', 'ignore'
            ])
            
            # Convert to proper types
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
                
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df[numeric_columns]
            
        except Exception as e:
            logger.error(f"Error fetching price data for {symbol}: {e}")
            return pd.DataFrame()
    
    def analyze_weekly_monthly_trends(self, btc_data: pd.DataFrame) -> Dict:
        """
        Analyze long-term trends from weekly/monthly data
        """
        if btc_data.empty or len(btc_data) < 50:
            return {'trend': 'INSUFFICIENT_DATA', 'strength': 0.0}
            
        # Calculate trend indicators for multiple timeframes
        trends = {}
        
        # Weekly trend analysis
        weekly_ema_20 = ta.EMA(btc_data, timeperiod=20)
        weekly_ema_50 = ta.EMA(btc_data, timeperiod=50)
        weekly_ema_200 = ta.EMA(btc_data, timeperiod=200)
        
        current_price = btc_data['close'].iloc[-1]
        weekly_trend_score = 0
        
        # EMA alignment scoring
        if current_price > weekly_ema_20.iloc[-1]:
            weekly_trend_score += 1
        if current_price > weekly_ema_50.iloc[-1]:
            weekly_trend_score += 1
        if current_price > weekly_ema_200.iloc[-1]:
            weekly_trend_score += 1
        if weekly_ema_20.iloc[-1] > weekly_ema_50.iloc[-1]:
            weekly_trend_score += 1
        if weekly_ema_50.iloc[-1] > weekly_ema_200.iloc[-1]:
            weekly_trend_score += 1
            
        # Volume trend analysis
        volume_ma_20 = btc_data['volume'].rolling(20).mean()
        recent_volume = btc_data['volume'].tail(5).mean()
        volume_trend = recent_volume / volume_ma_20.iloc[-1] if volume_ma_20.iloc[-1] > 0 else 1.0
        
        # Price momentum analysis
        price_change_4w = (current_price / btc_data['close'].iloc[-20] - 1) if len(btc_data) >= 20 else 0
        price_change_12w = (current_price / btc_data['close'].iloc[-60] - 1) if len(btc_data) >= 60 else 0
        
        trends['weekly'] = {
            'ema_alignment_score': weekly_trend_score / 5.0,
            'volume_trend': volume_trend,
            'price_momentum_4w': price_change_4w,
            'price_momentum_12w': price_change_12w,
            'key_resistance': btc_data['high'].tail(20).max(),
            'key_support': btc_data['low'].tail(20).min()
        }
        
        return trends
    
    def detect_market_regime(self, btc_data: pd.DataFrame, trends: Dict) -> MarketRegime:
        """
        Determine current market regime based on multiple factors
        """
        if btc_data.empty or not trends:
            return MarketRegime.TRANSITIONAL_UNCERTAINTY
            
        weekly_data = trends.get('weekly', {})
        
        # Scoring system for regime detection
        bull_score = 0
        bear_score = 0
        sideways_score = 0
        
        # EMA alignment factor
        ema_score = weekly_data.get('ema_alignment_score', 0.5)
        if ema_score > 0.7:
            bull_score += 2
        elif ema_score < 0.3:
            bear_score += 2
        else:
            sideways_score += 1
            
        # Momentum factor
        momentum_4w = weekly_data.get('price_momentum_4w', 0)
        momentum_12w = weekly_data.get('price_momentum_12w', 0)
        
        if momentum_4w > 0.1 and momentum_12w > 0.15:  # Strong uptrend
            bull_score += 3
        elif momentum_4w < -0.1 and momentum_12w < -0.15:  # Strong downtrend
            bear_score += 3
        elif abs(momentum_4w) < 0.05 and abs(momentum_12w) < 0.1:  # Sideways
            sideways_score += 2
        else:
            sideways_score += 1  # Mixed signals
            
        # Volume confirmation
        volume_trend = weekly_data.get('volume_trend', 1.0)
        if volume_trend > 1.2:  # Increasing volume
            if momentum_4w > 0:
                bull_score += 1
            else:
                bear_score += 1
        elif volume_trend < 0.8:  # Decreasing volume
            sideways_score += 1
            
        # Determine regime
        max_score = max(bull_score, bear_score, sideways_score)
        
        if bull_score == max_score and bull_score >= 4:
            if momentum_4w > 0.05:
                return MarketRegime.BULL_CONFIRMED
            else:
                return MarketRegime.BULL_WEAKENING
        elif bear_score == max_score and bear_score >= 4:
            if momentum_4w < -0.05:
                return MarketRegime.BEAR_CONFIRMED
            else:
                return MarketRegime.BEAR_WEAKENING
        elif sideways_score == max_score and sideways_score >= 3:
            return MarketRegime.SIDEWAYS_CONSOLIDATION
        else:
            return MarketRegime.TRANSITIONAL_UNCERTAINTY
    
    def analyze_volatility_regime(self, btc_data: pd.DataFrame) -> VolatilityRegime:
        """
        Determine current volatility regime
        """
        if btc_data.empty or len(btc_data) < 30:
            return VolatilityRegime.NORMAL_VOLATILITY
            
        try:
            # Calculate ATR (Average True Range)
            atr_14 = ta.ATR(btc_data, timeperiod=14)
            if atr_14.empty or pd.isna(atr_14.iloc[-1]):
                return VolatilityRegime.NORMAL_VOLATILITY
                
            
            # Calculate volatility percentile
            atr_percentile = (atr_14.tail(100).rank().iloc[-1] / 100) if len(atr_14) >= 100 else 0.5
            
            # Bollinger Band squeeze detection
            bb_upper, bb_middle, bb_lower = ta.BBANDS(btc_data, timeperiod=20)
            if bb_middle.empty or pd.isna(bb_middle.iloc[-1]):
                return VolatilityRegime.NORMAL_VOLATILITY
                
            bb_width = ((bb_upper - bb_lower) / bb_middle).iloc[-1]
            bb_width_ma = ((bb_upper - bb_lower) / bb_middle).rolling(50).mean().iloc[-1] if len(bb_middle) >= 50 else bb_width
            
            squeeze_ratio = bb_width / bb_width_ma if bb_width_ma > 0 else 1.0
            
            # Determine volatility regime
            if atr_percentile > 0.8 or squeeze_ratio > 1.5:
                return VolatilityRegime.HIGH_VOLATILITY
            elif atr_percentile > 0.95 or squeeze_ratio > 2.0:
                return VolatilityRegime.EXPLOSIVE_VOLATILITY
            elif atr_percentile < 0.3 or squeeze_ratio < 0.7:
                return VolatilityRegime.LOW_VOLATILITY
            else:
                return VolatilityRegime.NORMAL_VOLATILITY
                
        except Exception as e:
            logger.warning(f"Error in volatility analysis: {e}")
            return VolatilityRegime.NORMAL_VOLATILITY
    
    def analyze_risk_environment(self, btc_data: pd.DataFrame) -> RiskEnvironment:
        """
        Determine risk-on vs risk-off environment
        This would ideally include correlation with traditional markets
        """
        if btc_data.empty:
            return RiskEnvironment.NEUTRAL
            
        # For now, use momentum and volatility as proxy
        # In production, would include SPY correlation, DXY, VIX, etc.
        
        price_change_1w = (btc_data['close'].iloc[-1] / btc_data['close'].iloc[-7] - 1) if len(btc_data) >= 7 else 0
        
        # Volume momentum
        volume_recent = btc_data['volume'].tail(7).mean()
        volume_baseline = btc_data['volume'].tail(30).mean()
        volume_momentum = volume_recent / volume_baseline if volume_baseline > 0 else 1.0
        
        # Risk scoring
        risk_on_score = 0
        risk_off_score = 0
        
        if price_change_1w > 0.05 and volume_momentum > 1.1:
            risk_on_score += 2
        elif price_change_1w < -0.05 and volume_momentum > 1.1:
            risk_off_score += 2
        elif abs(price_change_1w) < 0.02:
            # Neutral scoring
            pass
        
        if risk_on_score > risk_off_score:
            return RiskEnvironment.RISK_ON
        elif risk_off_score > risk_on_score:
            return RiskEnvironment.RISK_OFF
        else:
            return RiskEnvironment.NEUTRAL
    
    def analyze_fundamental_health(self) -> FundamentalHealth:
        """
        Analyze fundamental health of crypto market
        This is a placeholder - would integrate real on-chain and macro data
        """
        # Placeholder implementation
        # In production would include:
        # - On-chain metrics (active addresses, network value, etc.)
        # - DeFi TVL trends
        # - Stablecoin supply changes
        # - Institutional flow metrics
        # - Regulatory environment score
        
        # For now, return based on simple heuristics
        return FundamentalHealth.WARNING_SIGNS
    
    def calculate_key_levels(self, btc_data: pd.DataFrame, trends: Dict) -> Dict:
        """
        Calculate key support/resistance levels for strategy reference
        """
        if btc_data.empty:
            return {}
            
        current_price = btc_data['close'].iloc[-1]
        
        # Weekly levels from trend analysis
        weekly_data = trends.get('weekly', {})
        weekly_resistance = weekly_data.get('key_resistance', current_price * 1.1)
        weekly_support = weekly_data.get('key_support', current_price * 0.9)
        
        # Fibonacci levels (simplified)
        high_52w = btc_data['high'].tail(260).max() if len(btc_data) >= 260 else btc_data['high'].max()
        low_52w = btc_data['low'].tail(260).min() if len(btc_data) >= 260 else btc_data['low'].min()
        
        fib_range = high_52w - low_52w
        fib_618 = low_52w + (fib_range * 0.618)
        fib_382 = low_52w + (fib_range * 0.382)
        
        return {
            'current_price': current_price,
            'weekly_support': weekly_support,
            'weekly_resistance': weekly_resistance,
            'fib_618_level': fib_618,
            'fib_382_level': fib_382,
            'yearly_high': high_52w,
            'yearly_low': low_52w,
            'regime_invalidation_level': weekly_support * 0.95  # 5% below weekly support
        }
    
    def generate_strategy_permissions(self, market_regime: MarketRegime, 
                                    volatility_regime: VolatilityRegime,
                                    risk_environment: RiskEnvironment,
                                    fundamental_health: FundamentalHealth) -> Dict:
        """
        Generate strategy permission matrix based on market analysis
        """
        permissions = {
            'momentum_strategies': False,
            'short_strategies': False,
            'mean_reversion_strategies': False,
            'breakout_strategies': False,
            'hedge_strategies': False,
            'position_size_multiplier': 1.0,
            'max_correlation_limit': 0.7,
            'max_daily_trades': 10,
            'strategy_allocations': {}
        }
        
        # Base permissions on market regime
        if market_regime in [MarketRegime.BULL_CONFIRMED, MarketRegime.BULL_WEAKENING]:
            permissions['momentum_strategies'] = True
            permissions['breakout_strategies'] = True
            permissions['hedge_strategies'] = True
            permissions['strategy_allocations'] = {
                'smart_money_long': 0.4,
                'momentum_breakout': 0.35,
                'btc_hedge_long': 0.25
            }
            
        elif market_regime in [MarketRegime.BEAR_CONFIRMED, MarketRegime.BEAR_WEAKENING]:
            permissions['short_strategies'] = True
            permissions['hedge_strategies'] = True
            permissions['mean_reversion_strategies'] = True  # For bounces
            permissions['strategy_allocations'] = {
                'short_reversal': 0.5,
                'oversold_bounce': 0.3,
                'safe_haven_rotation': 0.2
            }
            
        elif market_regime == MarketRegime.SIDEWAYS_CONSOLIDATION:
            permissions['mean_reversion_strategies'] = True
            permissions['breakout_strategies'] = True  # Breakout preparation
            permissions['strategy_allocations'] = {
                'mean_reversion': 0.6,
                'range_trading': 0.25,
                'volatility_breakout_prep': 0.15
            }
            
        else:  # TRANSITIONAL_UNCERTAINTY
            permissions['hedge_strategies'] = True
            permissions['position_size_multiplier'] = 0.5  # Reduce size during uncertainty
            permissions['max_daily_trades'] = 5
            permissions['strategy_allocations'] = {
                'conservative_hedge': 0.7,
                'minimal_momentum': 0.3
            }
        
        # Adjust for volatility regime
        if volatility_regime == VolatilityRegime.HIGH_VOLATILITY:
            permissions['position_size_multiplier'] *= 0.7
            permissions['max_correlation_limit'] = 0.5
        elif volatility_regime == VolatilityRegime.EXPLOSIVE_VOLATILITY:
            permissions['position_size_multiplier'] *= 0.5
            permissions['max_correlation_limit'] = 0.3
            permissions['max_daily_trades'] = 3
        elif volatility_regime == VolatilityRegime.LOW_VOLATILITY:
            permissions['position_size_multiplier'] *= 1.2
            
        # Adjust for risk environment
        if risk_environment == RiskEnvironment.RISK_OFF:
            permissions['position_size_multiplier'] *= 0.8
            permissions['momentum_strategies'] = False
        elif risk_environment == RiskEnvironment.RISK_ON:
            permissions['position_size_multiplier'] *= 1.1
            
        # Adjust for fundamental health
        if fundamental_health == FundamentalHealth.DETERIORATING:
            permissions['position_size_multiplier'] *= 0.6
        elif fundamental_health == FundamentalHealth.CRITICAL:
            permissions['position_size_multiplier'] *= 0.3
            permissions['max_daily_trades'] = 2
            
        return permissions
    
    def calculate_confidence_score(self, market_regime: MarketRegime,
                                 volatility_regime: VolatilityRegime,
                                 risk_environment: RiskEnvironment,
                                 btc_data: pd.DataFrame) -> float:
        """
        Calculate confidence score for current analysis (0.0 to 1.0)
        """
        confidence = 0.5  # Base confidence
        
        # Data quality factor
        if len(btc_data) >= 100:
            confidence += 0.1
        elif len(btc_data) < 50:
            confidence -= 0.2
            
        # Regime clarity factor
        if market_regime in [MarketRegime.BULL_CONFIRMED, MarketRegime.BEAR_CONFIRMED]:
            confidence += 0.2
        elif market_regime == MarketRegime.TRANSITIONAL_UNCERTAINTY:
            confidence -= 0.2
            
        # Volatility consistency factor
        if volatility_regime in [VolatilityRegime.NORMAL_VOLATILITY, VolatilityRegime.LOW_VOLATILITY]:
            confidence += 0.1
        elif volatility_regime == VolatilityRegime.EXPLOSIVE_VOLATILITY:
            confidence -= 0.1
            
        return max(0.0, min(1.0, confidence))
    
    def analyze_market_conditions(self) -> Dict:
        """
        Main analysis function - analyzes current market conditions
        """
        try:
            logger.info("Starting market regime analysis...")
            
            # Get BTC weekly data (primary market driver)
            btc_weekly = self.get_price_data('BTCUSDT', '1w', 200)
            btc_daily = self.get_price_data('BTCUSDT', '1d', 100)
            
            if btc_weekly.empty:
                logger.error("Could not fetch BTC data")
                return self.current_regime_state
                
            # Analyze trends from higher timeframes
            trends = self.analyze_weekly_monthly_trends(btc_weekly)
            
            # Determine market regime
            market_regime = self.detect_market_regime(btc_weekly, trends)
            
            # Analyze volatility regime (use daily for more granular analysis)
            volatility_regime = self.analyze_volatility_regime(btc_daily)
            
            # Determine risk environment
            risk_environment = self.analyze_risk_environment(btc_daily)
            
            # Analyze fundamental health
            fundamental_health = self.analyze_fundamental_health()
            
            # Calculate key levels
            key_levels = self.calculate_key_levels(btc_weekly, trends)
            
            # Generate strategy permissions
            strategy_permissions = self.generate_strategy_permissions(
                market_regime, volatility_regime, risk_environment, fundamental_health
            )
            
            # Calculate confidence score
            confidence_score = self.calculate_confidence_score(
                market_regime, volatility_regime, risk_environment, btc_weekly
            )
            
            # Update state
            self.current_regime_state = {
                'timestamp': datetime.now().isoformat(),
                'market_regime': market_regime.value,
                'volatility_regime': volatility_regime.value,
                'risk_environment': risk_environment.value,
                'fundamental_health': fundamental_health.value,
                'confidence_score': confidence_score,
                'key_levels': key_levels,
                'strategy_permissions': strategy_permissions,
                'analysis_data': {
                    'btc_price': float(key_levels.get('current_price', 0)),
                    'weekly_trends': trends.get('weekly', {}),
                    'data_quality': len(btc_weekly)
                }
            }
            
            self.last_analysis_time = datetime.now()
            
            logger.info(f"Market analysis complete: {market_regime.value} / {volatility_regime.value}")
            return self.current_regime_state
            
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            return self.current_regime_state
    
    def should_update_analysis(self, force_update: bool = False) -> bool:
        """
        Check if analysis should be updated
        """
        if force_update or not self.last_analysis_time:
            return True
            
        # Update every 4 hours for regime analysis
        time_since_update = datetime.now() - self.last_analysis_time
        return time_since_update > timedelta(hours=4)
    
    def get_current_regime_state(self, force_update: bool = False) -> Dict:
        """
        Get current market regime state
        """
        if self.should_update_analysis(force_update):
            return self.analyze_market_conditions()
        else:
            return self.current_regime_state
    
    def export_analysis_summary(self) -> str:
        """
        Export human-readable analysis summary
        """
        state = self.current_regime_state
        
        summary = f"""
=== CRYPTO MARKET REGIME ANALYSIS ===
Timestamp: {state.get('timestamp', 'Unknown')}
Confidence: {state.get('confidence_score', 0):.1%}

MARKET REGIME: {state.get('market_regime', 'Unknown')}
VOLATILITY: {state.get('volatility_regime', 'Unknown')}
RISK ENVIRONMENT: {state.get('risk_environment', 'Unknown')}
FUNDAMENTAL HEALTH: {state.get('fundamental_health', 'Unknown')}

KEY LEVELS:
- Current BTC Price: ${state.get('key_levels', {}).get('current_price', 0):,.0f}
- Weekly Support: ${state.get('key_levels', {}).get('weekly_support', 0):,.0f}
- Weekly Resistance: ${state.get('key_levels', {}).get('weekly_resistance', 0):,.0f}
- Regime Invalidation: ${state.get('key_levels', {}).get('regime_invalidation_level', 0):,.0f}

STRATEGY PERMISSIONS:
- Momentum Strategies: {'✅' if state.get('strategy_permissions', {}).get('momentum_strategies') else '❌'}
- Short Strategies: {'✅' if state.get('strategy_permissions', {}).get('short_strategies') else '❌'}
- Mean Reversion: {'✅' if state.get('strategy_permissions', {}).get('mean_reversion_strategies') else '❌'}
- Position Size Multiplier: {state.get('strategy_permissions', {}).get('position_size_multiplier', 1.0):.1f}x
- Max Daily Trades: {state.get('strategy_permissions', {}).get('max_daily_trades', 0)}

STRATEGY ALLOCATIONS:
"""
        
        allocations = state.get('strategy_permissions', {}).get('strategy_allocations', {})
        for strategy, allocation in allocations.items():
            summary += f"- {strategy.replace('_', ' ').title()}: {allocation:.1%}\n"
            
        return summary


if __name__ == "__main__":
    # Test the analyzer
    logging.basicConfig(level=logging.INFO)
    
    analyzer = CryptoMarketRegimeAnalyzer()
    result = analyzer.analyze_market_conditions()
    
    print(analyzer.export_analysis_summary())