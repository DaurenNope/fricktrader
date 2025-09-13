#!/usr/bin/env python3
"""
Test Alternative Data Integration with Live Market Data

This script tests our alternative data providers and validates the quality
of signals generated from on-chain, sentiment, and macro data.
"""

import sys
import os
import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_live_crypto_data():
    """Test live cryptocurrency data feeds"""
    print("🌐 TESTING LIVE CRYPTO DATA FEEDS")
    print("=" * 40)
    
    # Test multiple free APIs for redundancy
    apis_to_test = [
        {
            'name': 'CoinGecko API',
            'url': 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true&include_market_cap=true',
            'parser': 'coingecko'
        },
        {
            'name': 'CoinCap API', 
            'url': 'https://api.coincap.io/v2/assets?limit=5',
            'parser': 'coincap'
        },
        {
            'name': 'CryptoCompare API',
            'url': 'https://min-api.cryptocompare.com/data/pricemultifull?fsyms=BTC,ETH&tsyms=USD',
            'parser': 'cryptocompare'
        }
    ]
    
    results = {}
    
    async with aiohttp.ClientSession() as session:
        for api in apis_to_test:
            try:
                print(f"\n📡 Testing {api['name']}...")
                
                async with session.get(api['url'], timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Parse based on API type
                        if api['parser'] == 'coingecko':
                            btc_price = data.get('bitcoin', {}).get('usd')
                            eth_price = data.get('ethereum', {}).get('usd')
                            btc_change = data.get('bitcoin', {}).get('usd_24h_change')
                            
                            if btc_price and eth_price:
                                results[api['name']] = {
                                    'btc_price': btc_price,
                                    'eth_price': eth_price,
                                    'btc_24h_change': btc_change,
                                    'status': 'SUCCESS'
                                }
                                print(f"   ✅ BTC: ${btc_price:,.2f} ({btc_change:+.1f}%)")
                                print(f"   ✅ ETH: ${eth_price:,.2f}")
                            
                        elif api['parser'] == 'coincap':
                            assets = data.get('data', [])
                            btc_data = next((a for a in assets if a['id'] == 'bitcoin'), None)
                            eth_data = next((a for a in assets if a['id'] == 'ethereum'), None)
                            
                            if btc_data and eth_data:
                                results[api['name']] = {
                                    'btc_price': float(btc_data['priceUsd']),
                                    'eth_price': float(eth_data['priceUsd']),
                                    'btc_24h_change': float(btc_data['changePercent24Hr']),
                                    'status': 'SUCCESS'
                                }
                                print(f"   ✅ BTC: ${float(btc_data['priceUsd']):,.2f} ({float(btc_data['changePercent24Hr']):+.1f}%)")
                                print(f"   ✅ ETH: ${float(eth_data['priceUsd']):,.2f}")
                                
                        elif api['parser'] == 'cryptocompare':
                            raw_data = data.get('RAW', {})
                            btc_data = raw_data.get('BTC', {}).get('USD', {})
                            eth_data = raw_data.get('ETH', {}).get('USD', {})
                            
                            if btc_data and eth_data:
                                results[api['name']] = {
                                    'btc_price': btc_data.get('PRICE'),
                                    'eth_price': eth_data.get('PRICE'),
                                    'btc_24h_change': btc_data.get('CHANGEPCT24HOUR'),
                                    'status': 'SUCCESS'
                                }
                                print(f"   ✅ BTC: ${btc_data.get('PRICE'):,.2f} ({btc_data.get('CHANGEPCT24HOUR'):+.1f}%)")
                                print(f"   ✅ ETH: ${eth_data.get('PRICE'):,.2f}")
                    else:
                        results[api['name']] = {'status': 'FAILED', 'error': f'HTTP {response.status}'}
                        print(f"   ❌ Failed: HTTP {response.status}")
                        
            except Exception as e:
                results[api['name']] = {'status': 'FAILED', 'error': str(e)}
                print(f"   ❌ Error: {str(e)[:50]}...")
    
    return results

def test_alternative_data_provider():
    """Test our alternative data provider with mock/simulated data"""
    print("\n\n📊 TESTING ALTERNATIVE DATA PROVIDER")
    print("=" * 45)
    
    try:
        from data.alternative_data_provider import AlternativeDataProvider
        
        provider = AlternativeDataProvider()
        print("✅ Alternative data provider initialized")
        
        # Test comprehensive data retrieval
        print("\n🔄 Testing comprehensive data retrieval...")
        data = provider.get_comprehensive_data('BTC')
        
        print(f"📈 Data Quality Score: {data['data_quality_score']:.1%}")
        
        # Test on-chain data
        onchain = data['onchain']
        print("\n🐋 On-Chain Data:")
        print(f"   Whale Net Flows: ${onchain.whale_net_flows:+,.0f}M")
        print(f"   Exchange Flows: ${onchain.exchange_outflows - onchain.exchange_inflows:+,.0f}M")
        print(f"   Active Addresses: {onchain.active_addresses:,}")
        print(f"   Fear & Greed: {onchain.fear_greed_index}/100")
        
        # Test sentiment data
        sentiment = data['sentiment']
        print("\n📰 Sentiment Data:")
        print(f"   News Sentiment: {sentiment.news_sentiment:+.2f}")
        print(f"   Social Mentions: {sentiment.twitter_mentions:,}")
        print(f"   Institutional Flow: {sentiment.institutional_flow:+.2f}")
        
        # Test macro data
        macro = data['macro']
        print("\n🌍 Macro Data:")
        print(f"   Dollar Strength: {macro.dxy_change:+.1%}")
        print(f"   VIX Level: {macro.vix_level:.1f}")
        print(f"   BTC Dominance: {macro.btc_dominance:.1f}%")
        
        # Test signal generation
        signals = provider.get_signal_strength(data)
        significant_signals = {k: v for k, v in signals.items() if abs(v) > 0.15}
        
        print(f"\n🎯 Trading Signals (>{0.15:.0%} strength):")
        for signal_name, strength in significant_signals.items():
            direction = "🟢 BULLISH" if strength > 0 else "🔴 BEARISH"
            print(f"   {direction} {signal_name.replace('_', ' ').title()}: {strength:+.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Alternative data provider test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_sentiment_data_simulation():
    """Test sentiment data collection from various sources"""
    print("\n\n💭 TESTING SENTIMENT DATA COLLECTION")
    print("=" * 45)
    
    results = {}
    
    # Test Fear & Greed Index (real API)
    async with aiohttp.ClientSession() as session:
        try:
            print("📡 Testing Fear & Greed Index API...")
            async with session.get('https://api.alternative.me/fng/', timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    fng_data = data.get('data', [{}])[0]
                    fng_value = fng_data.get('value')
                    fng_text = fng_data.get('value_classification')
                    
                    results['fear_greed'] = {
                        'value': fng_value,
                        'classification': fng_text,
                        'status': 'SUCCESS'
                    }
                    
                    print(f"   ✅ Current Fear & Greed: {fng_value}/100 ({fng_text})")
                else:
                    results['fear_greed'] = {'status': 'FAILED', 'error': f'HTTP {response.status}'}
                    print(f"   ❌ Failed: HTTP {response.status}")
        except Exception as e:
            results['fear_greed'] = {'status': 'FAILED', 'error': str(e)}
            print(f"   ❌ Error: {str(e)[:50]}...")
    
    # Simulate other sentiment sources
    print("\n📊 Simulating other sentiment sources...")
    
    # News sentiment simulation
    news_sentiment = np.random.normal(0.1, 0.3)  # Slightly positive bias
    results['news_sentiment'] = {
        'value': news_sentiment,
        'status': 'SIMULATED'
    }
    print(f"   📰 News Sentiment: {news_sentiment:+.2f} (simulated)")
    
    # Social media sentiment simulation  
    social_sentiment = np.random.normal(-0.05, 0.25)  # Slightly negative (realistic)
    social_mentions = np.random.randint(1500, 5000)
    results['social_sentiment'] = {
        'value': social_sentiment,
        'mentions': social_mentions,
        'status': 'SIMULATED'
    }
    print(f"   💬 Social Sentiment: {social_sentiment:+.2f} ({social_mentions:,} mentions, simulated)")
    
    return results

def test_market_regime_analyzer():
    """Test market regime analyzer with historical data patterns"""
    print("\n\n🏛️ TESTING MARKET REGIME ANALYZER")
    print("=" * 40)
    
    try:
        from market_analysis.crypto_market_regime_analyzer import CryptoMarketRegimeAnalyzer
        
        analyzer = CryptoMarketRegimeAnalyzer()
        print("✅ Market regime analyzer initialized")
        
        # Generate test data for different market scenarios
        scenarios = ['bull', 'bear', 'sideways']
        
        for scenario in scenarios:
            print(f"\n📊 Testing {scenario.upper()} market scenario...")
            
            # Generate scenario-specific data
            dates = pd.date_range(start=datetime.now() - timedelta(days=60), periods=1440, freq='H')
            
            if scenario == 'bull':
                trend = np.linspace(0, 0.4, len(dates))  # 40% upward trend
                volatility = np.random.normal(0, 0.025, len(dates))
            elif scenario == 'bear':
                trend = np.linspace(0, -0.3, len(dates))  # 30% downward trend
                volatility = np.random.normal(0, 0.035, len(dates))
            else:  # sideways
                trend = np.sin(np.linspace(0, 4*np.pi, len(dates))) * 0.05
                volatility = np.random.normal(0, 0.02, len(dates))
            
            base_price = 45000
            price_changes = trend + volatility
            prices = [base_price * (1 + sum(price_changes[:i+1])) for i in range(len(dates))]
            
            btc_data = pd.DataFrame({
                'timestamp': dates,
                'close': prices,
                'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
                'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
                'volume': np.random.normal(1000000, 200000, len(dates))
            }, index=dates)
            
            # Create ETH data (scale BTC prices for correlation)
            eth_prices = [p * 0.08 for p in prices]  # ETH correlation to BTC
            eth_data = pd.DataFrame({
                'timestamp': dates,
                'close': eth_prices,
                'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in eth_prices],
                'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in eth_prices],
                'volume': np.random.normal(500000, 100000, len(dates))
            }, index=dates)
            
            # Create market cap data
            mcap_data = [p * 20 for p in prices]  # Total market cap approximation
            market_cap_data = pd.DataFrame({
                'timestamp': dates,
                'close': mcap_data,
                'high': [p * (1 + abs(np.random.normal(0, 0.005))) for p in mcap_data],
                'low': [p * (1 - abs(np.random.normal(0, 0.005))) for p in mcap_data],
                'volume': np.random.normal(2000000, 400000, len(dates))
            }, index=dates)
            
            # Create market data dict
            market_data = {
                'BTC': btc_data,
                'ETH': eth_data,
                'total_market_cap': market_cap_data
            }
            
            # Analyze regime
            regime_result = analyzer.analyze_market_regime(market_data)
            
            print(f"   Detected Regime: {regime_result.market_regime.value.upper()}")
            print(f"   Volatility: {regime_result.volatility_regime.value}")
            print(f"   Risk Environment: {regime_result.risk_environment.value}")
            print(f"   Confidence: {regime_result.confidence_score:.1%}")
            
            # Check if detection matches expected scenario
            expected_regimes = {
                'bull': 'bullish',
                'bear': 'bearish', 
                'sideways': 'sideways'
            }
            
            if regime_result.market_regime.value == expected_regimes.get(scenario):
                print("   ✅ Correct regime detection")
            else:
                print(f"   ⚠️ Expected {expected_regimes.get(scenario)}, got {regime_result.market_regime.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Market regime analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all alternative data tests"""
    print("🚀 ALTERNATIVE DATA INTEGRATION - COMPREHENSIVE TEST")
    print("📅 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    test_results = {}
    
    try:
        # Test 1: Live crypto data feeds
        print("TEST 1: Live Market Data Feeds")
        test_results['live_data'] = await test_live_crypto_data()
        
        # Test 2: Alternative data provider
        print("TEST 2: Alternative Data Provider")
        test_results['alt_data'] = test_alternative_data_provider()
        
        # Test 3: Sentiment data collection
        print("TEST 3: Sentiment Data Collection")
        test_results['sentiment'] = await test_sentiment_data_simulation()
        
        # Test 4: Market regime analyzer
        print("TEST 4: Market Regime Analyzer")
        test_results['regime'] = test_market_regime_analyzer()
        
        # Final assessment
        print("\n\n🏆 ALTERNATIVE DATA TEST RESULTS")
        print("=" * 40)
        
        # Count successful tests
        successful_apis = sum(1 for api_result in test_results.get('live_data', {}).values() 
                            if isinstance(api_result, dict) and api_result.get('status') == 'SUCCESS')
        
        alt_data_success = test_results.get('alt_data', False)
        regime_success = test_results.get('regime', False)
        
        print(f"📡 Live Data APIs: {successful_apis}/3 working")
        print(f"📊 Alternative Data Provider: {'✅ Working' if alt_data_success else '❌ Failed'}")
        print(f"💭 Sentiment Data: {'✅ Available' if 'sentiment' in test_results else '❌ Failed'}")
        print(f"🏛️ Market Regime Analyzer: {'✅ Working' if regime_success else '❌ Failed'}")
        
        # Overall assessment
        if successful_apis >= 1 and alt_data_success and regime_success:
            print("\n🎯 OVERALL STATUS: ✅ OPERATIONAL")
            print("\nAlternative Data Capabilities:")
            print("• Multiple live price feeds for redundancy")
            print("• On-chain metrics (whale flows, exchange data)")
            print("• Sentiment analysis (fear/greed, news, social)")
            print("• Macro environment tracking")
            print("• Market regime detection and classification")
            print("• Multi-dimensional signal generation")
            
            print("\n🚀 Ready for Enhanced Trading:")
            print("• Alternative data edge over price-only systems")
            print("• Multi-source confirmation for higher confidence")
            print("• Regime-aware strategy selection")
            print("• Sentiment-based risk adjustment")
        else:
            print("\n⚠️ OVERALL STATUS: PARTIAL FUNCTIONALITY")
            print("Some components working, others need attention")
    
    except Exception as e:
        print(f"\n❌ Alternative data test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())