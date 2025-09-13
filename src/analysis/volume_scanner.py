"""
Volume Scanner - Institutional Money Flow Detection
Identifies where smart money is accumulating/distributing across all trading pairs

Key Features:
- Volume Delta Analysis (Accumulation vs Distribution)  
- Institutional Volume Detection
- Cross-pair volume comparison
- Smart Money Flow tracking
- Real-time volume alerts
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

@dataclass
class VolumeAlert:
    """Volume alert data structure"""
    pair: str
    alert_type: str
    volume_ratio: float
    price_change: float
    volume_delta: float
    timestamp: datetime
    confidence: float

class MoneyFlowType(Enum):
    """Types of money flow patterns"""
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    NEUTRAL = "neutral"
    BREAKOUT = "breakout"
    MANIPULATION = "manipulation"

class VolumeScanner:
    """
    Scans for institutional volume patterns across trading pairs
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()
        self.logger = logging.getLogger(__name__)
        
        # Volume thresholds
        self.institutional_threshold = self.config.get('institutional_threshold', 3.0)
        self.spike_threshold = self.config.get('spike_threshold', 2.0)
        self.delta_threshold = self.config.get('delta_threshold', 1.5)
        
        # Analysis periods
        self.short_period = self.config.get('short_period', 20)
        self.medium_period = self.config.get('medium_period', 50)
        self.long_period = self.config.get('long_period', 100)
        
        # Alert storage
        self.alerts: List[VolumeAlert] = []
        self.flow_history: Dict[str, List[Dict]] = {}
        
    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            'institutional_threshold': 3.0,
            'spike_threshold': 2.0, 
            'delta_threshold': 1.5,
            'short_period': 20,
            'medium_period': 50,
            'long_period': 100,
            'min_price_change': 0.01,
            'max_alerts_per_pair': 10
        }
    
    def analyze_pair_volume(self, pair: str, dataframe: pd.DataFrame) -> Dict:
        """
        Comprehensive volume analysis for a single trading pair
        """
        if dataframe.empty or len(dataframe) < self.long_period:
            return self._empty_analysis(pair)
            
        try:
            # Calculate volume metrics
            volume_metrics = self._calculate_volume_metrics(dataframe)
            
            # Analyze money flow patterns
            money_flow = self._analyze_money_flow(dataframe, volume_metrics)
            
            # Detect institutional patterns
            institutional_patterns = self._detect_institutional_patterns(dataframe, volume_metrics)
            
            # Generate alerts
            alerts = self._generate_volume_alerts(pair, dataframe, volume_metrics, money_flow)
            
            # Calculate overall score
            overall_score = self._calculate_volume_score(volume_metrics, money_flow, institutional_patterns)
            
            return {
                'pair': pair,
                'timestamp': datetime.now(),
                'volume_metrics': volume_metrics,
                'money_flow': money_flow,
                'institutional_patterns': institutional_patterns,
                'alerts': alerts,
                'overall_score': overall_score,
                'recommendation': self._get_recommendation(overall_score, money_flow)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing volume for {pair}: {e}")
            return self._empty_analysis(pair)
    
    def _calculate_volume_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate comprehensive volume metrics"""
        
        # Basic volume statistics
        volume_ma_short = df['volume'].rolling(self.short_period).mean()
        volume_ma_medium = df['volume'].rolling(self.medium_period).mean()
        volume_ma_long = df['volume'].rolling(self.long_period).mean()
        
        current_volume = df['volume'].iloc[-1]
        volume_ratio_short = current_volume / volume_ma_short.iloc[-1] if volume_ma_short.iloc[-1] > 0 else 1
        volume_ratio_medium = current_volume / volume_ma_medium.iloc[-1] if volume_ma_medium.iloc[-1] > 0 else 1
        volume_ratio_long = current_volume / volume_ma_long.iloc[-1] if volume_ma_long.iloc[-1] > 0 else 1
        
        # Volume percentile (where current volume ranks)
        volume_percentile = (df['volume'].iloc[-1] > df['volume'].tail(100)).sum() / 100
        
        # Volume trend analysis
        recent_volume_trend = (volume_ma_short.iloc[-1] - volume_ma_short.iloc[-10]) / volume_ma_short.iloc[-10] if volume_ma_short.iloc[-10] > 0 else 0
        
        # Volume volatility
        volume_std = df['volume'].tail(50).std()
        volume_cv = volume_std / df['volume'].tail(50).mean() if df['volume'].tail(50).mean() > 0 else 0
        
        return {
            'current_volume': current_volume,
            'volume_ma_short': volume_ma_short.iloc[-1],
            'volume_ma_medium': volume_ma_medium.iloc[-1], 
            'volume_ma_long': volume_ma_long.iloc[-1],
            'volume_ratio_short': volume_ratio_short,
            'volume_ratio_medium': volume_ratio_medium,
            'volume_ratio_long': volume_ratio_long,
            'volume_percentile': volume_percentile,
            'volume_trend': recent_volume_trend,
            'volume_volatility': volume_cv,
            'is_institutional': volume_ratio_short > self.institutional_threshold,
            'is_spike': volume_ratio_short > self.spike_threshold
        }
    
    def _analyze_money_flow(self, df: pd.DataFrame, volume_metrics: Dict) -> Dict:
        """Analyze accumulation vs distribution patterns"""
        
        # Price-Volume relationship
        df_copy = df.copy()
        df_copy['price_change'] = df_copy['close'] - df_copy['open']
        df_copy['candle_range'] = df_copy['high'] - df_copy['low']
        
        # Volume-weighted price analysis
        df_copy['vwap'] = (df_copy['volume'] * (df_copy['high'] + df_copy['low'] + df_copy['close']) / 3).cumsum() / df_copy['volume'].cumsum()
        
        # Accumulation/Distribution Volume
        df_copy['accumulation_volume'] = np.where(
            (df_copy['price_change'] > 0) & (df_copy['close'] > df_copy['vwap']),
            df_copy['volume'], 0
        )
        df_copy['distribution_volume'] = np.where(
            (df_copy['price_change'] < 0) & (df_copy['close'] < df_copy['vwap']),
            df_copy['volume'], 0
        )
        
        # Rolling sums for trend analysis
        acc_sum_short = df_copy['accumulation_volume'].tail(self.short_period).sum()
        dist_sum_short = df_copy['distribution_volume'].tail(self.short_period).sum()
        acc_sum_medium = df_copy['accumulation_volume'].tail(self.medium_period).sum()
        dist_sum_medium = df_copy['distribution_volume'].tail(self.medium_period).sum()
        
        # Volume Delta
        volume_delta_short = acc_sum_short - dist_sum_short
        volume_delta_medium = acc_sum_medium - dist_sum_medium
        
        # Money flow classification
        total_volume_short = acc_sum_short + dist_sum_short
        if total_volume_short > 0:
            acc_percentage = acc_sum_short / total_volume_short
            if acc_percentage > 0.65:
                flow_type = MoneyFlowType.ACCUMULATION
            elif acc_percentage < 0.35:
                flow_type = MoneyFlowType.DISTRIBUTION
            else:
                flow_type = MoneyFlowType.NEUTRAL
        else:
            flow_type = MoneyFlowType.NEUTRAL
            
        # Institutional buying/selling pressure
        institutional_buying = (
            volume_metrics['is_institutional'] and
            flow_type == MoneyFlowType.ACCUMULATION and
            df_copy['close'].iloc[-1] > df_copy['vwap'].iloc[-1]
        )
        
        institutional_selling = (
            volume_metrics['is_institutional'] and
            flow_type == MoneyFlowType.DISTRIBUTION and
            df_copy['close'].iloc[-1] < df_copy['vwap'].iloc[-1]
        )
        
        return {
            'flow_type': flow_type,
            'accumulation_volume': acc_sum_short,
            'distribution_volume': dist_sum_short,
            'volume_delta_short': volume_delta_short,
            'volume_delta_medium': volume_delta_medium,
            'accumulation_percentage': acc_percentage if total_volume_short > 0 else 0.5,
            'institutional_buying': institutional_buying,
            'institutional_selling': institutional_selling,
            'vwap_position': 'above' if df_copy['close'].iloc[-1] > df_copy['vwap'].iloc[-1] else 'below',
            'flow_strength': abs(volume_delta_short) / (total_volume_short if total_volume_short > 0 else 1)
        }
    
    def _detect_institutional_patterns(self, df: pd.DataFrame, volume_metrics: Dict) -> Dict:
        """Detect specific institutional trading patterns"""
        
        patterns = {
            'dark_pool_prints': False,
            'iceberg_orders': False,
            'sweep_patterns': False,
            'accumulation_phase': False,
            'distribution_phase': False
        }
        
        # Dark pool prints (unusually large volume spikes)
        if (volume_metrics['volume_ratio_short'] > 5.0 and 
            volume_metrics['volume_percentile'] > 0.95):
            patterns['dark_pool_prints'] = True
            
        # Iceberg orders (sustained volume without major price moves)
        recent_price_change = abs(df['close'].iloc[-1] - df['close'].iloc[-20]) / df['close'].iloc[-20]
        if (volume_metrics['volume_ratio_short'] > 2.0 and 
            recent_price_change < 0.02):
            patterns['iceberg_orders'] = True
            
        # Liquidity sweep patterns
        recent_high = df['high'].tail(20).max()
        current_price = df['close'].iloc[-1]
        
        if (df['high'].iloc[-1] > recent_high and 
            current_price < df['high'].iloc[-1] * 0.99 and
            volume_metrics['is_institutional']):
            patterns['sweep_patterns'] = True
            
        # Accumulation phase detection
        if (volume_metrics['volume_trend'] > 0.1 and
            df['close'].iloc[-1] > df['close'].iloc[-50] and
            volume_metrics['volume_ratio_medium'] > 1.5):
            patterns['accumulation_phase'] = True
            
        # Distribution phase detection  
        if (volume_metrics['volume_ratio_short'] > 3.0 and
            df['close'].iloc[-1] < df['close'].iloc[-10] and
            volume_metrics['volume_percentile'] > 0.8):
            patterns['distribution_phase'] = True
            
        return patterns
    
    def _generate_volume_alerts(self, pair: str, df: pd.DataFrame, 
                              volume_metrics: Dict, money_flow: Dict) -> List[VolumeAlert]:
        """Generate volume-based trading alerts"""
        
        alerts = []
        current_price = df['close'].iloc[-1]
        price_change = (current_price - df['open'].iloc[-1]) / df['open'].iloc[-1]
        
        # Institutional volume alert
        if volume_metrics['is_institutional']:
            confidence = min(volume_metrics['volume_ratio_short'] / 5.0, 1.0)
            alerts.append(VolumeAlert(
                pair=pair,
                alert_type='INSTITUTIONAL_VOLUME',
                volume_ratio=volume_metrics['volume_ratio_short'],
                price_change=price_change,
                volume_delta=money_flow['volume_delta_short'],
                timestamp=datetime.now(),
                confidence=confidence
            ))
        
        # Smart money accumulation alert
        if (money_flow['institutional_buying'] and 
            money_flow['flow_strength'] > 0.3):
            alerts.append(VolumeAlert(
                pair=pair,
                alert_type='SMART_MONEY_ACCUMULATION',
                volume_ratio=volume_metrics['volume_ratio_short'],
                price_change=price_change,
                volume_delta=money_flow['volume_delta_short'],
                timestamp=datetime.now(),
                confidence=money_flow['flow_strength']
            ))
        
        # Distribution alert
        if (money_flow['institutional_selling'] and
            volume_metrics['volume_percentile'] > 0.8):
            alerts.append(VolumeAlert(
                pair=pair,
                alert_type='INSTITUTIONAL_DISTRIBUTION', 
                volume_ratio=volume_metrics['volume_ratio_short'],
                price_change=price_change,
                volume_delta=money_flow['volume_delta_short'],
                timestamp=datetime.now(),
                confidence=volume_metrics['volume_percentile']
            ))
            
        # Volume breakout alert
        if (volume_metrics['volume_ratio_short'] > 4.0 and
            abs(price_change) > 0.03):
            alerts.append(VolumeAlert(
                pair=pair,
                alert_type='VOLUME_BREAKOUT',
                volume_ratio=volume_metrics['volume_ratio_short'],
                price_change=price_change,
                volume_delta=money_flow['volume_delta_short'],
                timestamp=datetime.now(),
                confidence=min(volume_metrics['volume_ratio_short'] / 6.0, 1.0)
            ))
        
        return alerts
    
    def _calculate_volume_score(self, volume_metrics: Dict, money_flow: Dict, patterns: Dict) -> float:
        """Calculate overall volume attractiveness score (0-100)"""
        
        score = 0.0
        
        # Volume strength (30 points max)
        score += min(volume_metrics['volume_ratio_short'] * 6, 30)
        
        # Money flow direction (25 points max)
        if money_flow['flow_type'] == MoneyFlowType.ACCUMULATION:
            score += 25 * money_flow['accumulation_percentage']
        elif money_flow['flow_type'] == MoneyFlowType.DISTRIBUTION:
            score += 10  # Some value for distribution but less than accumulation
            
        # Institutional patterns (25 points max)
        pattern_score = sum(patterns.values()) * 5  # 5 points per pattern
        score += min(pattern_score, 25)
        
        # Volume trend (20 points max)
        if volume_metrics['volume_trend'] > 0:
            score += min(volume_metrics['volume_trend'] * 100, 20)
            
        return min(score, 100.0)
    
    def _get_recommendation(self, score: float, money_flow: Dict) -> str:
        """Get trading recommendation based on volume analysis"""
        
        if score >= 80:
            return "STRONG_BUY" if money_flow['institutional_buying'] else "STRONG_WATCH"
        elif score >= 60:
            return "BUY" if money_flow['flow_type'] == MoneyFlowType.ACCUMULATION else "WATCH"
        elif score >= 40:
            return "NEUTRAL"
        elif score >= 20:
            return "WEAK" 
        else:
            return "AVOID"
    
    def _empty_analysis(self, pair: str) -> Dict:
        """Return empty analysis for pairs with insufficient data"""
        return {
            'pair': pair,
            'timestamp': datetime.now(),
            'volume_metrics': {},
            'money_flow': {'flow_type': MoneyFlowType.NEUTRAL},
            'institutional_patterns': {},
            'alerts': [],
            'overall_score': 0.0,
            'recommendation': 'INSUFFICIENT_DATA'
        }
    
    def scan_multiple_pairs(self, pairs_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """
        Scan multiple trading pairs and rank by volume attractiveness
        """
        results = {}
        
        for pair, dataframe in pairs_data.items():
            results[pair] = self.analyze_pair_volume(pair, dataframe)
            
        # Rank by volume score
        ranked_pairs = sorted(
            results.items(), 
            key=lambda x: x[1]['overall_score'], 
            reverse=True
        )
        
        return {
            'individual_analysis': results,
            'ranked_pairs': ranked_pairs[:10],  # Top 10
            'total_alerts': sum(len(analysis['alerts']) for analysis in results.values()),
            'institutional_activity': [
                pair for pair, analysis in results.items() 
                if analysis['money_flow'].get('institutional_buying') or 
                   analysis['money_flow'].get('institutional_selling')
            ]
        }
    
    def get_top_volume_pairs(self, results: Dict, limit: int = 5) -> List[Tuple[str, float]]:
        """Get top pairs by volume score"""
        ranked = results.get('ranked_pairs', [])
        return [(pair, analysis['overall_score']) for pair, analysis in ranked[:limit]]
    
    def get_accumulation_opportunities(self, results: Dict) -> List[str]:
        """Get pairs showing strong accumulation patterns"""
        opportunities = []
        
        for pair, analysis in results.get('individual_analysis', {}).items():
            if (analysis['money_flow'].get('flow_type') == MoneyFlowType.ACCUMULATION and
                analysis['overall_score'] > 60 and
                analysis['money_flow'].get('institutional_buying', False)):
                opportunities.append(pair)
                
        return opportunities