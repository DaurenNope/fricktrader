"""
Enhanced Strategy Integration with OpenBB Market Data
Integrates advanced market data (delta, volume profile, institutional flow) into trading strategies
"""

import logging
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime
import pandas as pd
import numpy as np

from .openbb_provider import OpenBBMarketDataProvider, DeltaAnalysis, VolumeProfile, MarketDepthData, InstitutionalData

logger = logging.getLogger(__name__)

class EnhancedMarketDataStrategy:
    """
    Enhanced strategy that integrates OpenBB market data with existing technical analysis
    Provides Tiger Trade-like advanced features for Freqtrade strategies
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.market_data_provider = OpenBBMarketDataProvider(config)
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
        logger.info("🚀 Enhanced Market Data Strategy initialized")
    
    async def get_enhanced_signals(self, pair: str, timeframe: str = '4h') -> Dict[str, Any]:
        """
        Get enhanced trading signals combining technical analysis with advanced market data
        
        Returns comprehensive signal analysis similar to Tiger Trade's signal system
        """
        try:
            logger.info(f"🔍 Generating enhanced signals for {pair}")
            
            # Get comprehensive market analysis
            market_analysis = await self.market_data_provider.get_comprehensive_analysis(pair)
            
            if 'error' in market_analysis:
                logger.error(f"Error getting market analysis: {market_analysis['error']}")
                return {'error': market_analysis['error']}
            
            # Extract components
            delta_analysis = market_analysis.get('delta_analysis')
            volume_profile = market_analysis.get('volume_profile')
            market_depth = market_analysis.get('market_depth')
            institutional_data = market_analysis.get('institutional_data')
            
            # Calculate enhanced signals
            signals = {
                'pair': pair,
                'timestamp': datetime.now().isoformat(),
                'technical_score': 0.0,
                'delta_score': 0.0,
                'volume_score': 0.0,
                'institutional_score': 0.0,
                'market_depth_score': 0.0,
                'composite_score': 0.0,
                'signal_strength': 'neutral',
                'entry_recommendation': 'hold',
                'risk_level': 'medium',
                'key_levels': {},
                'analysis_details': {}
            }
            
            # Calculate individual scores
            if delta_analysis:
                signals['delta_score'] = self._calculate_delta_score(delta_analysis)
                signals['analysis_details']['delta'] = self._analyze_delta_signals(delta_analysis)
            
            if volume_profile:
                signals['volume_score'] = self._calculate_volume_score(volume_profile)
                signals['analysis_details']['volume'] = self._analyze_volume_signals(volume_profile)
                signals['key_levels'].update(self._extract_volume_levels(volume_profile))
            
            if market_depth:
                signals['market_depth_score'] = self._calculate_depth_score(market_depth)
                signals['analysis_details']['depth'] = self._analyze_depth_signals(market_depth)
                signals['key_levels'].update(self._extract_depth_levels(market_depth))
            
            if institutional_data:
                signals['institutional_score'] = self._calculate_institutional_score(institutional_data)
                signals['analysis_details']['institutional'] = self._analyze_institutional_signals(institutional_data)
            
            # Calculate composite score
            signals['composite_score'] = self._calculate_composite_score(signals)
            
            # Determine signal strength and recommendation
            signals['signal_strength'] = self._determine_signal_strength(signals['composite_score'])
            signals['entry_recommendation'] = self._determine_entry_recommendation(signals)
            signals['risk_level'] = self._assess_risk_level(signals)
            
            logger.info(f"✅ Enhanced signals generated for {pair}: {signals['signal_strength']} ({signals['composite_score']:.3f})")
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating enhanced signals for {pair}: {e}")
            return {'error': str(e)}
    
    def _calculate_delta_score(self, delta_analysis: Dict) -> float:
        """Calculate delta-based signal score (-1.0 to 1.0)"""
        try:
            score = 0.0
            
            # Net delta contribution (40%)
            net_delta = delta_analysis.get('net_delta', 0)
            if net_delta > 0:
                score += 0.4 * min(net_delta / 1000000, 1.0)  # Normalize to reasonable range
            else:
                score += 0.4 * max(net_delta / 1000000, -1.0)
            
            # Order flow strength (30%)
            order_flow = delta_analysis.get('order_flow_strength', 0)
            score += 0.3 * np.clip(order_flow, -1.0, 1.0)
            
            # Delta divergence (20%)
            divergence = delta_analysis.get('delta_divergence', 0)
            score += 0.2 * np.clip(divergence, -1.0, 1.0)
            
            # Institutional vs retail flow (10%)
            institutional_flow = delta_analysis.get('institutional_flow', 0.5)
            if institutional_flow > 0.6:  # More institutional buying
                score += 0.1
            elif institutional_flow < 0.4:  # More retail buying (contrarian signal)
                score -= 0.1
            
            return np.clip(score, -1.0, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating delta score: {e}")
            return 0.0
    
    def _calculate_volume_score(self, volume_profile: Dict) -> float:
        """Calculate volume profile-based signal score (-1.0 to 1.0)"""
        try:
            score = 0.0
            
            # Volume imbalance (50%)
            volume_imbalance = volume_profile.get('volume_imbalance', 0)
            score += 0.5 * np.clip(volume_imbalance, -1.0, 1.0)
            
            # Buying vs selling volume (30%)
            buying_volume = volume_profile.get('buying_volume', 0)
            selling_volume = volume_profile.get('selling_volume', 0)
            total_volume = buying_volume + selling_volume
            
            if total_volume > 0:
                buy_sell_ratio = (buying_volume - selling_volume) / total_volume
                score += 0.3 * np.clip(buy_sell_ratio, -1.0, 1.0)
            
            # Volume concentration (20%) - high concentration at POC is bullish
            total_volume = volume_profile.get('total_volume', 0)
            volume_by_price = volume_profile.get('volume_by_price', {})
            
            if volume_by_price and total_volume > 0:
                max_volume = max(volume_by_price.values())
                concentration = max_volume / total_volume
                if concentration > 0.1:  # High concentration
                    score += 0.2
                elif concentration < 0.05:  # Low concentration (distribution)
                    score -= 0.1
            
            return np.clip(score, -1.0, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating volume score: {e}")
            return 0.0
    
    def _calculate_depth_score(self, market_depth: Dict) -> float:
        """Calculate market depth-based signal score (-1.0 to 1.0)"""
        try:
            score = 0.0
            
            # Order book imbalance (60%)
            imbalance_ratio = market_depth.get('imbalance_ratio', 0.5)
            # Convert 0.5 (neutral) to 0, >0.5 to positive, <0.5 to negative
            imbalance_score = (imbalance_ratio - 0.5) * 2
            score += 0.6 * np.clip(imbalance_score, -1.0, 1.0)
            
            # Spread analysis (25%)
            spread = market_depth.get('spread', 0)
            mid_price = market_depth.get('mid_price', 1)
            
            if mid_price > 0:
                spread_pct = spread / mid_price
                if spread_pct < 0.001:  # Tight spread - good liquidity
                    score += 0.25
                elif spread_pct > 0.01:  # Wide spread - poor liquidity
                    score -= 0.25
            
            # Total volume (15%)
            total_bid_volume = market_depth.get('total_bid_volume', 0)
            total_ask_volume = market_depth.get('total_ask_volume', 0)
            total_volume = total_bid_volume + total_ask_volume
            
            # Higher volume generally positive for execution
            if total_volume > 1000:  # Arbitrary threshold
                score += 0.15
            elif total_volume < 100:
                score -= 0.15
            
            return np.clip(score, -1.0, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating depth score: {e}")
            return 0.0
    
    def _calculate_institutional_score(self, institutional_data: Dict) -> float:
        """Calculate institutional activity-based signal score (-1.0 to 1.0)"""
        try:
            score = 0.0
            
            # Dark pool volume (40%)
            dark_pool_volume = institutional_data.get('dark_pool_volume', 0)
            if dark_pool_volume > 0:
                # High dark pool volume can indicate institutional accumulation
                score += 0.4 * min(dark_pool_volume / 10000000, 1.0)  # Normalize
            
            # Block trades (30%)
            block_trades = institutional_data.get('block_trades', [])
            if len(block_trades) > 5:  # Many block trades
                score += 0.3
            elif len(block_trades) > 2:
                score += 0.15
            
            # Short interest (20%)
            float_short = institutional_data.get('float_short', 0)
            days_to_cover = institutional_data.get('days_to_cover', 0)
            
            if float_short > 0.2:  # High short interest
                if days_to_cover > 5:  # High days to cover - potential squeeze
                    score += 0.2
                else:
                    score -= 0.1  # High short interest, easy to cover
            
            # Institutional ownership (10%)
            institutional_ownership = institutional_data.get('institutional_ownership', 0)
            if institutional_ownership > 0.7:  # High institutional ownership
                score += 0.1
            
            return np.clip(score, -1.0, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating institutional score: {e}")
            return 0.0
    
    def _calculate_composite_score(self, signals: Dict) -> float:
        """Calculate weighted composite score from all signal components"""
        try:
            # Weights for different signal types
            weights = {
                'delta_score': 0.30,        # 30% - Order flow is critical
                'volume_score': 0.25,       # 25% - Volume profile important
                'market_depth_score': 0.20, # 20% - Real-time liquidity
                'institutional_score': 0.15, # 15% - Institutional activity
                'technical_score': 0.10     # 10% - Traditional technical (if available)
            }
            
            composite_score = 0.0
            total_weight = 0.0
            
            for score_type, weight in weights.items():
                score_value = signals.get(score_type, 0.0)
                if score_value != 0.0:  # Only include non-zero scores
                    composite_score += score_value * weight
                    total_weight += weight
            
            # Normalize by actual weights used
            if total_weight > 0:
                composite_score = composite_score / total_weight
            
            return np.clip(composite_score, -1.0, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            return 0.0
    
    def _determine_signal_strength(self, composite_score: float) -> str:
        """Determine signal strength based on composite score"""
        if composite_score > 0.6:
            return 'strong_bullish'
        elif composite_score > 0.3:
            return 'bullish'
        elif composite_score > 0.1:
            return 'weak_bullish'
        elif composite_score < -0.6:
            return 'strong_bearish'
        elif composite_score < -0.3:
            return 'bearish'
        elif composite_score < -0.1:
            return 'weak_bearish'
        else:
            return 'neutral'
    
    def _determine_entry_recommendation(self, signals: Dict) -> str:
        """Determine entry recommendation based on all signals"""
        composite_score = signals.get('composite_score', 0.0)
        signal_strength = signals.get('signal_strength', 'neutral')
        
        # Conservative approach - require strong signals for entry
        if composite_score > 0.4 and signal_strength in ['strong_bullish', 'bullish']:
            return 'strong_buy'
        elif composite_score > 0.2 and signal_strength in ['bullish', 'weak_bullish']:
            return 'buy'
        elif composite_score < -0.4 and signal_strength in ['strong_bearish', 'bearish']:
            return 'strong_sell'
        elif composite_score < -0.2 and signal_strength in ['bearish', 'weak_bearish']:
            return 'sell'
        else:
            return 'hold'
    
    def _assess_risk_level(self, signals: Dict) -> str:
        """Assess risk level based on market conditions"""
        try:
            risk_factors = 0
            
            # Check various risk factors
            depth_score = signals.get('market_depth_score', 0.0)
            if depth_score < -0.3:  # Poor liquidity
                risk_factors += 1
            
            institutional_score = signals.get('institutional_score', 0.0)
            if institutional_score < -0.5:  # Heavy institutional selling
                risk_factors += 1
            
            volume_score = signals.get('volume_score', 0.0)
            if volume_score < -0.4:  # Heavy selling volume
                risk_factors += 1
            
            composite_score = abs(signals.get('composite_score', 0.0))
            if composite_score < 0.1:  # Very weak signals
                risk_factors += 1
            
            # Determine risk level
            if risk_factors >= 3:
                return 'high'
            elif risk_factors >= 2:
                return 'medium_high'
            elif risk_factors >= 1:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            logger.error(f"Error assessing risk level: {e}")
            return 'medium'
    
    def _analyze_delta_signals(self, delta_analysis: Dict) -> Dict[str, Any]:
        """Provide detailed delta analysis"""
        return {
            'cumulative_delta': delta_analysis.get('cumulative_delta', 0),
            'net_delta': delta_analysis.get('net_delta', 0),
            'order_flow_strength': delta_analysis.get('order_flow_strength', 0),
            'delta_divergence': delta_analysis.get('delta_divergence', 0),
            'interpretation': self._interpret_delta_signals(delta_analysis)
        }
    
    def _analyze_volume_signals(self, volume_profile: Dict) -> Dict[str, Any]:
        """Provide detailed volume analysis"""
        return {
            'volume_imbalance': volume_profile.get('volume_imbalance', 0),
            'total_volume': volume_profile.get('total_volume', 0),
            'buying_volume': volume_profile.get('buying_volume', 0),
            'selling_volume': volume_profile.get('selling_volume', 0),
            'interpretation': self._interpret_volume_signals(volume_profile)
        }
    
    def _analyze_depth_signals(self, market_depth: Dict) -> Dict[str, Any]:
        """Provide detailed market depth analysis"""
        return {
            'imbalance_ratio': market_depth.get('imbalance_ratio', 0.5),
            'spread': market_depth.get('spread', 0),
            'total_bid_volume': market_depth.get('total_bid_volume', 0),
            'total_ask_volume': market_depth.get('total_ask_volume', 0),
            'interpretation': self._interpret_depth_signals(market_depth)
        }
    
    def _analyze_institutional_signals(self, institutional_data: Dict) -> Dict[str, Any]:
        """Provide detailed institutional analysis"""
        return {
            'dark_pool_volume': institutional_data.get('dark_pool_volume', 0),
            'block_trades_count': len(institutional_data.get('block_trades', [])),
            'float_short': institutional_data.get('float_short', 0),
            'interpretation': self._interpret_institutional_signals(institutional_data)
        }
    
    def _interpret_delta_signals(self, delta_analysis: Dict) -> str:
        """Interpret delta signals in plain English"""
        net_delta = delta_analysis.get('net_delta', 0)
        divergence = delta_analysis.get('delta_divergence', 0)
        
        if net_delta > 0 and divergence > 0.3:
            return "Strong buying pressure with bullish divergence - very positive"
        elif net_delta > 0:
            return "Net buying pressure detected - positive"
        elif net_delta < 0 and divergence < -0.3:
            return "Strong selling pressure with bearish divergence - very negative"
        elif net_delta < 0:
            return "Net selling pressure detected - negative"
        else:
            return "Balanced order flow - neutral"
    
    def _interpret_volume_signals(self, volume_profile: Dict) -> str:
        """Interpret volume signals in plain English"""
        imbalance = volume_profile.get('volume_imbalance', 0)
        
        if imbalance > 0.3:
            return "Strong buying volume dominance - bullish"
        elif imbalance > 0.1:
            return "Moderate buying volume - positive"
        elif imbalance < -0.3:
            return "Strong selling volume dominance - bearish"
        elif imbalance < -0.1:
            return "Moderate selling volume - negative"
        else:
            return "Balanced volume - neutral"
    
    def _interpret_depth_signals(self, market_depth: Dict) -> str:
        """Interpret market depth signals in plain English"""
        imbalance = market_depth.get('imbalance_ratio', 0.5)
        spread = market_depth.get('spread', 0)
        mid_price = market_depth.get('mid_price', 1)
        
        spread_pct = (spread / mid_price * 100) if mid_price > 0 else 0
        
        if imbalance > 0.6 and spread_pct < 0.1:
            return "Strong bid support with tight spread - very bullish"
        elif imbalance > 0.6:
            return "Strong bid support - bullish"
        elif imbalance < 0.4 and spread_pct < 0.1:
            return "Weak bid support but good liquidity - cautious"
        elif imbalance < 0.4:
            return "Weak bid support with wide spread - bearish"
        else:
            return "Balanced order book - neutral"
    
    def _interpret_institutional_signals(self, institutional_data: Dict) -> str:
        """Interpret institutional signals in plain English"""
        dark_pool = institutional_data.get('dark_pool_volume', 0)
        block_trades = len(institutional_data.get('block_trades', []))
        
        if dark_pool > 1000000 and block_trades > 5:
            return "High institutional activity - significant interest"
        elif dark_pool > 500000 or block_trades > 3:
            return "Moderate institutional activity - some interest"
        else:
            return "Low institutional activity - retail dominated"
    
    def _extract_volume_levels(self, volume_profile: Dict) -> Dict[str, float]:
        """Extract key price levels from volume profile"""
        return {
            'poc_price': volume_profile.get('poc_price', 0),
            'value_area_high': volume_profile.get('value_area_high', 0),
            'value_area_low': volume_profile.get('value_area_low', 0)
        }
    
    def _extract_depth_levels(self, market_depth: Dict) -> Dict[str, float]:
        """Extract key price levels from market depth"""
        levels = {}
        
        bids = market_depth.get('bids', [])
        asks = market_depth.get('asks', [])
        
        if bids:
            levels['best_bid'] = bids[0][0]
            levels['bid_support'] = sum(bid[1] for bid in bids[:5])  # Top 5 bid levels
        
        if asks:
            levels['best_ask'] = asks[0][0]
            levels['ask_resistance'] = sum(ask[1] for ask in asks[:5])  # Top 5 ask levels
        
        levels['mid_price'] = market_depth.get('mid_price', 0)
        
        return levels


# Integration function for Freqtrade strategies
async def get_enhanced_market_signals(pair: str, config: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Convenience function to get enhanced market signals for Freqtrade integration
    """
    try:
        strategy = EnhancedMarketDataStrategy(config)
        return await strategy.get_enhanced_signals(pair)
    except Exception as e:
        logger.error(f"Error getting enhanced signals: {e}")
        return {'error': str(e)}


# Example usage
if __name__ == "__main__":
    async def test_enhanced_strategy():
        """Test the enhanced strategy"""
        strategy = EnhancedMarketDataStrategy()
        
        # Test with BTC/USDT
        print("Testing enhanced signals for BTC/USDT...")
        signals = await strategy.get_enhanced_signals('BTC/USDT')
        print(f"BTC Signals: {signals}")
        
        # Test with AAPL
        print("\nTesting enhanced signals for AAPL...")
        signals = await strategy.get_enhanced_signals('AAPL')
        print(f"AAPL Signals: {signals}")
    
    # Run test
    asyncio.run(test_enhanced_strategy())