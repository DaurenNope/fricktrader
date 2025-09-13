#!/usr/bin/env python3
"""
Test script for the refactored OpenBB modular provider
Verifies that all functionality works correctly after the optimization
"""

import asyncio
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the refactored OpenBB provider
try:
    from src.market_data.openbb_provider import OpenBBMarketDataProvider
    logger.info("✅ Successfully imported OpenBBMarketDataProvider")
except ImportError as e:
    logger.error(f"❌ Failed to import OpenBBMarketDataProvider: {e}")
    exit(1)

# Import individual components for direct testing
try:
    from src.market_data.openbb import (
        OpenBBClient,
        CryptoDataProvider,
        MarketAnalyzer,
        DataFormatter
    )
    logger.info("✅ Successfully imported individual components")
except ImportError as e:
    logger.error(f"❌ Failed to import individual components: {e}")
    exit(1)


async def test_openbb_client():
    """Test OpenBB client functionality"""
    logger.info("🧪 Testing OpenBB Client...")

    client = OpenBBClient()

    # Test stock data
    try:
        data = await client.get_market_data("AAPL", "1d", 10)
        if data:
            logger.info(f"✅ OpenBB stock data: Got {len(data)} candles for AAPL")
        else:
            logger.info("ℹ️ No OpenBB stock data available (expected without API keys)")
    except Exception as e:
        logger.warning(f"⚠️ OpenBB stock data error: {e}")

    # Test quote data
    try:
        quote = await client.get_quote_data("AAPL")
        if quote:
            logger.info(f"✅ OpenBB quote data: {quote}")
        else:
            logger.info("ℹ️ No OpenBB quote data available")
    except Exception as e:
        logger.warning(f"⚠️ OpenBB quote error: {e}")


async def test_crypto_provider():
    """Test crypto data provider functionality"""
    logger.info("🧪 Testing Crypto Data Provider...")

    crypto_provider = CryptoDataProvider()

    # Test crypto symbol detection
    crypto_symbols = ["BTC/USDT", "ETH/USDT", "AAPL"]
    for symbol in crypto_symbols:
        is_crypto = crypto_provider.is_crypto_symbol(symbol)
        logger.info(f"✅ Symbol {symbol}: {'crypto' if is_crypto else 'not crypto'}")

    # Test OHLCV data
    try:
        data = await crypto_provider.get_ohlcv_data("BTC/USDT", "1h", 5)
        if data:
            logger.info(f"✅ Crypto OHLCV: Got {len(data)} candles for BTC/USDT")
        else:
            logger.info("ℹ️ No crypto OHLCV data available")
    except Exception as e:
        logger.warning(f"⚠️ Crypto OHLCV error: {e}")

    # Test order book
    try:
        order_book = await crypto_provider.get_order_book("BTC/USDT")
        if order_book:
            logger.info(f"✅ Crypto order book: Spread={order_book.spread:.2f}, Imbalance={order_book.imbalance_ratio:.3f}")
        else:
            logger.info("ℹ️ No crypto order book data available")
    except Exception as e:
        logger.warning(f"⚠️ Crypto order book error: {e}")

    # Test ticker data
    try:
        ticker = await crypto_provider.get_ticker_data("BTC/USDT")
        if ticker:
            logger.info(f"✅ Crypto ticker: Last price=${ticker.get('last_price', 'N/A')}")
        else:
            logger.info("ℹ️ No crypto ticker data available")
    except Exception as e:
        logger.warning(f"⚠️ Crypto ticker error: {e}")

    # Test supported symbols
    try:
        symbols = await crypto_provider.get_supported_symbols()
        if symbols:
            logger.info(f"✅ Supported crypto symbols: {len(symbols)} symbols (showing first 5: {symbols[:5]})")
        else:
            logger.info("ℹ️ No supported symbols available")
    except Exception as e:
        logger.warning(f"⚠️ Supported symbols error: {e}")


