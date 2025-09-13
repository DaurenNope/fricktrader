"""
Unit tests for sentiment analysis components.

Tests sentiment analyzer functionality, social media
data processing, and sentiment scoring algorithms.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from src.sentiment.sentiment_analyzer import SentimentAnalyzer
from src.social_trading.scraper_framework import ScraperFramework
from src.social_trading.trader_validator import TraderPerformanceValidator


class TestSentimentAnalyzer:
    """Test suite for SentimentAnalyzer class."""

    @pytest.fixture
    def analyzer_config(self):
        """Configuration for sentiment analyzer testing."""
        return {
            "sentiment_sources": ["twitter", "reddit", "news"],
            "update_interval_minutes": 15,
            "sentiment_threshold": 0.1,
            "cache_duration_hours": 1,
            "api_rate_limits": {"twitter": 100, "reddit": 60},
        }

    @pytest.fixture
    def analyzer(self, analyzer_config):
        """Create SentimentAnalyzer instance for testing."""
        return SentimentAnalyzer(analyzer_config)

    @pytest.mark.unit
    def test_analyzer_initialization(self, analyzer_config):
        """Test SentimentAnalyzer initialization."""
        analyzer = SentimentAnalyzer(analyzer_config)

        assert analyzer.config == analyzer_config
        assert analyzer.sentiment_threshold == 0.1
        assert analyzer.update_interval == 15
        assert "twitter" in analyzer.enabled_sources
        assert "reddit" in analyzer.enabled_sources

    @pytest.mark.unit
    def test_analyzer_default_config(self):
        """Test SentimentAnalyzer with default configuration."""
        analyzer = SentimentAnalyzer()

        assert analyzer.sentiment_threshold == 0.0
        assert analyzer.update_interval == 30
        assert len(analyzer.enabled_sources) > 0

    @pytest.mark.unit
    def test_analyze_text_positive_sentiment(self, analyzer):
        """Test analyzing positive sentiment text."""
        positive_texts = [
            "Bitcoin is going to the moon! Amazing rally!",
            "Excellent breakout, bullish momentum strong",
            "Great buying opportunity, very optimistic",
            "Love this crypto project, fantastic team",
        ]

        for text in positive_texts:
            result = analyzer.analyze_text(text)

            assert "sentiment_score" in result
            assert "sentiment_label" in result
            assert "confidence" in result

            # Should be positive sentiment
            assert result["sentiment_score"] > 0.1
            assert result["sentiment_label"] in ["positive", "bullish"]
            assert 0 <= result["confidence"] <= 1

    @pytest.mark.unit
    def test_analyze_text_negative_sentiment(self, analyzer):
        """Test analyzing negative sentiment text."""
        negative_texts = [
            "Bitcoin is crashing hard, panic selling everywhere",
            "Terrible market conditions, very bearish",
            "Awful project, going to zero soon",
            "Hate this volatility, selling everything",
        ]

        for text in negative_texts:
            result = analyzer.analyze_text(text)

            # Should be negative sentiment
            assert result["sentiment_score"] < -0.1
            assert result["sentiment_label"] in ["negative", "bearish"]
            assert 0 <= result["confidence"] <= 1

    @pytest.mark.unit
    def test_analyze_text_neutral_sentiment(self, analyzer):
        """Test analyzing neutral sentiment text."""
        neutral_texts = [
            "Bitcoin price is currently at $45,000",
            "Market data shows sideways movement",
            "Analysis indicates consolidation phase",
            "Technical indicators show mixed signals",
        ]

        for text in neutral_texts:
            result = analyzer.analyze_text(text)

            # Should be neutral sentiment
            assert -0.1 <= result["sentiment_score"] <= 0.1
            assert result["sentiment_label"] == "neutral"

    @pytest.mark.unit
    def test_analyze_batch_texts(self, analyzer):
        """Test batch analysis of multiple texts."""
        texts = [
            "Bitcoin is amazing, going to moon!",
            "Terrible crash, panic selling",
            "Price is at $45,000 currently",
            "Excellent bullish breakout",
            "Market shows neutral conditions",
        ]

        results = analyzer.analyze_batch(texts)

        assert isinstance(results, list)
        assert len(results) == len(texts)

        for i, result in enumerate(results):
            assert "text" in result
            assert "sentiment_score" in result
            assert "sentiment_label" in result
            assert result["text"] == texts[i]

    @pytest.mark.unit
    def test_get_symbol_sentiment_summary(self, analyzer):
        """Test getting sentiment summary for a symbol."""
        symbol = "BTC"

        # Mock sentiment data
        with patch.object(analyzer, "_fetch_recent_sentiment_data") as mock_fetch:
            mock_sentiment_data = [
                {
                    "text": "BTC bullish",
                    "sentiment_score": 0.8,
                    "timestamp": datetime.now(),
                },
                {
                    "text": "Bitcoin bearish",
                    "sentiment_score": -0.6,
                    "timestamp": datetime.now(),
                },
                {
                    "text": "BTC neutral",
                    "sentiment_score": 0.1,
                    "timestamp": datetime.now(),
                },
            ]
            mock_fetch.return_value = mock_sentiment_data

            summary = analyzer.get_symbol_sentiment_summary(symbol)

            assert "symbol" in summary
            assert "overall_sentiment" in summary
            assert "sentiment_score" in summary
            assert "positive_count" in summary
            assert "negative_count" in summary
            assert "neutral_count" in summary
            assert "total_mentions" in summary

            assert summary["symbol"] == symbol
            assert summary["total_mentions"] == 3
            assert summary["positive_count"] == 1
            assert summary["negative_count"] == 1
            assert summary["neutral_count"] == 1

    @pytest.mark.unit
    def test_sentiment_trend_analysis(self, analyzer):
        """Test sentiment trend analysis over time."""
        symbol = "ETH"

        # Mock historical sentiment data
        with patch.object(analyzer, "_fetch_historical_sentiment_data") as mock_fetch:
            base_time = datetime.now() - timedelta(hours=24)
            mock_data = []

            # Create trending sentiment (increasingly positive)
            for i in range(24):
                sentiment_score = -0.5 + (i * 0.05)  # From -0.5 to +0.65
                mock_data.append(
                    {
                        "sentiment_score": sentiment_score,
                        "timestamp": base_time + timedelta(hours=i),
                        "source": "twitter",
                    }
                )

            mock_fetch.return_value = mock_data

            trend = analyzer.get_sentiment_trend(symbol, hours=24)

            assert "symbol" in trend
            assert "trend_direction" in trend
            assert "trend_strength" in trend
            assert "hourly_averages" in trend

            # Should detect upward trend
            assert trend["trend_direction"] == "increasing"
            assert trend["trend_strength"] > 0.3

    @pytest.mark.unit
    def test_sentiment_alerts_generation(self, analyzer):
        """Test generation of sentiment-based alerts."""
        symbol = "BTC"

        # Mock extreme sentiment scenario
        with patch.object(analyzer, "_fetch_recent_sentiment_data") as mock_fetch:
            # Very negative sentiment (potential buying opportunity)
            mock_data = [
                {
                    "sentiment_score": -0.9,
                    "source": "twitter",
                    "timestamp": datetime.now(),
                },
                {
                    "sentiment_score": -0.8,
                    "source": "reddit",
                    "timestamp": datetime.now(),
                },
                {
                    "sentiment_score": -0.7,
                    "source": "news",
                    "timestamp": datetime.now(),
                },
            ]
            mock_fetch.return_value = mock_data

            alerts = analyzer.generate_sentiment_alerts(symbol)

            assert isinstance(alerts, list)
            if len(alerts) > 0:
                alert = alerts[0]
                assert "type" in alert
                assert "severity" in alert
                assert "message" in alert
                assert "symbol" in alert

                # Should generate extreme negative sentiment alert
                assert alert["type"] in ["extreme_negative", "oversold_sentiment"]
                assert alert["symbol"] == symbol

    @pytest.mark.unit
    def test_sentiment_data_validation(self, analyzer):
        """Test validation of sentiment data."""
        # Valid sentiment data
        valid_data = {
            "text": "Bitcoin is performing well",
            "sentiment_score": 0.5,
            "confidence": 0.8,
            "source": "twitter",
            "timestamp": datetime.now(),
        }

        is_valid = analyzer._validate_sentiment_data(valid_data)
        assert is_valid is True

        # Invalid sentiment data
        invalid_data_cases = [
            {"text": "", "sentiment_score": 0.5},  # Empty text
            {"text": "Good", "sentiment_score": 2.0},  # Invalid score range
            {
                "text": "Good",
                "sentiment_score": 0.5,
                "confidence": 1.5,
            },  # Invalid confidence
            {},  # Empty data
        ]

        for invalid_data in invalid_data_cases:
            is_valid = analyzer._validate_sentiment_data(invalid_data)
            assert is_valid is False

    @pytest.mark.unit
    def test_error_handling_invalid_text(self, analyzer):
        """Test error handling with invalid text input."""
        invalid_inputs = [None, "", [], {}, 123]

        for invalid_input in invalid_inputs:
            result = analyzer.analyze_text(invalid_input)

            # Should return neutral sentiment for invalid input
            assert result["sentiment_score"] == 0.0
            assert result["sentiment_label"] == "neutral"
            assert result["confidence"] == 0.0

    @pytest.mark.unit
    @patch("src.sentiment.sentiment_analyzer.logger")
    def test_logging_on_analysis(self, mock_logger, analyzer):
        """Test that sentiment analysis is properly logged."""
        analyzer.analyze_text("Bitcoin is great!")

        # Should log the analysis
        mock_logger.debug.assert_called()


class TestScraperFramework:
    """Test suite for ScraperFramework class."""

    @pytest.fixture
    def scraper_config(self):
        """Configuration for scraper framework testing."""
        return {
            "sources": ["twitter", "reddit"],
            "rate_limits": {
                "twitter": {"requests_per_minute": 30},
                "reddit": {"requests_per_minute": 60},
            },
            "keywords": ["bitcoin", "BTC", "ethereum", "ETH"],
            "max_results_per_source": 100,
        }

    @pytest.fixture
    def scraper(self, scraper_config):
        """Create ScraperFramework instance for testing."""
        return ScraperFramework(scraper_config)

    @pytest.mark.unit
    def test_scraper_initialization(self, scraper_config):
        """Test ScraperFramework initialization."""
        scraper = ScraperFramework(scraper_config)

        assert scraper.config == scraper_config
        assert "twitter" in scraper.enabled_sources
        assert "reddit" in scraper.enabled_sources
        assert scraper.keywords == scraper_config["keywords"]

    @pytest.mark.unit
    @patch("src.social_trading.scraper_framework.tweepy")
    def test_twitter_scraping_success(self, mock_tweepy, scraper):
        """Test successful Twitter data scraping."""
        # Mock Twitter API response
        mock_tweet = Mock()
        mock_tweet.text = "Bitcoin is performing amazingly well today! #BTC"
        mock_tweet.created_at = datetime.now()
        mock_tweet.user.screen_name = "cryptotrader123"
        mock_tweet.retweet_count = 50
        mock_tweet.favorite_count = 200

        mock_api = Mock()
        mock_api.search_tweets.return_value = [mock_tweet]
        mock_tweepy.API.return_value = mock_api

        results = scraper.scrape_twitter("bitcoin", count=10)

        assert isinstance(results, list)
        assert len(results) > 0

        result = results[0]
        assert "text" in result
        assert "source" in result
        assert "timestamp" in result
        assert "metadata" in result

        assert result["source"] == "twitter"
        assert "bitcoin" in result["text"].lower()

    @pytest.mark.unit
    @patch("src.social_trading.scraper_framework.praw")
    def test_reddit_scraping_success(self, mock_praw, scraper):
        """Test successful Reddit data scraping."""
        # Mock Reddit API response
        mock_submission = Mock()
        mock_submission.title = "Bitcoin Analysis: Why BTC is Going Up"
        mock_submission.selftext = "Detailed analysis of Bitcoin market conditions..."
        mock_submission.created_utc = datetime.now().timestamp()
        mock_submission.author.name = "cryptoanalyst"
        mock_submission.score = 150
        mock_submission.num_comments = 25

        mock_subreddit = Mock()
        mock_subreddit.search.return_value = [mock_submission]

        mock_reddit = Mock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_praw.Reddit.return_value = mock_reddit

        results = scraper.scrape_reddit("bitcoin", limit=10)

        assert isinstance(results, list)
        assert len(results) > 0

        result = results[0]
        assert "text" in result
        assert "source" in result
        assert "timestamp" in result

        assert result["source"] == "reddit"

    @pytest.mark.unit
    def test_rate_limiting_enforcement(self, scraper):
        """Test rate limiting functionality."""
        import time

        # Mock rate limit config with very short intervals for testing
        scraper.rate_limits["twitter"]["requests_per_minute"] = 2
        scraper._request_counts = {"twitter": 0}
        scraper._last_request_time = {"twitter": time.time()}

        # First request should go through
        can_request_1 = scraper._can_make_request("twitter")
        assert can_request_1 is True

        scraper._record_request("twitter")
        scraper._record_request("twitter")

        # Should be rate limited now
        can_request_2 = scraper._can_make_request("twitter")
        assert can_request_2 is False

    @pytest.mark.unit
    def test_data_filtering_by_keywords(self, scraper):
        """Test filtering scraped data by keywords."""
        mock_data = [
            {"text": "Bitcoin is amazing today", "source": "twitter"},
            {"text": "Ethereum smart contracts are powerful", "source": "reddit"},
            {
                "text": "Stock market is volatile",
                "source": "twitter",
            },  # Should be filtered out
            {"text": "BTC to the moon", "source": "twitter"},
        ]

        filtered_data = scraper._filter_by_keywords(mock_data)

        assert len(filtered_data) == 3  # Should exclude the stock market post

        for item in filtered_data:
            text_lower = item["text"].lower()
            has_keyword = any(
                keyword.lower() in text_lower for keyword in scraper.keywords
            )
            assert has_keyword is True

    @pytest.mark.unit
    def test_data_deduplication(self, scraper):
        """Test removal of duplicate scraped data."""
        mock_data = [
            {"text": "Bitcoin is great", "source": "twitter", "id": "1"},
            {
                "text": "Bitcoin is great",
                "source": "twitter",
                "id": "2",
            },  # Duplicate text
            {"text": "Ethereum is powerful", "source": "reddit", "id": "3"},
            {
                "text": "Bitcoin is great",
                "source": "reddit",
                "id": "4",
            },  # Duplicate text, different source
        ]

        deduplicated_data = scraper._remove_duplicates(mock_data)

        # Should remove exact text duplicates
        assert len(deduplicated_data) <= len(mock_data)

        # Check that duplicates were removed
        texts_seen = set()
        for item in deduplicated_data:
            assert item["text"] not in texts_seen
            texts_seen.add(item["text"])

    @pytest.mark.unit
    def test_error_handling_api_failure(self, scraper):
        """Test handling of API failures during scraping."""
        with patch.object(scraper, "_make_api_request") as mock_request:
            mock_request.side_effect = Exception("API Error")

            # Should handle API errors gracefully
            results = scraper.scrape_twitter("bitcoin")

            assert isinstance(results, list)
            assert len(results) == 0  # Empty results on API failure


class TestTraderPerformanceValidator:
    """Test suite for TraderPerformanceValidator class."""

    @pytest.fixture
    def validator_config(self):
        """Configuration for trader validator testing."""
        return {
            "min_followers": 1000,
            "min_trading_history_months": 6,
            "min_win_rate": 0.6,
            "min_profit_factor": 1.2,
            "max_drawdown_threshold": 0.3,
            "verification_sources": ["twitter", "tradingview", "broker_statements"],
            "db_path": "test_trader_validation.db",
        }

    @pytest.fixture
    def validator(self, validator_config):
        """Create TraderPerformanceValidator instance for testing."""
        return TraderPerformanceValidator(validator_config)

    @pytest.mark.unit
    def test_validator_initialization(self, validator_config):
        """Test TraderValidator initialization."""
        validator = TraderValidator(validator_config)

        assert validator.config == validator_config
        assert validator.min_followers == 1000
        assert validator.min_win_rate == 0.6

    @pytest.mark.unit
    def test_validate_trader_profile_success(self, validator):
        """Test successful trader profile validation."""
        trader_profile = {
            "username": "professional_trader",
            "followers_count": 5000,
            "trading_history_months": 24,
            "win_rate": 0.72,
            "profit_factor": 2.1,
            "max_drawdown": 0.15,
            "verified_trades": 150,
            "social_proof": {
                "twitter_verified": True,
                "tradingview_reputation": "high",
                "broker_statements": True,
            },
        }

        result = validator.validate_trader_profile(trader_profile)

        assert result["is_valid"] is True
        assert result["confidence_score"] > 0.7
        assert len(result["passed_criteria"]) > 0
        assert len(result["failed_criteria"]) == 0

    @pytest.mark.unit
    def test_validate_trader_profile_insufficient_followers(self, validator):
        """Test trader validation with insufficient followers."""
        trader_profile = {
            "username": "new_trader",
            "followers_count": 500,  # Below minimum
            "trading_history_months": 12,
            "win_rate": 0.8,
            "profit_factor": 2.0,
            "max_drawdown": 0.1,
            "verified_trades": 50,
        }

        result = validator.validate_trader_profile(trader_profile)

        assert result["is_valid"] is False
        assert "min_followers" in result["failed_criteria"]

    @pytest.mark.unit
    def test_validate_trader_profile_poor_performance(self, validator):
        """Test trader validation with poor performance metrics."""
        trader_profile = {
            "username": "poor_performer",
            "followers_count": 2000,
            "trading_history_months": 12,
            "win_rate": 0.3,  # Below minimum
            "profit_factor": 0.8,  # Below minimum
            "max_drawdown": 0.5,  # Above maximum
            "verified_trades": 100,
        }

        result = validator.validate_trader_profile(trader_profile)

        assert result["is_valid"] is False
        assert "min_win_rate" in result["failed_criteria"]
        assert "min_profit_factor" in result["failed_criteria"]
        assert "max_drawdown_threshold" in result["failed_criteria"]

    @pytest.mark.unit
    def test_calculate_trader_score(self, validator):
        """Test trader score calculation."""
        trader_profile = {
            "username": "scored_trader",
            "followers_count": 3000,
            "trading_history_months": 18,
            "win_rate": 0.65,
            "profit_factor": 1.8,
            "max_drawdown": 0.2,
            "verified_trades": 200,
            "social_proof_score": 0.85,
        }

        score = validator.calculate_trader_score(trader_profile)

        assert isinstance(score, float)
        assert 0 <= score <= 1
        assert score > 0.5  # Should be decent score for good metrics

    @pytest.mark.unit
    def test_get_trader_ranking(self, validator):
        """Test trader ranking functionality."""
        traders = [
            {
                "username": "trader1",
                "win_rate": 0.8,
                "profit_factor": 2.5,
                "followers_count": 10000,
            },
            {
                "username": "trader2",
                "win_rate": 0.6,
                "profit_factor": 1.2,
                "followers_count": 2000,
            },
            {
                "username": "trader3",
                "win_rate": 0.9,
                "profit_factor": 3.0,
                "followers_count": 15000,
            },
        ]

        rankings = validator.get_trader_rankings(traders)

        assert isinstance(rankings, list)
        assert len(rankings) == len(traders)

        # Should be sorted by score (highest first)
        for i in range(len(rankings) - 1):
            assert rankings[i]["score"] >= rankings[i + 1]["score"]

        # trader3 should likely be ranked highest due to best metrics
        assert rankings[0]["username"] == "trader3"
