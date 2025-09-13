"""
Clean, Interchangeable Strategy Framework
Unified architecture for all trading strategies with standardized data access
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Trading signal types"""
    BUY = "buy"
    SELL = "sell" 
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class TimeFrame(Enum):
    """Standard timeframes"""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


@dataclass
class TradingSignal:
    """Standardized trading signal"""
    symbol: str
    signal_type: SignalType
    strength: float  # 0.0 to 1.0
    price: float
    timestamp: datetime
    strategy_name: str
    confidence: float  # 0.0 to 1.0
    reasoning: str
    metadata: Dict[str, Any]
    
    # Risk management
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: Optional[float] = None


@dataclass
class MarketData:
    """Unified market data structure"""
    symbol: str
    ohlcv: pd.DataFrame  # timestamp, open, high, low, close, volume
    orderbook: Optional[Dict[str, Any]] = None
    market_depth: Optional[Dict[str, Any]] = None
    delta_analysis: Optional[Dict[str, Any]] = None
    volume_profile: Optional[Dict[str, Any]] = None
    sentiment: Optional[Dict[str, Any]] = None
    fundamentals: Optional[Dict[str, Any]] = None
    macro_data: Optional[Dict[str, Any]] = None


class DataProvider(ABC):
    """Abstract base class for data providers"""
    
    @abstractmethod
    async def get_market_data(
        self, 
        symbol: str, 
        timeframe: TimeFrame, 
        periods: int = 100
    ) -> MarketData:
        """Get comprehensive market data"""
        pass
    
    @abstractmethod
    async def get_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """Get real-time market data"""
        pass


class TradingStrategy(ABC):
    """
    Abstract base class for all trading strategies
    Clean, standardized interface for strategy development
    """
    
    def __init__(
        self, 
        name: str,
        data_provider: DataProvider,
        config: Dict[str, Any] = None
    ):
        self.name = name
        self.data_provider = data_provider
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # Strategy state
        self.is_active = True
        self.last_signal_time: Optional[datetime] = None
        self.performance_metrics = {}
        
    @abstractmethod
    async def analyze(
        self, 
        symbol: str, 
        timeframe: TimeFrame = TimeFrame.H1
    ) -> Optional[TradingSignal]:
        """
        Core strategy logic - must be implemented by each strategy
        
        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            timeframe: Analysis timeframe
            
        Returns:
            TradingSignal or None if no signal
        """
        pass
    
    @abstractmethod
    def get_required_indicators(self) -> List[str]:
        """Return list of required technical indicators"""
        pass
    
    def validate_signal(self, signal: TradingSignal) -> bool:
        """Validate signal before sending"""
        if not signal:
            return False
            
        # Basic validation
        if signal.strength < 0 or signal.strength > 1:
            self.logger.warning(f"Invalid signal strength: {signal.strength}")
            return False
            
        if signal.confidence < 0 or signal.confidence > 1:
            self.logger.warning(f"Invalid confidence: {signal.confidence}")
            return False
            
        # Time-based validation (prevent spam)
        min_interval = self.config.get("min_signal_interval", 300)  # 5 minutes default
        if (self.last_signal_time and 
            (datetime.now() - self.last_signal_time).seconds < min_interval):
            self.logger.info("Signal suppressed - too soon after last signal")
            return False
            
        return True
    
    async def execute_strategy(
        self, 
        symbol: str, 
        timeframe: TimeFrame = TimeFrame.H1
    ) -> Optional[TradingSignal]:
        """Execute strategy with error handling and logging"""
        try:
            if not self.is_active:
                return None
                
            self.logger.info(f"Executing {self.name} strategy for {symbol}")
            
            # Run strategy analysis
            signal = await self.analyze(symbol, timeframe)
            
            if signal and self.validate_signal(signal):
                self.last_signal_time = datetime.now()
                self.logger.info(
                    f"Generated {signal.signal_type.value} signal: "
                    f"strength={signal.strength:.2f}, confidence={signal.confidence:.2f}"
                )
                return signal
            else:
                self.logger.debug("No valid signal generated")
                return None
                
        except Exception as e:
            self.logger.error(f"Strategy execution failed: {e}")
            return None


