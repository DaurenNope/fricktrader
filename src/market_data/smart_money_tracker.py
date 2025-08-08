"""
Smart Money Tracker - Follow the Pros!
Track insider trading, institutional flows, and unusual options activity
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import asyncio

logger = logging.getLogger(__name__)

try:
    from openbb import obb
    OPENBB_AVAILABLE = True
    logger.info("✅ OpenBB Platform loaded for Smart Money Tracking")
except ImportError as e:
    OPENBB_AVAILABLE = False
    logger.error(f"❌ OpenBB Platform not available: {e}")

class SmartMoneyTracker:
    """
    Track smart money moves across multiple data sources
    Follow what the pros are doing before retail catches on!
    """
    
    def __init__(self):
        self.obb_available = OPENBB_AVAILABLE
        self.cache = {}
        self.cache_duration = 300  # 5 minutes cache
        
    # =============================================================================
    # 1. 🔥 UNUSUAL OPTIONS ACTIVITY (Big Money Moves)
    # =============================================================================
    
    async def get_unusual_options_activity(self, symbol: str) -> Dict[str, Any]:
        """Track unusual options activity - where smart money is betting"""
        if not self.obb_available:
            return self._create_mock_options_data(symbol)
        
        try:
            logger.info(f"🔍 Tracking unusual options activity for {symbol}")
            
            # Get unusual options flow
            try:
                unusual_flow = obb.derivatives.options.unusual(symbol=symbol)
                unusual_data = unusual_flow.to_dict('records') if hasattr(unusual_flow, 'to_dict') else []
            except Exception as e:
                logger.warning(f"Unusual options not available: {e}")
                unusual_data = []
            
            # Get put/call ratio
            try:
                pcr_data = obb.derivatives.options.pcr(symbol=symbol)
                put_call_ratio = float(pcr_data) if pcr_data else 0.5
            except Exception as e:
                logger.warning(f"Put/call ratio not available: {e}")
                put_call_ratio = 0.5
            
            # Get max pain
            try:
                max_pain_data = obb.derivatives.options.max_pain(symbol=symbol)
                max_pain = float(max_pain_data) if max_pain_data else 0
            except Exception as e:
                logger.warning(f"Max pain not available: {e}")
                max_pain = 0
            
            # Analyze the data
            analysis = self._analyze_options_flow(unusual_data, put_call_ratio, max_pain)
            
            return {
                "symbol": symbol,
                "unusual_activity": unusual_data[:10],  # Top 10 unusual trades
                "put_call_ratio": put_call_ratio,
                "max_pain": max_pain,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting options activity: {e}")
            return self._create_mock_options_data(symbol)
    
    def _analyze_options_flow(self, unusual_data: List, pcr: float, max_pain: float) -> Dict[str, Any]:
        """Analyze options flow for smart money signals"""
        
        # Analyze put/call ratio
        if pcr > 1.2:
            pcr_signal = "BEARISH"
            pcr_strength = "HIGH"
        elif pcr < 0.8:
            pcr_signal = "BULLISH" 
            pcr_strength = "HIGH"
        else:
            pcr_signal = "NEUTRAL"
            pcr_strength = "LOW"
        
        # Count unusual activity
        total_unusual = len(unusual_data)
        call_activity = len([trade for trade in unusual_data if trade.get('type', '').lower() == 'call'])
        put_activity = len([trade for trade in unusual_data if trade.get('type', '').lower() == 'put'])
        
        # Smart money signal
        if call_activity > put_activity * 2:
            smart_money_signal = "BULLISH"
        elif put_activity > call_activity * 2:
            smart_money_signal = "BEARISH"
        else:
            smart_money_signal = "NEUTRAL"
        
        return {
            "put_call_signal": pcr_signal,
            "put_call_strength": pcr_strength,
            "unusual_trades_count": total_unusual,
            "call_activity": call_activity,
            "put_activity": put_activity,
            "smart_money_signal": smart_money_signal,
            "max_pain_level": max_pain,
            "recommendation": self._get_options_recommendation(pcr_signal, smart_money_signal)
        }
    
    # =============================================================================
    # 2. 📊 INSIDER TRADING TRACKER (Executive Moves)
    # =============================================================================
    
    async def get_insider_trading_activity(self, symbol: str) -> Dict[str, Any]:
        """Track insider trading - when executives buy/sell their own stock"""
        if not self.obb_available:
            return self._create_mock_insider_data(symbol)
        
        try:
            logger.info(f"🕵️ Tracking insider trading for {symbol}")
            
            # Get insider trading data
            try:
                insider_data = obb.equity.ownership.insider_trading(symbol=symbol)
                insider_trades = insider_data.to_dict('records') if hasattr(insider_data, 'to_dict') else []
            except Exception as e:
                logger.warning(f"Insider trading data not available: {e}")
                insider_trades = []
            
            # Analyze insider activity
            analysis = self._analyze_insider_activity(insider_trades)
            
            return {
                "symbol": symbol,
                "recent_trades": insider_trades[:10],  # Last 10 insider trades
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting insider trading: {e}")
            return self._create_mock_insider_data(symbol)
    
    def _analyze_insider_activity(self, trades: List) -> Dict[str, Any]:
        """Analyze insider trading patterns"""
        
        if not trades:
            return {
                "total_trades": 0,
                "buy_trades": 0,
                "sell_trades": 0,
                "net_sentiment": "NEUTRAL",
                "signal_strength": "LOW",
                "recommendation": "No insider activity detected"
            }
        
        # Categorize trades
        buy_trades = [t for t in trades if t.get('transaction_type', '').lower() in ['buy', 'purchase', 'acquisition']]
        sell_trades = [t for t in trades if t.get('transaction_type', '').lower() in ['sell', 'sale', 'disposition']]
        
        # Calculate sentiment
        buy_count = len(buy_trades)
        sell_count = len(sell_trades)
        
        if buy_count > sell_count * 2:
            sentiment = "BULLISH"
            strength = "HIGH"
        elif sell_count > buy_count * 2:
            sentiment = "BEARISH"
            strength = "HIGH"
        else:
            sentiment = "NEUTRAL"
            strength = "MEDIUM"
        
        return {
            "total_trades": len(trades),
            "buy_trades": buy_count,
            "sell_trades": sell_count,
            "net_sentiment": sentiment,
            "signal_strength": strength,
            "recommendation": self._get_insider_recommendation(sentiment, strength)
        }
    
    # =============================================================================
    # 3. 🏦 INSTITUTIONAL FLOW TRACKER (Smart Money Institutions)
    # =============================================================================
    
    async def get_institutional_flow(self, symbol: str) -> Dict[str, Any]:
        """Track institutional ownership and flow changes"""
        if not self.obb_available:
            return self._create_mock_institutional_data(symbol)
        
        try:
            logger.info(f"🏦 Tracking institutional flow for {symbol}")
            
            # Get institutional ownership
            try:
                institutional_data = obb.equity.ownership.institutional(symbol=symbol)
                institutional_holdings = institutional_data.to_dict('records') if hasattr(institutional_data, 'to_dict') else []
            except Exception as e:
                logger.warning(f"Institutional data not available: {e}")
                institutional_holdings = []
            
            # Get short interest
            try:
                short_data = obb.equity.short.short_interest(symbol=symbol)
                short_interest = short_data.to_dict('records') if hasattr(short_data, 'to_dict') else []
            except Exception as e:
                logger.warning(f"Short interest not available: {e}")
                short_interest = []
            
            # Analyze institutional flow
            analysis = self._analyze_institutional_flow(institutional_holdings, short_interest)
            
            return {
                "symbol": symbol,
                "top_institutions": institutional_holdings[:10],
                "short_interest": short_interest,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting institutional flow: {e}")
            return self._create_mock_institutional_data(symbol)
    
    def _analyze_institutional_flow(self, institutions: List, short_data: List) -> Dict[str, Any]:
        """Analyze institutional ownership patterns"""
        
        if not institutions:
            return {
                "total_institutions": 0,
                "institutional_ownership": 0,
                "flow_signal": "NEUTRAL",
                "short_squeeze_risk": "LOW",
                "recommendation": "No institutional data available"
            }
        
        # Calculate total institutional ownership
        total_shares = sum(float(inst.get('shares', 0)) for inst in institutions)
        
        # Analyze short interest
        short_ratio = 0
        if short_data:
            latest_short = short_data[0] if short_data else {}
            short_ratio = float(latest_short.get('short_interest_ratio', 0))
        
        # Determine signals
        if short_ratio > 10:
            squeeze_risk = "HIGH"
        elif short_ratio > 5:
            squeeze_risk = "MEDIUM"
        else:
            squeeze_risk = "LOW"
        
        return {
            "total_institutions": len(institutions),
            "institutional_ownership": total_shares,
            "flow_signal": "BULLISH" if total_shares > 1000000 else "NEUTRAL",
            "short_squeeze_risk": squeeze_risk,
            "short_ratio": short_ratio,
            "recommendation": self._get_institutional_recommendation(total_shares, short_ratio)
        }
    
    # =============================================================================
    # 4. 🎯 COMPREHENSIVE SMART MONEY ANALYSIS
    # =============================================================================
    
    async def get_comprehensive_smart_money_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get complete smart money analysis combining all sources"""
        logger.info(f"🎯 Running comprehensive smart money analysis for {symbol}")
        
        # Run all analyses in parallel
        options_task = self.get_unusual_options_activity(symbol)
        insider_task = self.get_insider_trading_activity(symbol)
        institutional_task = self.get_institutional_flow(symbol)
        
        # Wait for all results
        options_data, insider_data, institutional_data = await asyncio.gather(
            options_task, insider_task, institutional_task
        )
        
        # Create comprehensive analysis
        comprehensive_analysis = self._create_comprehensive_analysis(
            options_data, insider_data, institutional_data
        )
        
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "options_flow": options_data,
            "insider_trading": insider_data,
            "institutional_flow": institutional_data,
            "comprehensive_analysis": comprehensive_analysis
        }
    
    def _create_comprehensive_analysis(self, options: Dict, insider: Dict, institutional: Dict) -> Dict[str, Any]:
        """Create comprehensive smart money analysis"""
        
        # Extract signals
        options_signal = options.get('analysis', {}).get('smart_money_signal', 'NEUTRAL')
        insider_signal = insider.get('analysis', {}).get('net_sentiment', 'NEUTRAL')
        institutional_signal = institutional.get('analysis', {}).get('flow_signal', 'NEUTRAL')
        
        # Calculate composite score
        signals = [options_signal, insider_signal, institutional_signal]
        bullish_count = signals.count('BULLISH')
        bearish_count = signals.count('BEARISH')
        
        if bullish_count >= 2:
            composite_signal = "BULLISH"
            confidence = "HIGH" if bullish_count == 3 else "MEDIUM"
        elif bearish_count >= 2:
            composite_signal = "BEARISH"
            confidence = "HIGH" if bearish_count == 3 else "MEDIUM"
        else:
            composite_signal = "NEUTRAL"
            confidence = "LOW"
        
        return {
            "composite_signal": composite_signal,
            "confidence": confidence,
            "options_signal": options_signal,
            "insider_signal": insider_signal,
            "institutional_signal": institutional_signal,
            "agreement_score": max(bullish_count, bearish_count) / 3,
            "recommendation": self._get_final_recommendation(composite_signal, confidence),
            "risk_level": "LOW" if confidence == "HIGH" else "MEDIUM" if confidence == "MEDIUM" else "HIGH"
        }
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def _get_options_recommendation(self, pcr_signal: str, smart_money_signal: str) -> str:
        if pcr_signal == "BULLISH" and smart_money_signal == "BULLISH":
            return "Strong bullish options flow - consider long positions"
        elif pcr_signal == "BEARISH" and smart_money_signal == "BEARISH":
            return "Strong bearish options flow - consider short positions or puts"
        else:
            return "Mixed options signals - wait for clearer direction"
    
    def _get_insider_recommendation(self, sentiment: str, strength: str) -> str:
        if sentiment == "BULLISH" and strength == "HIGH":
            return "Strong insider buying - executives are confident"
        elif sentiment == "BEARISH" and strength == "HIGH":
            return "Heavy insider selling - potential warning sign"
        else:
            return "Neutral insider activity - no clear signal"
    
    def _get_institutional_recommendation(self, ownership: float, short_ratio: float) -> str:
        if ownership > 1000000 and short_ratio > 10:
            return "High institutional ownership + high short interest = potential squeeze"
        elif ownership > 1000000:
            return "Strong institutional backing - smart money is accumulating"
        elif short_ratio > 10:
            return "High short interest - watch for potential squeeze"
        else:
            return "Normal institutional activity"
    
    def _get_final_recommendation(self, signal: str, confidence: str) -> str:
        if signal == "BULLISH" and confidence == "HIGH":
            return "🚀 STRONG BUY - All smart money indicators align bullish"
        elif signal == "BEARISH" and confidence == "HIGH":
            return "🔻 STRONG SELL - All smart money indicators align bearish"
        elif signal == "BULLISH" and confidence == "MEDIUM":
            return "📈 BUY - Majority of smart money indicators bullish"
        elif signal == "BEARISH" and confidence == "MEDIUM":
            return "📉 SELL - Majority of smart money indicators bearish"
        else:
            return "⏸️ HOLD - Mixed or weak smart money signals"
    
    # =============================================================================
    # MOCK DATA FOR TESTING (when OpenBB not available)
    # =============================================================================
    
    def _create_mock_options_data(self, symbol: str) -> Dict[str, Any]:
        """Create mock options data for testing"""
        return {
            "symbol": symbol,
            "unusual_activity": [
                {"type": "call", "strike": 100, "volume": 5000, "open_interest": 1000},
                {"type": "put", "strike": 95, "volume": 3000, "open_interest": 800}
            ],
            "put_call_ratio": 0.85,
            "max_pain": 98.5,
            "analysis": {
                "put_call_signal": "BULLISH",
                "smart_money_signal": "BULLISH",
                "recommendation": "Strong bullish options flow detected"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _create_mock_insider_data(self, symbol: str) -> Dict[str, Any]:
        """Create mock insider data for testing"""
        return {
            "symbol": symbol,
            "recent_trades": [
                {"name": "CEO John Smith", "transaction_type": "buy", "shares": 10000, "price": 95.50},
                {"name": "CFO Jane Doe", "transaction_type": "buy", "shares": 5000, "price": 94.25}
            ],
            "analysis": {
                "net_sentiment": "BULLISH",
                "signal_strength": "HIGH",
                "recommendation": "Strong insider buying detected"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _create_mock_institutional_data(self, symbol: str) -> Dict[str, Any]:
        """Create mock institutional data for testing"""
        return {
            "symbol": symbol,
            "top_institutions": [
                {"name": "Vanguard", "shares": 5000000, "percentage": 8.5},
                {"name": "BlackRock", "shares": 4500000, "percentage": 7.8}
            ],
            "analysis": {
                "flow_signal": "BULLISH",
                "short_squeeze_risk": "MEDIUM",
                "recommendation": "Strong institutional backing"
            },
            "timestamp": datetime.now().isoformat()
        }


# Test function
async def test_smart_money_tracker():
    """Test the smart money tracker"""
    tracker = SmartMoneyTracker()
    
    print("🔥 Testing Smart Money Tracker")
    print("=" * 50)
    
    # Test with a popular stock
    symbol = "AAPL"
    
    result = await tracker.get_comprehensive_smart_money_analysis(symbol)
    
    print(f"\n📊 Smart Money Analysis for {symbol}:")
    print(f"Composite Signal: {result['comprehensive_analysis']['composite_signal']}")
    print(f"Confidence: {result['comprehensive_analysis']['confidence']}")
    print(f"Recommendation: {result['comprehensive_analysis']['recommendation']}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_smart_money_tracker())