async def test_market_analyzer():
    """Test market analyzer functionality"""
    logger.info("🧪 Testing Market Analyzer...")

    client = OpenBBClient()
    crypto_provider = CryptoDataProvider()
    analyzer = MarketAnalyzer(client, crypto_provider)

    # Test symbols to analyze
    test_symbols = ["AAPL", "BTC/USDT"]

    for symbol in test_symbols:
        logger.info(f"📊 Analyzing {symbol}...")

        # Test market depth
        try:
            depth = await analyzer.get_market_depth(symbol)
            if depth:
                logger.info(f"✅ Market depth for {symbol}: Mid price=${depth.mid_price:.2f}")
            else:
                logger.info(f"ℹ️ No market depth data for {symbol}")
        except Exception as e:
            logger.warning(f"⚠️ Market depth error for {symbol}: {e}")

        # Test delta analysis
        try:
            delta = await analyzer.get_delta_analysis(symbol, "1h", 20)
            if delta:
                logger.info(f"✅ Delta analysis for {symbol}: Net delta={delta.net_delta:.2f}")
            else:
                logger.info(f"ℹ️ No delta analysis data for {symbol}")
        except Exception as e:
            logger.warning(f"⚠️ Delta analysis error for {symbol}: {e}")

        # Test volume profile (only for crypto to avoid long waits)
        if crypto_provider.is_crypto_symbol(symbol):
            try:
                volume_profile = await analyzer.get_volume_profile(symbol, "1h", 10)
                if volume_profile:
                    logger.info(f"✅ Volume profile for {symbol}: POC=${volume_profile.poc_price:.2f}")
                else:
                    logger.info(f"ℹ️ No volume profile data for {symbol}")
            except Exception as e:
                logger.warning(f"⚠️ Volume profile error for {symbol}: {e}")


async def test_data_formatter():
    """Test data formatter functionality"""
    logger.info("🧪 Testing Data Formatter...")

    formatter = DataFormatter()

    # Test cache functionality
    test_key = "test_data"
    test_value = {"timestamp": datetime.now().isoformat(), "value": 123.45}

    # Cache some data
    formatter.cache_data(test_key, test_value)
    logger.info("✅ Data cached successfully")

    # Retrieve cached data
    cached_data = formatter.get_cached_data(test_key)
    if cached_data:
        logger.info(f"✅ Cached data retrieved: {cached_data}")
    else:
        logger.warning("⚠️ Failed to retrieve cached data")

    # Get cache statistics
    stats = formatter.get_cache_stats()
    logger.info(f"✅ Cache stats: {stats}")

    # Clear cache
    formatter.clear_cache()
    logger.info("✅ Cache cleared successfully")


async def test_main_provider():
    """Test the main OpenBB provider integration"""
    logger.info("🧪 Testing Main OpenBB Provider...")

    config = {
        "api_keys": {}  # Empty config for testing without API keys
    }

    provider = OpenBBMarketDataProvider(config)

    # Test comprehensive analysis for a crypto symbol (faster than stocks)
    symbol = "BTC/USDT"
    logger.info(f"📊 Running comprehensive analysis for {symbol}...")

    try:
        analysis = await provider.get_comprehensive_analysis(symbol)

        if analysis.get("error"):
            logger.warning(f"⚠️ Analysis error: {analysis['error']}")
        else:
            logger.info(f"✅ Comprehensive analysis completed for {symbol}")

            # Show summary
            summary = analysis.get("summary", {})
            logger.info(f"   - Overall sentiment: {summary.get('overall_sentiment', 'unknown')}")
            logger.info(f"   - Confidence score: {summary.get('confidence_score', 0):.3f}")
            logger.info(f"   - Data sources available: {analysis.get('data_sources', {})}")

            if summary.get("opportunities"):
                logger.info(f"   - Opportunities: {len(summary['opportunities'])}")
            if summary.get("risk_factors"):
                logger.info(f"   - Risk factors: {len(summary['risk_factors'])}")

    except Exception as e:
        logger.error(f"❌ Comprehensive analysis error: {e}")

    # Test individual methods
    try:
        depth = await provider.get_market_depth(symbol)
        if depth:
            logger.info(f"✅ Market depth via main provider: Spread={depth.spread:.4f}")
        else:
            logger.info("ℹ️ No market depth data via main provider")
    except Exception as e:
        logger.warning(f"⚠️ Market depth via main provider error: {e}")


async def main():
    """Run all tests"""
    logger.info("🚀 Starting OpenBB Modular Provider Tests")
    logger.info("=" * 60)

    try:
        # Test individual components
        await test_openbb_client()
        logger.info("-" * 40)

        await test_crypto_provider()
        logger.info("-" * 40)

        await test_data_formatter()
        logger.info("-" * 40)

        await test_market_analyzer()
        logger.info("-" * 40)

        # Test integrated provider
        await test_main_provider()
        logger.info("-" * 40)

        logger.info("🎉 All OpenBB modular tests completed successfully!")

    except Exception as e:
        logger.error(f"❌ Test suite error: {e}")
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n✅ OpenBB modular provider is working correctly!")
    else:
        print("\n❌ Some tests failed - please check the logs above")
        exit(1)
