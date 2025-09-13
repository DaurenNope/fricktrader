"""
Sentiment Analysis Module for Crypto Trading
Combines Twitter, Reddit, News, and Fear & Greed Index data
"""

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


@dataclass
class SentimentData:
    """Data class for sentiment analysis results"""

    twitter_sentiment: float = 0.0
    reddit_sentiment: float = 0.0
    news_sentiment: float = 0.0
    fear_greed_index: float = 50.0
    composite_sentiment: float = 0.0
    timestamp: datetime = None
    confidence: float = 0.0


class SentimentAnalyzer:
    """
    Comprehensive sentiment analysis for cryptocurrency markets

    Combines multiple data sources:
    - Twitter/X sentiment analysis
    - Reddit cryptocurrency discussions
    - News sentiment from major crypto outlets
    - Fear & Greed Index
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.cache = {}
        self.cache_duration = 300  # 5 minutes cache

        # API endpoints
        self.fear_greed_url = "https://api.alternative.me/fng/"
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self.twitter_bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

        logger.info("🎭 Sentiment Analyzer initialized")

    def get_fear_greed_index(self) -> float:
        """
        Get Fear & Greed Index from Alternative.me
        Returns: 0-100 scale (0=Extreme Fear, 100=Extreme Greed)
        """
        try:
            response = requests.get(self.fear_greed_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "data" in data and len(data["data"]) > 0:
                    value = int(data["data"][0]["value"])
                    logger.info(f"📊 Fear & Greed Index: {value}")
                    return value
        except Exception as e:
            logger.warning(f"Failed to get Fear & Greed Index: {e}")

        return 50.0  # Neutral fallback

    def get_crypto_news_sentiment(self, pair: str = "BTC") -> float:
        """
        Analyze sentiment from crypto news sources
        Returns: -1.0 to 1.0 (negative to positive sentiment)
        """
        try:
            # Extract base currency from pair
            base_currency = pair.split("/")[0] if "/" in pair else pair

            # Simple keyword-based sentiment analysis
            # In a real implementation, you'd use NLP libraries like VADER or TextBlob

            # Mock sentiment based on current market conditions
            # In production, this would fetch real news and analyze sentiment
            sentiment_score = 0.1  # Slightly positive default

            logger.info(f"📰 News sentiment for {base_currency}: {sentiment_score:.3f}")
            return sentiment_score

        except Exception as e:
            logger.warning(f"Failed to get news sentiment: {e}")
            return 0.0

    def get_social_media_sentiment(self, pair: str = "BTC") -> Tuple[float, float]:
        """
        Get sentiment from Twitter and Reddit
        Returns: (twitter_sentiment, reddit_sentiment) both -1.0 to 1.0
        """
        try:
            base_currency = pair.split("/")[0] if "/" in pair else pair

            # Mock social media sentiment
            # In production, this would use Twitter API v2 and Reddit API

            # Twitter sentiment (slightly positive bias for crypto)
            twitter_sentiment = 0.15

            # Reddit sentiment (more volatile, community-driven)
            reddit_sentiment = 0.05

            logger.info(
                f"🐦 Twitter sentiment for {base_currency}: {twitter_sentiment:.3f}"
            )
            logger.info(
                f"🔴 Reddit sentiment for {base_currency}: {reddit_sentiment:.3f}"
            )

            return twitter_sentiment, reddit_sentiment

        except Exception as e:
            logger.warning(f"Failed to get social media sentiment: {e}")
            return 0.0, 0.0

    def get_sentiment_score(self, pair: str = "BTC/USDT") -> float:
        """
        Get comprehensive sentiment score for a trading pair

        Weighting:
        - Fear & Greed Index: 30%
        - Twitter sentiment: 25%
        - News sentiment: 25%
        - Reddit sentiment: 20%

        Returns: -1.0 to 1.0 (bearish to bullish sentiment)
        """
        cache_key = f"sentiment_{pair}"

        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                return cached_data.composite_sentiment

        try:
            # Get all sentiment components
            fear_greed = self.get_fear_greed_index()
            twitter_sentiment, reddit_sentiment = self.get_social_media_sentiment(pair)
            news_sentiment = self.get_crypto_news_sentiment(pair)

            # Normalize Fear & Greed Index to -1 to 1 scale
            # 0-25: Extreme Fear (-1.0 to -0.5)
            # 25-45: Fear (-0.5 to -0.1)
            # 45-55: Neutral (-0.1 to 0.1)
            # 55-75: Greed (0.1 to 0.5)
            # 75-100: Extreme Greed (0.5 to 1.0)
            if fear_greed <= 25:
                fg_normalized = -1.0 + (fear_greed / 25.0) * 0.5
            elif fear_greed <= 45:
                fg_normalized = -0.5 + ((fear_greed - 25) / 20.0) * 0.4
            elif fear_greed <= 55:
                fg_normalized = -0.1 + ((fear_greed - 45) / 10.0) * 0.2
            elif fear_greed <= 75:
                fg_normalized = 0.1 + ((fear_greed - 55) / 20.0) * 0.4
            else:
                fg_normalized = 0.5 + ((fear_greed - 75) / 25.0) * 0.5

            # Calculate weighted composite sentiment
            composite_sentiment = (
                fg_normalized * 0.30  # Fear & Greed: 30%
                + twitter_sentiment * 0.25  # Twitter: 25%
                + news_sentiment * 0.25  # News: 25%
                + reddit_sentiment * 0.20  # Reddit: 20%
            )

            # Ensure it's within bounds
            composite_sentiment = max(-1.0, min(1.0, composite_sentiment))

            # Create sentiment data object
            sentiment_data = SentimentData(
                twitter_sentiment=twitter_sentiment,
                reddit_sentiment=reddit_sentiment,
                news_sentiment=news_sentiment,
                fear_greed_index=fear_greed,
                composite_sentiment=composite_sentiment,
                timestamp=datetime.now(),
                confidence=0.7,  # Mock confidence score
            )

            # Cache the result
            self.cache[cache_key] = (sentiment_data, time.time())

            logger.info(
                f"🎭 Composite sentiment for {pair}: {composite_sentiment:.3f} (FG:{fear_greed}, T:{twitter_sentiment:.2f}, N:{news_sentiment:.2f}, R:{reddit_sentiment:.2f})"
            )

            return composite_sentiment

        except Exception as e:
            logger.error(f"Error calculating sentiment score: {e}")
            return 0.0  # Neutral fallback

    def get_detailed_sentiment(self, pair: str = "BTC/USDT") -> SentimentData:
        """
        Get detailed sentiment analysis with all components
        """
        cache_key = f"sentiment_detailed_{pair}"

        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                return cached_data

        # Get composite score (this will also cache the detailed data)
        composite_score = self.get_sentiment_score(pair)

        # Return cached detailed data
        if f"sentiment_{pair}" in self.cache:
            return self.cache[f"sentiment_{pair}"][0]

        # Fallback
        return SentimentData(
            composite_sentiment=composite_score, timestamp=datetime.now()
        )
