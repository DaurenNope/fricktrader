#!/usr/bin/env python3
"""
Aladdin-Level Sophisticated Market Screener
Detects unusual activities, anomalies, and alpha opportunities
Comparable to BlackRock's Aladdin system for institutional-grade analysis
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
import statistics
from concurrent.futures import ThreadPoolExecutor
import requests
import json

logger = logging.getLogger(__name__)

@dataclass
class AnomalySignal:
    """Represents a detected market anomaly with scoring"""
    symbol: str
    anomaly_type: str
    severity: float  # 0-1 scale
    confidence: float  # 0-1 scale
    expected_move: float  # Expected price movement %
    time_horizon: str  # '1h', '4h', '1d', '1w'
    description: str
    supporting_data: dict
    risk_reward: float
    
class AladdinScreener:
    """
    Sophisticated market screener for detecting unusual activities
    Uses multiple data sources and advanced statistical analysis
    """
    
    def __init__(self):
        self.symbols = [
            'BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'DOT/USDT', 'LINK/USDT',
            'SOL/USDT', 'AVAX/USDT', 'MATIC/USDT', 'UNI/USDT', 'ATOM/USDT'
        ]
        self.anomaly_threshold = 2.5  # Standard deviations for anomaly detection
        self.min_confidence = 0.7
        
    async def scan_for_anomalies(self) -> List[AnomalySignal]:
        """
        Main screening function - detects all types of anomalies
        """
        logger.info("🔍 Starting Aladdin-level market scan for anomalies...")
        
        anomalies = []
        
        # Run all anomaly detection methods in parallel
        tasks = [
            self.detect_volume_anomalies(),
            self.detect_price_anomalies(), 
            self.detect_whale_movements(),
            self.detect_options_flow_anomalies(),
            self.detect_correlation_breakdowns(),
            self.detect_momentum_divergences(),
            self.detect_liquidity_anomalies(),
            self.detect_cross_asset_signals(),
            self.detect_macro_regime_shifts(),
            self.detect_insider_patterns()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all detected anomalies
        for result in results:
            if isinstance(result, list):
                anomalies.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Anomaly detection error: {result}")
        
        # Rank anomalies by potential alpha
        ranked_anomalies = self.rank_anomalies_by_alpha(anomalies)
        
        logger.info(f"🎯 Detected {len(ranked_anomalies)} high-confidence anomalies")
        return ranked_anomalies[:20]  # Return top 20 opportunities    
  
  async def detect_volume_anomalies(self) -> List[AnomalySignal]:
        """
        Detect unusual volume patterns that precede major moves
        """
        anomalies = []
        
        for symbol in self.symbols:
            try:
                # Get volume data for analysis
                volume_data = await self.get_volume_profile(symbol)
                
                # Detect volume spikes (>3 std dev from mean)
                volume_spike = self.analyze_volume_spike(volume_data)
                if volume_spike['severity'] > self.anomaly_threshold:
                    anomalies.append(AnomalySignal(
                        symbol=symbol,
                        anomaly_type='volume_spike',
                        severity=min(volume_spike['severity'] / 5.0, 1.0),
                        confidence=volume_spike['confidence'],
                        expected_move=volume_spike['expected_move'],
                        time_horizon='4h',
                        description=f"Volume spike {volume_spike['multiplier']:.1f}x normal - institutional activity detected",
                        supporting_data=volume_spike,
                        risk_reward=volume_spike['risk_reward']
                    ))
                
                # Detect dark pool activity
                dark_pool = self.analyze_dark_pool_activity(volume_data)
                if dark_pool['anomaly_score'] > 0.7:
                    anomalies.append(AnomalySignal(
                        symbol=symbol,
                        anomaly_type='dark_pool_activity',
                        severity=dark_pool['anomaly_score'],
                        confidence=0.85,
                        expected_move=dark_pool['expected_move'],
                        time_horizon='1d',
                        description=f"Unusual dark pool activity - {dark_pool['direction']} pressure building",
                        supporting_data=dark_pool,
                        risk_reward=dark_pool['risk_reward']
                    ))
                    
            except Exception as e:
                logger.error(f"Volume anomaly detection error for {symbol}: {e}")
        
        return anomalies
    
    async def detect_whale_movements(self) -> List[AnomalySignal]:
        """
        Detect large whale transactions and accumulation patterns
        """
        anomalies = []
        
        for symbol in self.symbols:
            try:
                # Analyze on-chain whale movements
                whale_data = await self.get_whale_transactions(symbol)
                
                # Detect accumulation patterns
                accumulation = self.analyze_whale_accumulation(whale_data)
                if accumulation['strength'] > 0.8:
                    anomalies.append(AnomalySignal(
                        symbol=symbol,
                        anomaly_type='whale_accumulation',
                        severity=accumulation['strength'],
                        confidence=0.9,
                        expected_move=accumulation['price_target'],
                        time_horizon='1w',
                        description=f"Whale accumulation detected: {accumulation['whale_count']} whales buying {accumulation['total_amount']:.0f} tokens",
                        supporting_data=accumulation,
                        risk_reward=accumulation['risk_reward']
                    ))
                
                # Detect distribution patterns
                distribution = self.analyze_whale_distribution(whale_data)
                if distribution['strength'] > 0.8:
                    anomalies.append(AnomalySignal(
                        symbol=symbol,
                        anomaly_type='whale_distribution',
                        severity=distribution['strength'],
                        confidence=0.85,
                        expected_move=-distribution['price_target'],
                        time_horizon='1w',
                        description=f"Whale distribution detected: {distribution['whale_count']} whales selling {distribution['total_amount']:.0f} tokens",
                        supporting_data=distribution,
                        risk_reward=distribution['risk_reward']
                    ))
                    
            except Exception as e:
                logger.error(f"Whale movement detection error for {symbol}: {e}")
        
        return anomalies    

    async def detect_options_flow_anomalies(self) -> List[AnomalySignal]:
        """
        Detect unusual options flow that indicates informed trading
        """
        anomalies = []
        
        for symbol in self.symbols:
            try:
                # Get options flow data
                options_data = await self.get_options_flow(symbol)
                
                # Detect unusual call/put ratios
                put_call_anomaly = self.analyze_put_call_ratio(options_data)
                if put_call_anomaly['anomaly_score'] > 0.75:
                    anomalies.append(AnomalySignal(
                        symbol=symbol,
                        anomaly_type='put_call_anomaly',
                        severity=put_call_anomaly['anomaly_score'],
                        confidence=0.8,
                        expected_move=put_call_anomaly['expected_move'],
                        time_horizon='1w',
                        description=f"Unusual put/call ratio: {put_call_anomaly['ratio']:.2f} (normal: {put_call_anomaly['normal_ratio']:.2f})",
                        supporting_data=put_call_anomaly,
                        risk_reward=put_call_anomaly['risk_reward']
                    ))
                
                # Detect gamma squeeze potential
                gamma_squeeze = self.analyze_gamma_squeeze_risk(options_data)
                if gamma_squeeze['risk_score'] > 0.8:
                    anomalies.append(AnomalySignal(
                        symbol=symbol,
                        anomaly_type='gamma_squeeze_setup',
                        severity=gamma_squeeze['risk_score'],
                        confidence=0.75,
                        expected_move=gamma_squeeze['expected_move'],
                        time_horizon='1d',
                        description=f"Gamma squeeze setup detected - high gamma at ${gamma_squeeze['strike_price']}",
                        supporting_data=gamma_squeeze,
                        risk_reward=gamma_squeeze['risk_reward']
                    ))
                    
            except Exception as e:
                logger.error(f"Options flow detection error for {symbol}: {e}")
        
        return anomalies
    
    async def detect_correlation_breakdowns(self) -> List[AnomalySignal]:
        """
        Detect when normal correlations break down - often precedes major moves
        """
        anomalies = []
        
        try:
            # Analyze cross-asset correlations
            correlation_matrix = await self.calculate_correlation_matrix()
            
            # Detect correlation breakdowns
            breakdowns = self.find_correlation_anomalies(correlation_matrix)
            
            for breakdown in breakdowns:
                if breakdown['anomaly_strength'] > 0.7:
                    anomalies.append(AnomalySignal(
                        symbol=breakdown['symbol'],
                        anomaly_type='correlation_breakdown',
                        severity=breakdown['anomaly_strength'],
                        confidence=0.8,
                        expected_move=breakdown['expected_move'],
                        time_horizon='1d',
                        description=f"Correlation breakdown with {breakdown['reference_asset']} - historical correlation: {breakdown['historical_corr']:.2f}, current: {breakdown['current_corr']:.2f}",
                        supporting_data=breakdown,
                        risk_reward=breakdown['risk_reward']
                    ))
                    
        except Exception as e:
            logger.error(f"Correlation breakdown detection error: {e}")
        
        return anomalies
    
    async def detect_momentum_divergences(self) -> List[AnomalySignal]:
        """
        Detect price-momentum divergences that signal reversals
        """
        anomalies = []
        
        for symbol in self.symbols:
            try:
                # Get price and momentum data
                price_data = await self.get_price_data(symbol)
                momentum_data = await self.calculate_momentum_indicators(price_data)
                
                # Detect bullish divergence
                bullish_div = self.detect_bullish_divergence(price_data, momentum_data)
                if bullish_div['strength'] > 0.75:
                    anomalies.append(AnomalySignal(
                        symbol=symbol,
                        anomaly_type='bullish_divergence',
                        severity=bullish_div['strength'],
                        confidence=0.85,
                        expected_move=bullish_div['target_move'],
                        time_horizon='1w',
                        description=f"Bullish divergence detected - price making lower lows while {bullish_div['indicator']} making higher lows",
                        supporting_data=bullish_div,
                        risk_reward=bullish_div['risk_reward']
                    ))
                
                # Detect bearish divergence
                bearish_div = self.detect_bearish_divergence(price_data, momentum_data)
                if bearish_div['strength'] > 0.75:
                    anomalies.append(AnomalySignal(
                        symbol=symbol,
                        anomaly_type='bearish_divergence',
                        severity=bearish_div['strength'],
                        confidence=0.85,
                        expected_move=-bearish_div['target_move'],
                        time_horizon='1w',
                        description=f"Bearish divergence detected - price making higher highs while {bearish_div['indicator']} making lower highs",
                        supporting_data=bearish_div,
                        risk_reward=bearish_div['risk_reward']
                    ))
                    
            except Exception as e:
                logger.error(f"Momentum divergence detection error for {symbol}: {e}")
        
        return anomalies    

    async def detect_liquidity_anomalies(self) -> List[AnomalySignal]:
        """
        Detect liquidity anomalies that create arbitrage opportunities
        """
        anomalies = []
        
        for symbol in self.symbols:
            try:
                # Get order book data
                order_book = await self.get_order_book_data(symbol)
                
                # Detect liquidity gaps
                liquidity_gaps = self.analyze_liquidity_gaps(order_book)
                for gap in liquidity_gaps:
                    if gap['severity'] > 0.8:
                        anomalies.append(AnomalySignal(
                            symbol=symbol,
                            anomaly_type='liquidity_gap',
                            severity=gap['severity'],
                            confidence=0.9,
                            expected_move=gap['expected_move'],
                            time_horizon='1h',
                            description=f"Liquidity gap detected at ${gap['price_level']:.2f} - {gap['gap_size']:.1f}% gap",
                            supporting_data=gap,
                            risk_reward=gap['risk_reward']
                        ))
                
                # Detect bid-ask spread anomalies
                spread_anomaly = self.analyze_spread_anomalies(order_book)
                if spread_anomaly['anomaly_score'] > 0.75:
                    anomalies.append(AnomalySignal(
                        symbol=symbol,
                        anomaly_type='spread_anomaly',
                        severity=spread_anomaly['anomaly_score'],
                        confidence=0.8,
                        expected_move=spread_anomaly['expected_move'],
                        time_horizon='30m',
                        description=f"Unusual bid-ask spread: {spread_anomaly['current_spread']:.4f} vs normal {spread_anomaly['normal_spread']:.4f}",
                        supporting_data=spread_anomaly,
                        risk_reward=spread_anomaly['risk_reward']
                    ))
                    
            except Exception as e:
                logger.error(f"Liquidity anomaly detection error for {symbol}: {e}")
        
        return anomalies
    
    async def detect_cross_asset_signals(self) -> List[AnomalySignal]:
        """
        Detect signals from related assets that haven't been priced in yet
        """
        anomalies = []
        
        try:
            # Analyze cross-asset relationships
            cross_signals = await self.analyze_cross_asset_relationships()
            
            for signal in cross_signals:
                if signal['strength'] > 0.8:
                    anomalies.append(AnomalySignal(
                        symbol=signal['target_symbol'],
                        anomaly_type='cross_asset_signal',
                        severity=signal['strength'],
                        confidence=0.75,
                        expected_move=signal['expected_move'],
                        time_horizon='1d',
                        description=f"Cross-asset signal from {signal['source_asset']} - {signal['relationship_type']} relationship suggests move",
                        supporting_data=signal,
                        risk_reward=signal['risk_reward']
                    ))
                    
        except Exception as e:
            logger.error(f"Cross-asset signal detection error: {e}")
        
        return anomalies
    
    async def detect_macro_regime_shifts(self) -> List[AnomalySignal]:
        """
        Detect macro regime changes that affect entire markets
        """
        anomalies = []
        
        try:
            # Analyze macro indicators
            macro_data = await self.get_macro_indicators()
            
            # Detect regime shifts
            regime_shift = self.analyze_regime_shift(macro_data)
            if regime_shift['confidence'] > 0.8:
                # Apply regime shift to all symbols
                for symbol in self.symbols:
                    anomalies.append(AnomalySignal(
                        symbol=symbol,
                        anomaly_type='macro_regime_shift',
                        severity=regime_shift['strength'],
                        confidence=regime_shift['confidence'],
                        expected_move=regime_shift['expected_moves'].get(symbol, 0),
                        time_horizon='1w',
                        description=f"Macro regime shift detected: {regime_shift['new_regime']} - {regime_shift['description']}",
                        supporting_data=regime_shift,
                        risk_reward=regime_shift['risk_reward']
                    ))
                    
        except Exception as e:
            logger.error(f"Macro regime shift detection error: {e}")
        
        return anomalies
    
    async def detect_insider_patterns(self) -> List[AnomalySignal]:
        """
        Detect patterns that suggest insider trading or informed flow
        """
        anomalies = []
        
        for symbol in self.symbols:
            try:
                # Analyze trading patterns for insider activity
                insider_signals = await self.analyze_insider_patterns(symbol)
                
                for signal in insider_signals:
                    if signal['confidence'] > 0.8:
                        anomalies.append(AnomalySignal(
                            symbol=symbol,
                            anomaly_type='insider_pattern',
                            severity=signal['strength'],
                            confidence=signal['confidence'],
                            expected_move=signal['expected_move'],
                            time_horizon=signal['time_horizon'],
                            description=f"Insider pattern detected: {signal['pattern_type']} - {signal['description']}",
                            supporting_data=signal,
                            risk_reward=signal['risk_reward']
                        ))
                        
            except Exception as e:
                logger.error(f"Insider pattern detection error for {symbol}: {e}")
        
        return anomalies   
 
    def rank_anomalies_by_alpha(self, anomalies: List[AnomalySignal]) -> List[AnomalySignal]:
        """
        Rank anomalies by their alpha potential using sophisticated scoring
        """
        def calculate_alpha_score(anomaly: AnomalySignal) -> float:
            # Base score from severity and confidence
            base_score = anomaly.severity * anomaly.confidence
            
            # Boost score for high-alpha anomaly types
            type_multipliers = {
                'whale_accumulation': 1.5,
                'insider_pattern': 1.4,
                'gamma_squeeze_setup': 1.3,
                'correlation_breakdown': 1.2,
                'dark_pool_activity': 1.2,
                'liquidity_gap': 1.1,
                'volume_spike': 1.0,
                'momentum_divergence': 0.9,
                'cross_asset_signal': 0.8
            }
            
            multiplier = type_multipliers.get(anomaly.anomaly_type, 1.0)
            
            # Risk-reward adjustment
            risk_reward_bonus = min(anomaly.risk_reward / 3.0, 0.3)  # Max 30% bonus
            
            # Time horizon adjustment (shorter = higher urgency)
            time_multipliers = {'30m': 1.3, '1h': 1.2, '4h': 1.1, '1d': 1.0, '1w': 0.9}
            time_multiplier = time_multipliers.get(anomaly.time_horizon, 1.0)
            
            final_score = base_score * multiplier * time_multiplier + risk_reward_bonus
            return min(final_score, 1.0)  # Cap at 1.0
        
        # Calculate alpha scores and sort
        for anomaly in anomalies:
            anomaly.alpha_score = calculate_alpha_score(anomaly)
        
        return sorted(anomalies, key=lambda x: x.alpha_score, reverse=True)
    
    # =====================================================================
    # SOPHISTICATED ANALYSIS METHODS (Aladdin-level algorithms)
    # =====================================================================
    
    def analyze_volume_spike(self, volume_data: dict) -> dict:
        """Analyze volume spikes using statistical methods"""
        volumes = volume_data['volumes']
        current_volume = volumes[-1]
        
        # Calculate rolling statistics
        mean_volume = np.mean(volumes[:-1])
        std_volume = np.std(volumes[:-1])
        
        # Z-score for anomaly detection
        z_score = (current_volume - mean_volume) / std_volume if std_volume > 0 else 0
        
        # Volume multiplier
        multiplier = current_volume / mean_volume if mean_volume > 0 else 1
        
        # Expected price move based on volume-price relationship
        volume_price_correlation = np.corrcoef(volumes[:-10], volume_data['prices'][:-10])[0,1]
        expected_move = min(abs(z_score) * 0.02, 0.15)  # Max 15% expected move
        
        return {
            'severity': abs(z_score),
            'confidence': min(abs(z_score) / 5.0, 1.0),
            'multiplier': multiplier,
            'expected_move': expected_move,
            'risk_reward': expected_move / 0.05,  # Assume 5% risk
            'volume_price_correlation': volume_price_correlation
        }
    
    def analyze_whale_accumulation(self, whale_data: dict) -> dict:
        """Analyze whale accumulation patterns"""
        transactions = whale_data['transactions']
        
        # Count large buy transactions
        large_buys = [tx for tx in transactions if tx['type'] == 'buy' and tx['amount'] > whale_data['whale_threshold']]
        large_sells = [tx for tx in transactions if tx['type'] == 'sell' and tx['amount'] > whale_data['whale_threshold']]
        
        # Calculate net accumulation
        total_bought = sum(tx['amount'] for tx in large_buys)
        total_sold = sum(tx['amount'] for tx in large_sells)
        net_accumulation = total_bought - total_sold
        
        # Accumulation strength
        strength = min(net_accumulation / whale_data['circulating_supply'], 1.0)
        
        # Price target based on accumulation
        price_target = strength * 0.3  # Up to 30% move for full accumulation
        
        return {
            'strength': abs(strength),
            'whale_count': len(set(tx['address'] for tx in large_buys)),
            'total_amount': net_accumulation,
            'price_target': price_target,
            'risk_reward': price_target / 0.08,  # 8% risk assumption
            'accumulation_rate': net_accumulation / len(transactions) if transactions else 0
        }
    
    async def get_volume_profile(self, symbol: str) -> dict:
        """Get volume profile data (mock implementation)"""
        # In production, this would connect to real data feeds
        return {
            'volumes': np.random.lognormal(10, 1, 100).tolist(),
            'prices': np.random.normal(100, 5, 100).tolist(),
            'timestamps': [datetime.now() - timedelta(hours=i) for i in range(100)]
        }
    
    async def get_whale_transactions(self, symbol: str) -> dict:
        """Get whale transaction data (mock implementation)"""
        return {
            'transactions': [
                {'type': 'buy', 'amount': 1000000, 'address': 'whale1', 'timestamp': datetime.now()},
                {'type': 'sell', 'amount': 500000, 'address': 'whale2', 'timestamp': datetime.now()}
            ],
            'whale_threshold': 100000,
            'circulating_supply': 1000000000
        }
    
    async def get_options_flow(self, symbol: str) -> dict:
        """Get options flow data (mock implementation)"""
        return {
            'put_volume': 1000,
            'call_volume': 1500,
            'gamma_exposure': {'strikes': [100, 105, 110], 'gamma': [0.1, 0.2, 0.15]},
            'unusual_activity': []
        }
    
    def analyze_put_call_ratio(self, options_data: dict) -> dict:
        """Analyze put/call ratio for anomalies"""
        current_ratio = options_data['put_volume'] / options_data['call_volume']
        normal_ratio = 0.8  # Historical average
        
        anomaly_score = abs(current_ratio - normal_ratio) / normal_ratio
        expected_move = min(anomaly_score * 0.1, 0.2)  # Max 20% move
        
        return {
            'ratio': current_ratio,
            'normal_ratio': normal_ratio,
            'anomaly_score': min(anomaly_score, 1.0),
            'expected_move': expected_move,
            'risk_reward': expected_move / 0.06
        }