class MultiSignalStrategy(TradingStrategy):
    """
    Multi-signal strategy combining multiple indicators and data sources
    Clean implementation of the current MultiSignalStrategy
    """
    
    def __init__(self, data_provider: DataProvider, config: Dict[str, Any] = None):
        super().__init__("MultiSignal", data_provider, config)
        
        # Configure signal weights
        self.weights = config.get("signal_weights", {
            "technical": 0.4,
            "sentiment": 0.2,
            "volume": 0.2,
            "momentum": 0.2
        })
        
        # Thresholds
        self.buy_threshold = config.get("buy_threshold", 0.7)
        self.sell_threshold = config.get("sell_threshold", 0.3)
        
    def get_required_indicators(self) -> List[str]:
        """Required technical indicators"""
        return [
            "sma_20", "sma_50", "ema_12", "ema_26",
            "rsi", "macd", "bb_upper", "bb_lower", "bb_middle",
            "volume_sma", "atr"
        ]
    
    async def analyze(
        self, 
        symbol: str, 
        timeframe: TimeFrame = TimeFrame.H1
    ) -> Optional[TradingSignal]:
        """Multi-signal analysis combining various data sources"""
        
        # Get comprehensive market data
        market_data = await self.data_provider.get_market_data(
            symbol, timeframe, periods=200
        )
        
        if market_data.ohlcv.empty:
            self.logger.warning(f"No market data available for {symbol}")
            return None
        
        # Calculate technical indicators
        technical_score = self._calculate_technical_score(market_data.ohlcv)
        
        # Analyze market depth and delta
        orderflow_score = self._analyze_order_flow(market_data)
        
        # Sentiment analysis
        sentiment_score = self._analyze_sentiment(market_data)
        
        # Volume analysis
        volume_score = self._analyze_volume(market_data.ohlcv)
        
        # Combine signals with weights
        total_score = (
            technical_score * self.weights["technical"] +
            sentiment_score * self.weights["sentiment"] +
            volume_score * self.weights["volume"] +
            orderflow_score * self.weights["momentum"]
        )
        
        # Generate signal
        current_price = float(market_data.ohlcv['close'].iloc[-1])
        
        signal_type = SignalType.HOLD
        if total_score >= self.buy_threshold:
            signal_type = SignalType.BUY
        elif total_score <= self.sell_threshold:
            signal_type = SignalType.SELL
        
        # Calculate confidence based on signal consensus
        confidence = abs(total_score - 0.5) * 2  # Scale to 0-1
        
        # Create signal
        if signal_type != SignalType.HOLD:
            return TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                strength=abs(total_score - 0.5) * 2,  # Distance from neutral
                price=current_price,
                timestamp=datetime.now(),
                strategy_name=self.name,
                confidence=confidence,
                reasoning=self._generate_reasoning(
                    technical_score, sentiment_score, volume_score, orderflow_score
                ),
                metadata={
                    "technical_score": technical_score,
                    "sentiment_score": sentiment_score,
                    "volume_score": volume_score,
                    "orderflow_score": orderflow_score,
                    "total_score": total_score,
                    "timeframe": timeframe.value
                },
                stop_loss=self._calculate_stop_loss(market_data.ohlcv, signal_type),
                take_profit=self._calculate_take_profit(market_data.ohlcv, signal_type)
            )
        
        return None
    
    def _calculate_technical_score(self, df: pd.DataFrame) -> float:
        """Calculate technical analysis score"""
        try:
            # Calculate indicators
            df = self._add_technical_indicators(df)
            
            latest = df.iloc[-1]
            score = 0.5  # Start neutral
            
            # Moving average signals
            if latest['close'] > latest['sma_20']:
                score += 0.1
            if latest['close'] > latest['sma_50']:
                score += 0.1
            if latest['sma_20'] > latest['sma_50']:
                score += 0.1
                
            # RSI
            if 30 <= latest['rsi'] <= 70:  # Not overbought/oversold
                if latest['rsi'] > 50:
                    score += 0.05
                else:
                    score -= 0.05
                    
            # MACD
            if latest['macd'] > latest['macd_signal']:
                score += 0.1
                
            # Bollinger Bands
            if latest['close'] < latest['bb_lower']:
                score += 0.05  # Oversold, potential bounce
            elif latest['close'] > latest['bb_upper']:
                score -= 0.05  # Overbought
                
            return max(0, min(1, score))
            
        except Exception as e:
            self.logger.error(f"Error calculating technical score: {e}")
            return 0.5
    
    def _analyze_order_flow(self, market_data: MarketData) -> float:
        """Analyze order flow and market depth"""
        try:
            score = 0.5
            
            if market_data.delta_analysis:
                delta = market_data.delta_analysis
                
                # Net delta
                if delta.get('net_delta', 0) > 0:
                    score += 0.1
                elif delta.get('net_delta', 0) < 0:
                    score -= 0.1
                    
                # Institutional flow
                institutional_flow = delta.get('institutional_flow', 0.5)
                if institutional_flow > 0.6:
                    score += 0.05
                    
            if market_data.market_depth:
                depth = market_data.market_depth
                
                # Order book imbalance
                imbalance = depth.get('imbalance_ratio', 0.5)
                if imbalance > 0.6:
                    score += 0.1
                elif imbalance < 0.4:
                    score -= 0.1
                    
            return max(0, min(1, score))
            
        except Exception as e:
            self.logger.error(f"Error analyzing order flow: {e}")
            return 0.5
    
    def _analyze_sentiment(self, market_data: MarketData) -> float:
        """Analyze market sentiment"""
        try:
            score = 0.5
            
            if market_data.sentiment:
                sentiment_data = market_data.sentiment
                
                # Social sentiment
                if 'social_score' in sentiment_data:
                    social_score = sentiment_data['social_score']
                    score = score * 0.5 + social_score * 0.5
                    
            return max(0, min(1, score))
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}")
            return 0.5
    
    def _analyze_volume(self, df: pd.DataFrame) -> float:
        """Analyze volume patterns"""
        try:
            score = 0.5
            
            # Volume moving average
            df['volume_sma_20'] = df['volume'].rolling(20).mean()
            
            latest = df.iloc[-1]
            
            # High volume confirmation
            if latest['volume'] > latest['volume_sma_20'] * 1.5:
                # High volume - check if price is moving in same direction
                price_change = (latest['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close']
                if price_change > 0:
                    score += 0.1
                else:
                    score -= 0.1
                    
            return max(0, min(1, score))
            
        except Exception as e:
            self.logger.error(f"Error analyzing volume: {e}")
            return 0.5
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to dataframe"""
        # Simple Moving Averages
        df['sma_20'] = df['close'].rolling(20).mean()
        df['sma_50'] = df['close'].rolling(50).mean()
        
        # Exponential Moving Averages
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr'] = true_range.rolling(14).mean()
        
        return df
    
    def _calculate_stop_loss(self, df: pd.DataFrame, signal_type: SignalType) -> float:
        """Calculate stop loss level"""
        try:
            current_price = float(df['close'].iloc[-1])
            atr = float(df['atr'].iloc[-1]) if 'atr' in df else current_price * 0.02
            
            if signal_type == SignalType.BUY:
                return current_price - (2 * atr)  # 2 ATR stop loss
            else:
                return current_price + (2 * atr)
                
        except Exception as e:
            self.logger.error(f"Error calculating stop loss: {e}")
            return None
    
    def _calculate_take_profit(self, df: pd.DataFrame, signal_type: SignalType) -> float:
        """Calculate take profit level"""
        try:
            current_price = float(df['close'].iloc[-1])
            atr = float(df['atr'].iloc[-1]) if 'atr' in df else current_price * 0.02
            
            if signal_type == SignalType.BUY:
                return current_price + (3 * atr)  # 3 ATR take profit (1:1.5 R:R)
            else:
                return current_price - (3 * atr)
                
        except Exception as e:
            self.logger.error(f"Error calculating take profit: {e}")
            return None
    
    def _generate_reasoning(
        self, 
        technical: float, 
        sentiment: float, 
        volume: float, 
        orderflow: float
    ) -> str:
        """Generate human-readable reasoning for the signal"""
        components = []
        
        if technical > 0.6:
            components.append("Strong technical indicators")
        elif technical < 0.4:
            components.append("Weak technical indicators")
            
        if sentiment > 0.6:
            components.append("Positive market sentiment")
        elif sentiment < 0.4:
            components.append("Negative market sentiment")
            
        if volume > 0.6:
            components.append("Strong volume confirmation")
        elif volume < 0.4:
            components.append("Weak volume")
            
        if orderflow > 0.6:
            components.append("Bullish order flow")
        elif orderflow < 0.4:
            components.append("Bearish order flow")
        
        if not components:
            return "Neutral market conditions"
            
        return "; ".join(components)


class StrategyManager:
    """
    Manages multiple trading strategies
    Provides unified interface for strategy execution and management
    """
    
    def __init__(self, data_provider: DataProvider):
        self.data_provider = data_provider
        self.strategies: List[TradingStrategy] = []
        self.logger = logging.getLogger(__name__)
        
    def add_strategy(self, strategy: TradingStrategy):
        """Add a strategy to the manager"""
        self.strategies.append(strategy)
        self.logger.info(f"Added strategy: {strategy.name}")
        
    def remove_strategy(self, strategy_name: str):
        """Remove a strategy by name"""
        self.strategies = [s for s in self.strategies if s.name != strategy_name]
        self.logger.info(f"Removed strategy: {strategy_name}")
        
    async def execute_all_strategies(
        self, 
        symbol: str, 
        timeframe: TimeFrame = TimeFrame.H1
    ) -> List[TradingSignal]:
        """Execute all active strategies"""
        signals = []
        
        tasks = [
            strategy.execute_strategy(symbol, timeframe) 
            for strategy in self.strategies if strategy.is_active
        ]
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(
                        f"Strategy {self.strategies[i].name} failed: {result}"
                    )
                elif result:
                    signals.append(result)
        
        return signals
    
    def get_strategy_status(self) -> Dict[str, Any]:
        """Get status of all strategies"""
        return {
            "total_strategies": len(self.strategies),
            "active_strategies": len([s for s in self.strategies if s.is_active]),
            "strategies": [
                {
                    "name": s.name,
                    "active": s.is_active,
                    "last_signal": s.last_signal_time.isoformat() if s.last_signal_time else None
                }
                for s in self.strategies
            ]
        }