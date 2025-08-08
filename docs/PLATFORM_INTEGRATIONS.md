# Platform Integrations Guide

This guide explains how to configure and use the enhanced social trading platform integrations.

## Overview

The system now supports real-time monitoring and signal extraction from:

- **TradingView**: Enhanced scraping with actual trading signal extraction
- **Twitter API v2**: Real-time trader monitoring and tweet analysis
- **Reddit API**: Subreddit monitoring for r/cryptocurrency sentiment
- **Discord**: Webhook monitoring for trading communities

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Twitter API v2 Configuration
TWITTER_BEARER_TOKEN=your_bearer_token_here
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here

# Reddit API Configuration
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=CryptoTrader:v1.0

# Discord Bot Configuration
DISCORD_BOT_TOKEN=your_bot_token_here
```

### API Setup Instructions

#### Twitter API v2
1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new app and generate API keys
3. Enable API v2 access
4. Add the credentials to your `.env` file

#### Reddit API
1. Go to [Reddit Apps](https://www.reddit.com/prefs/apps)
2. Create a new application (script type)
3. Note the client ID and secret
4. Add the credentials to your `.env` file

#### Discord Bot
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and bot
3. Copy the bot token
4. Invite the bot to your trading servers with message reading permissions

## Usage Examples

### Basic Signal Collection

```python
from src.social_trading.scraper_framework import TraderDiscoveryEngine

# Initialize the engine
engine = TraderDiscoveryEngine()

# Collect signals from all platforms
signals = engine.collect_all_signals()

# Display top signals
for signal in signals[:5]:
    print(f"{signal.pair} {signal.signal_type} - Confidence: {signal.confidence:.2f}")
    print(f"Platform: {signal.platform} | Trader: {signal.trader_username}")
    print(f"Reasoning: {signal.reasoning}")
    print()
```

### Platform-Specific Usage

```python
from src.social_trading.scraper_framework import (
    TradingViewScraper,
    TwitterScraper,
    RedditScraper,
    DiscordScraper
)

# TradingView enhanced scraping
tv_scraper = TradingViewScraper()
ideas = tv_scraper.scrape_crypto_ideas(limit=10)

# Twitter API v2 integration
twitter_scraper = TwitterScraper()
traders = twitter_scraper.search_crypto_traders(query="bitcoin trading", limit=20)

# Reddit API integration
reddit_scraper = RedditScraper()
posts = reddit_scraper.scrape_crypto_subreddits(['cryptocurrency', 'Bitcoin'])

# Discord monitoring
discord_scraper = DiscordScraper()
messages = discord_scraper.monitor_trading_channels(['channel_id_1', 'channel_id_2'])
```

## Features

### Enhanced TradingView Integration
- ✅ Real trading signal extraction from ideas
- ✅ Cryptocurrency pair detection
- ✅ Signal type classification (BUY/SELL/HOLD)
- ✅ Confidence scoring
- ✅ Price target extraction

### Twitter API v2 Integration
- ✅ Real-time trader search and monitoring
- ✅ Tweet analysis for trading signals
- ✅ User profile and follower data
- ✅ Verification status tracking
- ✅ Fallback to mock data when API unavailable

### Reddit API Integration
- ✅ Multi-subreddit monitoring
- ✅ Sentiment analysis for trading signals
- ✅ Post scoring and author tracking
- ✅ Real-time data via PRAW library
- ✅ Fallback to web scraping when API unavailable

### Discord Webhook Monitoring
- ✅ Real-time channel monitoring
- ✅ Message analysis for trading signals
- ✅ Multi-channel support
- ✅ Async monitoring capabilities
- ✅ Mock data for testing without bot setup

## Signal Quality and Filtering

The system includes intelligent signal filtering:

- **Confidence Threshold**: Only signals with confidence ≥ 0.4 are included
- **Deduplication**: Removes duplicate signals from same trader/pair/type
- **Time-based Filtering**: Prioritizes recent signals
- **Platform Weighting**: Different confidence levels per platform
- **Volume Limiting**: Maximum 50 signals to prevent information overload

## Testing

Run the integration tests to verify setup:

```bash
python test_platform_integrations.py
```

This will test all platform integrations and show their status.

## Troubleshooting

### Common Issues

1. **API Rate Limits**: The system includes built-in rate limiting and fallback mechanisms
2. **Missing Dependencies**: Run `pip install -r requirements.txt` to install all required packages
3. **API Key Issues**: Verify your API keys are correctly set in the `.env` file
4. **Network Issues**: The system gracefully handles network failures with fallback data

### Fallback Behavior

When APIs are not configured or unavailable:
- **Twitter**: Uses mock trader data
- **Reddit**: Falls back to web scraping
- **Discord**: Uses mock message data
- **TradingView**: Continues with basic web scraping

## Integration with Trading System

The collected signals can be integrated with your trading strategies:

```python
# Example integration with trading strategy
def process_social_signals():
    engine = TraderDiscoveryEngine()
    signals = engine.collect_all_signals()
    
    # Filter high-confidence signals
    high_confidence = [s for s in signals if s.confidence >= 0.7]
    
    # Group by cryptocurrency
    by_crypto = {}
    for signal in high_confidence:
        crypto = signal.pair.split('/')[0]
        if crypto not in by_crypto:
            by_crypto[crypto] = []
        by_crypto[crypto].append(signal)
    
    # Generate trading recommendations
    for crypto, crypto_signals in by_crypto.items():
        buy_signals = [s for s in crypto_signals if s.signal_type == 'BUY']
        sell_signals = [s for s in crypto_signals if s.signal_type == 'SELL']
        
        if len(buy_signals) > len(sell_signals):
            print(f"📈 {crypto}: Strong BUY sentiment ({len(buy_signals)} signals)")
        elif len(sell_signals) > len(buy_signals):
            print(f"📉 {crypto}: Strong SELL sentiment ({len(sell_signals)} signals)")
```

## Next Steps

1. Configure API keys for full functionality
2. Set up Discord bot for real-time monitoring
3. Integrate signals with your trading strategy
4. Implement signal persistence and historical tracking
5. Add more sophisticated sentiment analysis
6. Create automated trading rules based on social signals