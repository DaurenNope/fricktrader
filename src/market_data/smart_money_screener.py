"""
Smart Money Screener - Find Stocks with Strong Smart Money Activity
Scan multiple symbols for unusual options, insider trading, and institutional flows
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

logger = logging.getLogger(__name__)

try:
    from smart_money_tracker import SmartMoneyTracker
    SMART_MONEY_AVAILABLE = True
except ImportError:
    try:
        from .smart_money_tracker import SmartMoneyTracker
        SMART_MONEY_AVAILABLE = True
    except ImportError:
        SMART_MONEY_AVAILABLE = False
        logger.error("Smart Money Tracker not available")

class SmartMoneyScreener:
    """
    Screen multiple symbols for smart money activity
    Find the best opportunities where institutions, insiders, and options flow align
    """
    
    def __init__(self):
        self.tracker = SmartMoneyTracker() if SMART_MONEY_AVAILABLE else None
        self.cache = {}
        self.cache_duration = 600  # 10 minutes cache
        
        # Popular symbols to screen
        self.default_symbols = [
            # Large Cap Tech
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
            # Financial
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C',
            # Healthcare
            'JNJ', 'PFE', 'UNH', 'ABBV', 'MRK',
            # Consumer
            'KO', 'PEP', 'WMT', 'HD', 'MCD',
            # Energy
            'XOM', 'CVX', 'COP', 'SLB',
            # Crypto-related
            'COIN', 'MSTR', 'RIOT', 'MARA',
            # Popular ETFs
            'SPY', 'QQQ', 'IWM', 'GLD', 'TLT'
        ]
    
    async def screen_symbols(self, symbols: List[str] = None, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Screen multiple symbols for smart money activity
        
        Args:
            symbols: List of symbols to screen (uses default if None)
            filters: Screening filters (confidence, signal strength, etc.)
        
        Returns:
            Dictionary with screening results and rankings
        """
        if not self.tracker:
            return {"error": "Smart Money Tracker not available"}
        
        if symbols is None:
            symbols = self.default_symbols
        
        if filters is None:
            filters = {
                'min_confidence': 'MEDIUM',
                'min_agreement_score': 0.5,
                'signals': ['BULLISH', 'BEARISH'],  # Include both
                'max_symbols': 20
            }
        
        logger.info(f"🔍 Screening {len(symbols)} symbols for smart money activity")
        
        # Screen symbols in parallel for speed
        results = await self._screen_symbols_parallel(symbols[:filters.get('max_symbols', 20)])
        
        # Filter and rank results
        filtered_results = self._filter_results(results, filters)
        ranked_results = self._rank_results(filtered_results)
        
        # Create summary statistics
        summary = self._create_summary(ranked_results)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'symbols_screened': len(symbols),
            'results_found': len(ranked_results),
            'filters_applied': filters,
            'summary': summary,
            'top_opportunities': ranked_results[:10],  # Top 10
            'all_results': ranked_results
        }
    
    async def _screen_symbols_parallel(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Screen symbols in parallel for better performance"""
        
        # Create tasks for parallel execution
        tasks = []
        for symbol in symbols:
            task = self._screen_single_symbol(symbol)
            tasks.append(task)
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and None results
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error screening {symbols[i]}: {result}")
            elif result and 'error' not in result:
                valid_results.append(result)
        
        logger.info(f"✅ Successfully screened {len(valid_results)} out of {len(symbols)} symbols")
        return valid_results
    
    async def _screen_single_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Screen a single symbol for smart money activity"""
        try:
            # Get comprehensive smart money analysis
            analysis = await self.tracker.get_comprehensive_smart_money_analysis(symbol)
            
            if 'error' in analysis:
                return None
            
            # Extract key metrics
            comprehensive = analysis.get('comprehensive_analysis', {})
            options_data = analysis.get('options_flow', {}).get('analysis', {})
            insider_data = analysis.get('insider_trading', {}).get('analysis', {})
            institutional_data = analysis.get('institutional_flow', {}).get('analysis', {})
            
            # Create screening result
            result = {
                'symbol': symbol,
                'composite_signal': comprehensive.get('composite_signal', 'NEUTRAL'),
                'confidence': comprehensive.get('confidence', 'LOW'),
                'agreement_score': comprehensive.get('agreement_score', 0.0),
                'risk_level': comprehensive.get('risk_level', 'HIGH'),
                'recommendation': comprehensive.get('recommendation', ''),
                
                # Individual signal strengths
                'options_signal': comprehensive.get('options_signal', 'NEUTRAL'),
                'insider_signal': comprehensive.get('insider_signal', 'NEUTRAL'),
                'institutional_signal': comprehensive.get('institutional_signal', 'NEUTRAL'),
                
                # Detailed metrics
                'options_metrics': {
                    'put_call_ratio': options_data.get('put_call_ratio', 0.5),
                    'unusual_trades': options_data.get('unusual_trades_count', 0),
                    'smart_money_signal': options_data.get('smart_money_signal', 'NEUTRAL')
                },
                
                'insider_metrics': {
                    'total_trades': insider_data.get('total_trades', 0),
                    'buy_trades': insider_data.get('buy_trades', 0),
                    'sell_trades': insider_data.get('sell_trades', 0),
                    'net_sentiment': insider_data.get('net_sentiment', 'NEUTRAL')
                },
                
                'institutional_metrics': {
                    'ownership': institutional_data.get('institutional_ownership', 0),
                    'short_ratio': institutional_data.get('short_ratio', 0),
                    'squeeze_risk': institutional_data.get('short_squeeze_risk', 'LOW')
                },
                
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error screening {symbol}: {e}")
            return None
    
    def _filter_results(self, results: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter results based on screening criteria"""
        
        filtered = []
        
        for result in results:
            # Check confidence level
            confidence_levels = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}
            min_confidence = confidence_levels.get(filters.get('min_confidence', 'LOW'), 1)
            result_confidence = confidence_levels.get(result.get('confidence', 'LOW'), 1)
            
            if result_confidence < min_confidence:
                continue
            
            # Check agreement score
            if result.get('agreement_score', 0) < filters.get('min_agreement_score', 0):
                continue
            
            # Check signal types
            allowed_signals = filters.get('signals', ['BULLISH', 'BEARISH', 'NEUTRAL'])
            if result.get('composite_signal', 'NEUTRAL') not in allowed_signals:
                continue
            
            filtered.append(result)
        
        return filtered
    
    def _rank_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank results by smart money strength"""
        
        def calculate_score(result):
            """Calculate composite smart money score"""
            
            # Base score from agreement
            score = result.get('agreement_score', 0) * 100
            
            # Confidence bonus
            confidence_bonus = {
                'HIGH': 30,
                'MEDIUM': 15,
                'LOW': 0
            }
            score += confidence_bonus.get(result.get('confidence', 'LOW'), 0)
            
            # Signal strength bonus
            signal_bonus = {
                'BULLISH': 20,
                'BEARISH': 20,
                'NEUTRAL': 0
            }
            score += signal_bonus.get(result.get('composite_signal', 'NEUTRAL'), 0)
            
            # Individual signal bonuses
            individual_signals = [
                result.get('options_signal', 'NEUTRAL'),
                result.get('insider_signal', 'NEUTRAL'),
                result.get('institutional_signal', 'NEUTRAL')
            ]
            
            for signal in individual_signals:
                if signal in ['BULLISH', 'BEARISH']:
                    score += 10
            
            # Options activity bonus
            unusual_trades = result.get('options_metrics', {}).get('unusual_trades', 0)
            if unusual_trades > 5:
                score += 15
            elif unusual_trades > 2:
                score += 10
            
            # Insider trading bonus
            insider_trades = result.get('insider_metrics', {}).get('total_trades', 0)
            if insider_trades > 10:
                score += 15
            elif insider_trades > 5:
                score += 10
            
            # Short squeeze potential bonus
            squeeze_risk = result.get('institutional_metrics', {}).get('squeeze_risk', 'LOW')
            if squeeze_risk == 'HIGH':
                score += 25
            elif squeeze_risk == 'MEDIUM':
                score += 15
            
            return score
        
        # Calculate scores and sort
        for result in results:
            result['smart_money_score'] = calculate_score(result)
        
        # Sort by score (highest first)
        ranked = sorted(results, key=lambda x: x['smart_money_score'], reverse=True)
        
        return ranked
    
    def _create_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create summary statistics from screening results"""
        
        if not results:
            return {
                'total_opportunities': 0,
                'bullish_count': 0,
                'bearish_count': 0,
                'high_confidence_count': 0,
                'avg_agreement_score': 0,
                'top_categories': []
            }
        
        # Count signals
        bullish_count = len([r for r in results if r.get('composite_signal') == 'BULLISH'])
        bearish_count = len([r for r in results if r.get('composite_signal') == 'BEARISH'])
        high_confidence = len([r for r in results if r.get('confidence') == 'HIGH'])
        
        # Average agreement score
        avg_agreement = sum(r.get('agreement_score', 0) for r in results) / len(results)
        
        # Top categories
        categories = {}
        for result in results[:10]:  # Top 10 only
            symbol = result.get('symbol', '')
            if symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']:
                categories['Tech'] = categories.get('Tech', 0) + 1
            elif symbol in ['JPM', 'BAC', 'WFC', 'GS', 'MS']:
                categories['Financial'] = categories.get('Financial', 0) + 1
            elif symbol in ['SPY', 'QQQ', 'IWM']:
                categories['ETF'] = categories.get('ETF', 0) + 1
            elif symbol in ['COIN', 'MSTR', 'RIOT', 'MARA']:
                categories['Crypto'] = categories.get('Crypto', 0) + 1
            else:
                categories['Other'] = categories.get('Other', 0) + 1
        
        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_opportunities': len(results),
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'high_confidence_count': high_confidence,
            'avg_agreement_score': round(avg_agreement, 2),
            'top_categories': top_categories[:3]  # Top 3 categories
        }
    
    async def get_top_opportunities(self, limit: int = 10, signal_type: str = 'ALL') -> Dict[str, Any]:
        """Get top smart money opportunities quickly"""
        
        filters = {
            'min_confidence': 'MEDIUM',
            'min_agreement_score': 0.6,
            'signals': ['BULLISH', 'BEARISH'] if signal_type == 'ALL' else [signal_type],
            'max_symbols': 30  # Screen more for better results
        }
        
        results = await self.screen_symbols(filters=filters)
        
        return {
            'top_opportunities': results.get('top_opportunities', [])[:limit],
            'summary': results.get('summary', {}),
            'timestamp': results.get('timestamp', datetime.now().isoformat())
        }


# Test function
async def test_smart_money_screener():
    """Test the smart money screener"""
    screener = SmartMoneyScreener()
    
    print("🔍 Testing Smart Money Screener")
    print("=" * 50)
    
    # Test with a small set of symbols
    test_symbols = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'SPY']
    
    results = await screener.screen_symbols(test_symbols)
    
    print(f"\n📊 Screening Results:")
    print(f"Symbols Screened: {results.get('symbols_screened', 0)}")
    print(f"Opportunities Found: {results.get('results_found', 0)}")
    
    summary = results.get('summary', {})
    print(f"\n📈 Summary:")
    print(f"Bullish Opportunities: {summary.get('bullish_count', 0)}")
    print(f"Bearish Opportunities: {summary.get('bearish_count', 0)}")
    print(f"High Confidence: {summary.get('high_confidence_count', 0)}")
    print(f"Avg Agreement Score: {summary.get('avg_agreement_score', 0)}")
    
    # Show top opportunities
    top_opps = results.get('top_opportunities', [])
    if top_opps:
        print(f"\n🔥 Top Opportunities:")
        for i, opp in enumerate(top_opps[:3], 1):
            print(f"{i}. {opp.get('symbol', 'N/A')} - {opp.get('composite_signal', 'N/A')} "
                  f"({opp.get('confidence', 'N/A')} confidence, Score: {opp.get('smart_money_score', 0):.0f})")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_smart_money_screener())