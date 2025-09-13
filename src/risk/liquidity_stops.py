"""
Liquidity-Based Stop Loss System
Places stops based on order book depth, support/resistance levels, and market microstructure
Avoids thin liquidity areas and adapts to real market conditions
"""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class LiquidityStopManager:
    """
    Advanced stop loss system based on market microstructure and liquidity analysis
    """
    
    def __init__(self, exchange_client=None):
        self.exchange = exchange_client
        self.order_book_cache = {}
        self.cache_duration = 30  # seconds
        self.min_liquidity_threshold = 50000  # USD equivalent
        self.max_spread_threshold = 0.005  # 0.5% max spread
        
    def get_intelligent_stop_loss(self, pair: str, entry_price: float, 
                                position_size: float, trade_direction: str = "long") -> Dict:
        """
        Calculate intelligent stop loss based on liquidity and market structure
        
        Returns:
            Dict with stop_price, reasoning, confidence, and risk metrics
        """
        try:
            # Get market data
            order_book = self._get_order_book(pair)
            recent_prices = self._get_recent_price_levels(pair)
            
            # Calculate multiple stop loss candidates
            candidates = []
            
            # 1. Liquidity-based stop
            liquidity_stop = self._calculate_liquidity_stop(
                pair, entry_price, order_book, trade_direction
            )
            if liquidity_stop:
                candidates.append(liquidity_stop)
            
            # 2. Support/Resistance stop
            sr_stop = self._calculate_support_resistance_stop(
                pair, entry_price, recent_prices, trade_direction
            )
            if sr_stop:
                candidates.append(sr_stop)
            
            # 3. Volume Profile stop
            vp_stop = self._calculate_volume_profile_stop(
                pair, entry_price, recent_prices, trade_direction
            )
            if vp_stop:
                candidates.append(vp_stop)
            
            # 4. ATR-based adaptive stop
            atr_stop = self._calculate_adaptive_atr_stop(
                pair, entry_price, recent_prices, trade_direction
            )
            if atr_stop:
                candidates.append(atr_stop)
            
            # Select best stop loss candidate
            best_stop = self._select_optimal_stop(candidates, entry_price, 
                                                position_size, trade_direction)
            
            return best_stop
            
        except Exception as e:
            logger.error(f"Error calculating intelligent stop loss: {e}")
            # Fallback to conservative fixed stop
            fallback_stop = entry_price * 0.97 if trade_direction == "long" else entry_price * 1.03
            return {
                "stop_price": fallback_stop,
                "reasoning": "Fallback - liquidity analysis failed",
                "confidence": 0.3,
                "risk_reward_ratio": 3.0,
                "liquidity_score": 0.5
            }
    
    def _get_order_book(self, pair: str) -> Optional[Dict]:
        """Get order book data with caching"""
        cache_key = f"orderbook_{pair}"
        current_time = datetime.now().timestamp()
        
        # Check cache
        if (cache_key in self.order_book_cache and 
            current_time - self.order_book_cache[cache_key]["timestamp"] < self.cache_duration):
            return self.order_book_cache[cache_key]["data"]
        
        try:
            if self.exchange:
                # In production, would fetch real order book
                order_book = self.exchange.fetch_order_book(pair, limit=100)
            else:
                # Mock order book for demo
                order_book = self._generate_mock_order_book(pair)
            
            # Cache the result
            self.order_book_cache[cache_key] = {
                "data": order_book,
                "timestamp": current_time
            }
            
            return order_book
            
        except Exception as e:
            logger.error(f"Error fetching order book for {pair}: {e}")
            return None
    
    def _generate_mock_order_book(self, pair: str) -> Dict:
        """Generate realistic mock order book for testing"""
        # Simulate current price around $100 for demo
        base_price = 100.0
        
        bids = []
        asks = []
        
        # Generate realistic bid/ask levels with varying liquidity
        for i in range(50):
            # Bids (buy orders) below current price
            bid_price = base_price * (1 - (i * 0.001))  # 0.1% increments
            bid_size = np.random.exponential(1000) * (1 / (i + 1))  # Decreasing liquidity
            bids.append([bid_price, bid_size])
            
            # Asks (sell orders) above current price
            ask_price = base_price * (1 + (i * 0.001))
            ask_size = np.random.exponential(1000) * (1 / (i + 1))
            asks.append([ask_price, ask_size])
        
        return {
            "bids": bids,
            "asks": asks,
            "timestamp": datetime.now().timestamp()
        }
    
    def _get_recent_price_levels(self, pair: str) -> List[Dict]:
        """Get recent price action for support/resistance analysis"""
        # In production, would fetch real OHLCV data
        # For demo, generate realistic price levels
        
        base_price = 100.0
        price_levels = []
        
        # Generate 100 recent candles with realistic price action
        for i in range(100):
            price_variation = np.random.normal(0, 0.02)  # 2% standard deviation
            price = base_price * (1 + price_variation)
            
            high = price * (1 + abs(np.random.normal(0, 0.01)))
            low = price * (1 - abs(np.random.normal(0, 0.01)))
            volume = np.random.exponential(10000)
            
            price_levels.append({
                "open": price,
                "high": high,
                "low": low,
                "close": price * (1 + np.random.normal(0, 0.005)),
                "volume": volume,
                "timestamp": datetime.now().timestamp() - (i * 900)  # 15 min intervals
            })
        
        return price_levels
    
    def _calculate_liquidity_stop(self, pair: str, entry_price: float, 
                                order_book: Dict, direction: str) -> Optional[Dict]:
        """Calculate stop based on order book liquidity"""
        if not order_book:
            return None
        
        try:
            if direction == "long":
                # For long positions, look at bid liquidity below entry
                relevant_orders = [
                    [price, size] for price, size in order_book["bids"] 
                    if price < entry_price
                ]
            else:
                # For short positions, look at ask liquidity above entry
                relevant_orders = [
                    [price, size] for price, size in order_book["asks"] 
                    if price > entry_price
                ]
            
            if not relevant_orders:
                return None
            
            # Find areas of thin liquidity (gaps in order book)
            liquidity_gaps = self._find_liquidity_gaps(relevant_orders, entry_price)
            
            # Calculate cumulative liquidity at each level
            cumulative_liquidity = self._calculate_cumulative_liquidity(relevant_orders)
            
            # Find optimal stop placement before major liquidity gaps
            optimal_stop = self._find_optimal_liquidity_stop(
                liquidity_gaps, cumulative_liquidity, entry_price, direction
            )
            
            if optimal_stop:
                return {
                    "stop_price": optimal_stop["price"],
                    "reasoning": f"Liquidity-based: {optimal_stop['reason']}",
                    "confidence": optimal_stop["confidence"],
                    "liquidity_score": optimal_stop["liquidity_score"],
                    "risk_reward_ratio": abs(entry_price - optimal_stop["price"]) / entry_price
                }
            
        except Exception as e:
            logger.error(f"Error calculating liquidity stop: {e}")
        
        return None
    
    def _find_liquidity_gaps(self, orders: List, entry_price: float) -> List[Dict]:
        """Identify significant gaps in order book liquidity"""
        gaps = []
        
        for i in range(len(orders) - 1):
            current_price = orders[i][0]
            next_price = orders[i + 1][0]
            current_size = orders[i][1]
            next_size = orders[i + 1][1]
            
            # Calculate price gap and size drop
            price_gap = abs(current_price - next_price) / entry_price
            size_drop = (current_size - next_size) / current_size if current_size > 0 else 0
            
            # Identify significant gaps (large price gap or liquidity drop)
            if price_gap > 0.002 or size_drop > 0.7:  # 0.2% price gap or 70% liquidity drop
                gaps.append({
                    "price": current_price,
                    "gap_size": price_gap,
                    "liquidity_drop": size_drop,
                    "severity": price_gap + size_drop  # Combined severity score
                })
        
        return sorted(gaps, key=lambda x: x["severity"], reverse=True)
    
    def _calculate_cumulative_liquidity(self, orders: List) -> List[Dict]:
        """Calculate cumulative liquidity at each price level"""
        cumulative = []
        total_liquidity = 0
        
        for price, size in orders:
            total_liquidity += size
            cumulative.append({
                "price": price,
                "cumulative_liquidity": total_liquidity,
                "individual_size": size
            })
        
        return cumulative
    
    def _find_optimal_liquidity_stop(self, gaps: List, cumulative: List, 
                                   entry_price: float, direction: str) -> Optional[Dict]:
        """Find optimal stop placement considering liquidity"""
        
        if not gaps or not cumulative:
            return None
        
        # Look for the first significant liquidity gap
        for gap in gaps[:3]:  # Check top 3 gaps
            gap_price = gap["price"]
            
            # Find liquidity at this level
            liquidity_at_level = next(
                (level for level in cumulative if abs(level["price"] - gap_price) < 0.01),
                None
            )
            
            if liquidity_at_level:
                # Calculate stop placement just before the gap
                if direction == "long":
                    stop_price = gap_price * 1.001  # Slightly above the gap
                else:
                    stop_price = gap_price * 0.999  # Slightly below the gap
                
                # Validate stop placement
                risk_percent = abs(entry_price - stop_price) / entry_price
                
                if 0.01 <= risk_percent <= 0.05:  # Between 1-5% risk
                    return {
                        "price": stop_price,
                        "reason": f"Before liquidity gap (severity: {gap['severity']:.3f})",
                        "confidence": min(0.9, 0.5 + gap['severity']),
                        "liquidity_score": min(1.0, liquidity_at_level["cumulative_liquidity"] / 10000)
                    }
        
        return None
    
    def _calculate_support_resistance_stop(self, pair: str, entry_price: float, 
                                         price_history: List, direction: str) -> Optional[Dict]:
        """Calculate stop based on support/resistance levels"""
        
        if not price_history:
            return None
        
        try:
            # Extract price levels
            prices = pd.DataFrame(price_history)
            
            # Find significant support/resistance levels
            if direction == "long":
                # Look for support levels below entry
                support_levels = self._find_support_levels(prices, entry_price)
                if support_levels:
                    strongest_support = max(support_levels, key=lambda x: x["strength"])
                    stop_price = strongest_support["price"] * 0.995  # Slightly below support
                    
                    return {
                        "stop_price": stop_price,
                        "reasoning": f"Below support level (strength: {strongest_support['strength']:.2f})",
                        "confidence": min(0.9, strongest_support["strength"] / 10),
                        "risk_reward_ratio": abs(entry_price - stop_price) / entry_price * 3
                    }
            else:
                # Look for resistance levels above entry
                resistance_levels = self._find_resistance_levels(prices, entry_price)
                if resistance_levels:
                    strongest_resistance = max(resistance_levels, key=lambda x: x["strength"])
                    stop_price = strongest_resistance["price"] * 1.005  # Slightly above resistance
                    
                    return {
                        "stop_price": stop_price,
                        "reasoning": f"Above resistance level (strength: {strongest_resistance['strength']:.2f})",
                        "confidence": min(0.9, strongest_resistance["strength"] / 10),
                        "risk_reward_ratio": abs(entry_price - stop_price) / entry_price * 3
                    }
        
        except Exception as e:
            logger.error(f"Error calculating S/R stop: {e}")
        
        return None
    
    def _find_support_levels(self, prices: pd.DataFrame, entry_price: float) -> List[Dict]:
        """Identify support levels from price history"""
        support_levels = []
        
        # Find local lows
        lows = prices['low'].values
        
        for i in range(2, len(lows) - 2):
            if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and 
                lows[i] < lows[i+1] and lows[i] < lows[i+2] and
                lows[i] < entry_price):
                
                # Calculate strength based on how many times price bounced from this level
                strength = self._calculate_level_strength(lows, lows[i], tolerance=0.01)
                
                if strength >= 2:  # At least 2 touches
                    support_levels.append({
                        "price": lows[i],
                        "strength": strength,
                        "touches": strength
                    })
        
        return support_levels
    
    def _find_resistance_levels(self, prices: pd.DataFrame, entry_price: float) -> List[Dict]:
        """Identify resistance levels from price history"""
        resistance_levels = []
        
        # Find local highs
        highs = prices['high'].values
        
        for i in range(2, len(highs) - 2):
            if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and 
                highs[i] > highs[i+1] and highs[i] > highs[i+2] and
                highs[i] > entry_price):
                
                # Calculate strength
                strength = self._calculate_level_strength(highs, highs[i], tolerance=0.01)
                
                if strength >= 2:
                    resistance_levels.append({
                        "price": highs[i],
                        "strength": strength,
                        "touches": strength
                    })
        
        return resistance_levels
    
    def _calculate_level_strength(self, prices: np.array, level: float, tolerance: float) -> int:
        """Calculate how many times price touched a specific level"""
        touches = 0
        for price in prices:
            if abs(price - level) / level <= tolerance:
                touches += 1
        return touches
    
    def _calculate_volume_profile_stop(self, pair: str, entry_price: float, 
                                     price_history: List, direction: str) -> Optional[Dict]:
        """Calculate stop based on volume profile analysis"""
        
        if not price_history:
            return None
        
        try:
            # Calculate volume at price levels
            volume_profile = self._calculate_volume_at_price(price_history)
            
            # Find high volume nodes (support/resistance)
            hvn_levels = self._find_high_volume_nodes(volume_profile, entry_price, direction)
            
            if hvn_levels:
                best_hvn = hvn_levels[0]  # Closest high volume node
                
                if direction == "long":
                    stop_price = best_hvn["price"] * 0.995
                else:
                    stop_price = best_hvn["price"] * 1.005
                
                return {
                    "stop_price": stop_price,
                    "reasoning": f"Volume profile HVN (volume: {best_hvn['volume']:.0f})",
                    "confidence": min(0.8, best_hvn["volume"] / 50000),
                    "risk_reward_ratio": abs(entry_price - stop_price) / entry_price * 2.5
                }
        
        except Exception as e:
            logger.error(f"Error calculating volume profile stop: {e}")
        
        return None
    
    def _calculate_volume_at_price(self, price_history: List) -> Dict:
        """Calculate volume distribution at different price levels"""
        volume_profile = {}
        
        for candle in price_history:
            # Distribute volume across the candle's price range
            price_range = candle["high"] - candle["low"]
            if price_range > 0:
                volume_per_level = candle["volume"] / (price_range * 1000)  # Volume per price point
                
                # Distribute volume (simplified - assumes uniform distribution)
                mid_price = (candle["high"] + candle["low"]) / 2
                price_bucket = round(mid_price, 2)  # Round to nearest cent
                
                volume_profile[price_bucket] = volume_profile.get(price_bucket, 0) + candle["volume"]
        
        return volume_profile
    
    def _find_high_volume_nodes(self, volume_profile: Dict, entry_price: float, 
                              direction: str) -> List[Dict]:
        """Find high volume nodes for stop placement"""
        
        # Sort by volume
        sorted_levels = sorted(volume_profile.items(), key=lambda x: x[1], reverse=True)
        
        hvn_levels = []
        for price, volume in sorted_levels[:10]:  # Top 10 volume levels
            if direction == "long" and price < entry_price:
                hvn_levels.append({"price": price, "volume": volume})
            elif direction == "short" and price > entry_price:
                hvn_levels.append({"price": price, "volume": volume})
        
        # Sort by proximity to entry price
        hvn_levels.sort(key=lambda x: abs(x["price"] - entry_price))
        
        return hvn_levels[:3]  # Return top 3 closest HVN levels
    
    def _calculate_adaptive_atr_stop(self, pair: str, entry_price: float, 
                                   price_history: List, direction: str) -> Optional[Dict]:
        """Calculate ATR-based stop adjusted for current volatility"""
        
        if len(price_history) < 14:
            return None
        
        try:
            # Calculate ATR
            prices = pd.DataFrame(price_history)
            high_low = prices['high'] - prices['low']
            high_close = abs(prices['high'] - prices['close'].shift(1))
            low_close = abs(prices['low'] - prices['close'].shift(1))
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(14).mean().iloc[-1]
            
            # Adjust ATR based on recent volatility
            recent_volatility = true_range.rolling(5).mean().iloc[-1]
            volatility_ratio = recent_volatility / atr
            
            # Dynamic multiplier based on volatility
            if volatility_ratio > 1.5:  # High volatility
                atr_multiplier = 2.5
            elif volatility_ratio > 1.2:  # Medium volatility
                atr_multiplier = 2.0
            else:  # Low volatility
                atr_multiplier = 1.5
            
            if direction == "long":
                stop_price = entry_price - (atr * atr_multiplier)
            else:
                stop_price = entry_price + (atr * atr_multiplier)
            
            return {
                "stop_price": stop_price,
                "reasoning": f"Adaptive ATR ({atr_multiplier:.1f}x, vol ratio: {volatility_ratio:.2f})",
                "confidence": 0.7,
                "risk_reward_ratio": atr_multiplier * 2,
                "atr_value": atr,
                "volatility_adjustment": volatility_ratio
            }
        
        except Exception as e:
            logger.error(f"Error calculating ATR stop: {e}")
        
        return None
    
    def _select_optimal_stop(self, candidates: List[Dict], entry_price: float, 
                           position_size: float, direction: str) -> Dict:
        """Select the best stop loss from all candidates"""
        
        if not candidates:
            # Ultimate fallback
            fallback_stop = entry_price * 0.97 if direction == "long" else entry_price * 1.03
            return {
                "stop_price": fallback_stop,
                "reasoning": "No candidates - using fallback",
                "confidence": 0.3,
                "risk_reward_ratio": 3.0
            }
        
        # Score each candidate
        for candidate in candidates:
            risk_percent = abs(entry_price - candidate["stop_price"]) / entry_price
            
            # Scoring factors
            confidence_score = candidate.get("confidence", 0.5) * 0.4
            risk_score = max(0, (0.05 - risk_percent) / 0.05) * 0.3  # Prefer 1-5% risk
            rr_score = min(1.0, candidate.get("risk_reward_ratio", 2.0) / 5.0) * 0.3
            
            candidate["total_score"] = confidence_score + risk_score + rr_score
            candidate["risk_percent"] = risk_percent
        
        # Select highest scoring candidate
        best_candidate = max(candidates, key=lambda x: x["total_score"])
        
        logger.info(f"Selected stop: {best_candidate['reasoning']} "
                   f"@ {best_candidate['stop_price']:.4f} "
                   f"(Risk: {best_candidate['risk_percent']:.2%}, "
                   f"Score: {best_candidate['total_score']:.3f})")
        
        return best_candidate