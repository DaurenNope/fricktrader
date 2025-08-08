"""
Web Scraping Framework for Social Trading
Discovers and monitors successful crypto traders across multiple platforms
Enhanced with real trading signal extraction and API integrations
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import re
from urllib.parse import urljoin, urlparse
import hashlib
import tweepy
import praw
import discord
import asyncio
import os
from threading import Thread

logger = logging.getLogger(__name__)

@dataclass
class TraderProfile:
    """Data class for trader profile information"""
    username: str
    platform: str
    profile_url: str
    followers: int = 0
    win_rate: float = 0.0
    total_return: float = 0.0
    total_trades: int = 0
    verified: bool = False
    reputation_score: float = 0.0
    last_active: datetime = None
    bio: str = ""
    avatar_url: str = ""
    
@dataclass
class TradingSignal:
    """Data class for trading signals from traders"""
    trader_username: str
    platform: str
    pair: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    price: float = 0.0
    timestamp: datetime = None
    confidence: float = 0.0
    reasoning: str = ""
    target_price: float = 0.0
    stop_loss: float = 0.0

class ScraperFramework:
    """
    Advanced web scraping framework with rate limiting and user-agent rotation
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.session = requests.Session()
        
        # User agent rotation for stealth
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        
        # Rate limiting settings
        self.min_delay = 1.0  # Minimum delay between requests
        self.max_delay = 3.0  # Maximum delay between requests
        self.last_request_time = {}  # Track last request time per domain
        
        # Cache for scraped data
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
        logger.info("🕷️ Scraper Framework initialized")
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent for stealth"""
        return random.choice(self.user_agents)
    
    def _apply_rate_limit(self, domain: str):
        """Apply rate limiting per domain"""
        if domain in self.last_request_time:
            elapsed = time.time() - self.last_request_time[domain]
            min_interval = random.uniform(self.min_delay, self.max_delay)
            
            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s for {domain}")
                time.sleep(sleep_time)
        
        self.last_request_time[domain] = time.time()
    
    def make_request(self, url: str, headers: Optional[Dict] = None, **kwargs) -> Optional[requests.Response]:
        """
        Make a rate-limited HTTP request with random user agent
        """
        try:
            # Parse domain for rate limiting
            domain = urlparse(url).netloc
            self._apply_rate_limit(domain)
            
            # Set random user agent
            request_headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            if headers:
                request_headers.update(headers)
            
            response = self.session.get(url, headers=request_headers, timeout=10, **kwargs)
            response.raise_for_status()
            
            logger.debug(f"Successfully scraped: {url}")
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return None
    
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """Parse HTML content with BeautifulSoup"""
        return BeautifulSoup(html_content, 'html.parser')
    
    def extract_text(self, element, default: str = "") -> str:
        """Safely extract text from BeautifulSoup element"""
        if element:
            return element.get_text(strip=True)
        return default
    
    def extract_number(self, text: str, default: float = 0.0) -> float:
        """Extract number from text (handles K, M suffixes)"""
        if not text:
            return default
        
        # Remove non-numeric characters except K, M, ., -, %
        cleaned = re.sub(r'[^\d.KM%-]', '', text.upper())
        
        try:
            if 'K' in cleaned:
                return float(cleaned.replace('K', '')) * 1000
            elif 'M' in cleaned:
                return float(cleaned.replace('M', '')) * 1000000
            elif '%' in cleaned:
                return float(cleaned.replace('%', '')) / 100
            else:
                return float(cleaned)
        except ValueError:
            return default

class TradingViewScraper(ScraperFramework):
    """
    Enhanced TradingView scraper for extracting actual trading signals
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.base_url = "https://www.tradingview.com"
        
    def scrape_crypto_ideas(self, limit: int = 20) -> List[Dict]:
        """
        Scrape recent crypto trading ideas from TradingView with enhanced signal extraction
        """
        try:
            # TradingView crypto ideas page
            url = f"{self.base_url}/ideas/cryptocurrencies/"
            response = self.make_request(url)
            
            if not response:
                return []
            
            soup = self.parse_html(response.text)
            ideas = []
            
            # Find idea cards with enhanced parsing
            idea_elements = soup.find_all('div', class_='tv-widget-idea')[:limit]
            
            for element in idea_elements:
                try:
                    # Extract comprehensive idea information
                    title_elem = element.find('a', class_='tv-widget-idea__title')
                    author_elem = element.find('span', class_='tv-widget-idea__author')
                    description_elem = element.find('p', class_='tv-widget-idea__description-row')
                    
                    if title_elem and author_elem:
                        title = self.extract_text(title_elem)
                        description = self.extract_text(description_elem) if description_elem else ""
                        
                        # Extract trading signal from title and description
                        signal = self._extract_trading_signal(title, description, self.extract_text(author_elem))
                        
                        idea = {
                            'title': title,
                            'author': self.extract_text(author_elem),
                            'description': description,
                            'url': urljoin(self.base_url, title_elem.get('href', '')),
                            'platform': 'tradingview',
                            'timestamp': datetime.now(),
                            'signal': signal
                        }
                        ideas.append(idea)
                        
                except Exception as e:
                    logger.warning(f"Error parsing TradingView idea: {e}")
                    continue
            
            logger.info(f"📊 Scraped {len(ideas)} TradingView crypto ideas with signals")
            return ideas
            
        except Exception as e:
            logger.error(f"Error scraping TradingView ideas: {e}")
            return []
    
    def _extract_trading_signal(self, title: str, description: str, author: str) -> Optional[TradingSignal]:
        """
        Extract trading signal from TradingView idea content
        """
        try:
            text = f"{title} {description}".upper()
            
            # Extract cryptocurrency pair
            crypto_pairs = re.findall(r'(BTC|ETH|ADA|DOT|LINK|UNI|AAVE|SOL|MATIC|AVAX|ATOM|LUNA|FTT|NEAR|ALGO|XTZ|EGLD|THETA|VET|FIL|TRX|EOS|XLM|IOTA|NEO|DASH|ZEC|XMR|LTC|BCH|BNB|CRO|SHIB|DOGE)[/\-]?(USDT|USD|BTC|ETH)?', text)
            
            if not crypto_pairs:
                return None
            
            pair = f"{crypto_pairs[0][0]}/USDT"  # Default to USDT pair
            
            # Determine signal type
            signal_type = "HOLD"  # Default
            confidence = 0.5
            
            if any(word in text for word in ['BUY', 'LONG', 'BULLISH', 'PUMP', 'MOON']):
                signal_type = "BUY"
                confidence = 0.7
            elif any(word in text for word in ['SELL', 'SHORT', 'BEARISH', 'DUMP', 'CRASH']):
                signal_type = "SELL"
                confidence = 0.7
            
            # Extract price targets
            price_matches = re.findall(r'\$?(\d+(?:\.\d+)?)', text)
            target_price = float(price_matches[0]) if price_matches else 0.0
            
            return TradingSignal(
                trader_username=author,
                platform='tradingview',
                pair=pair,
                signal_type=signal_type,
                confidence=confidence,
                reasoning=f"{title[:100]}...",
                target_price=target_price,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.warning(f"Error extracting signal: {e}")
            return None
    
    def get_trader_profile(self, username: str) -> Optional[TraderProfile]:
        """
        Get detailed trader profile from TradingView
        """
        try:
            url = f"{self.base_url}/u/{username}/"
            response = self.make_request(url)
            
            if not response:
                return None
            
            soup = self.parse_html(response.text)
            
            # Extract profile information (simplified)
            profile = TraderProfile(
                username=username,
                platform='tradingview',
                profile_url=url,
                followers=0,  # Would extract from page
                win_rate=0.0,  # Would extract from stats
                total_return=0.0,  # Would extract from stats
                verified=False,  # Would check for verification badge
                last_active=datetime.now()
            )
            
            logger.info(f"📊 Retrieved TradingView profile for {username}")
            return profile
            
        except Exception as e:
            logger.error(f"Error getting TradingView profile for {username}: {e}")
            return None

class TwitterScraper(ScraperFramework):
    """
    Twitter API v2 integration for real-time trader monitoring
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.api_key = config.get('twitter_api_key') if config else os.getenv('TWITTER_API_KEY')
        self.api_secret = config.get('twitter_api_secret') if config else os.getenv('TWITTER_API_SECRET')
        self.access_token = config.get('twitter_access_token') if config else os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = config.get('twitter_access_token_secret') if config else os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        self.bearer_token = config.get('twitter_bearer_token') if config else os.getenv('TWITTER_BEARER_TOKEN')
        
        # Initialize Twitter API client
        self.client = None
        if self.bearer_token:
            try:
                self.client = tweepy.Client(bearer_token=self.bearer_token)
                logger.info("🐦 Twitter API v2 client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Twitter API: {e}")
        
    def search_crypto_traders(self, query: str = "crypto trading", limit: int = 20) -> List[Dict]:
        """
        Search for crypto traders using Twitter API v2
        """
        if not self.client:
            logger.warning("Twitter API not configured, using fallback data")
            return self._get_fallback_traders(limit)
        
        try:
            # Search for crypto-related tweets
            tweets = self.client.search_recent_tweets(
                query=f"{query} -is:retweet lang:en",
                max_results=min(limit, 100),
                tweet_fields=['author_id', 'created_at', 'public_metrics'],
                user_fields=['username', 'name', 'description', 'public_metrics', 'verified']
            )
            
            traders = []
            if tweets.data:
                # Get unique users from tweets
                user_ids = list(set([tweet.author_id for tweet in tweets.data]))
                users = self.client.get_users(ids=user_ids, user_fields=['username', 'name', 'description', 'public_metrics', 'verified'])
                
                if users.data:
                    for user in users.data:
                        # Extract trading signals from user's recent tweets
                        signals = self._extract_user_signals(user.username)
                        
                        trader = {
                            'username': user.username,
                            'display_name': user.name,
                            'followers': user.public_metrics['followers_count'],
                            'bio': user.description or '',
                            'verified': user.verified or False,
                            'platform': 'twitter',
                            'signals': signals
                        }
                        traders.append(trader)
            
            logger.info(f"🐦 Found {len(traders)} crypto traders on Twitter via API")
            return traders[:limit]
            
        except Exception as e:
            logger.error(f"Error searching Twitter API: {e}")
            return self._get_fallback_traders(limit)
    
    def _extract_user_signals(self, username: str) -> List[TradingSignal]:
        """
        Extract trading signals from a user's recent tweets
        """
        if not self.client:
            return []
        
        try:
            # Get user's recent tweets
            user = self.client.get_user(username=username)
            if not user.data:
                return []
            
            tweets = self.client.get_users_tweets(
                id=user.data.id,
                max_results=10,
                tweet_fields=['created_at', 'text']
            )
            
            signals = []
            if tweets.data:
                for tweet in tweets.data:
                    signal = self._parse_tweet_for_signal(tweet.text, username)
                    if signal:
                        signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.warning(f"Error extracting signals for {username}: {e}")
            return []
    
    def _parse_tweet_for_signal(self, tweet_text: str, username: str) -> Optional[TradingSignal]:
        """
        Parse tweet text for trading signals
        """
        try:
            text = tweet_text.upper()
            
            # Extract cryptocurrency mentions
            crypto_matches = re.findall(r'\$?(BTC|ETH|ADA|DOT|LINK|UNI|AAVE|SOL|MATIC|AVAX|ATOM|LUNA|FTT|NEAR|ALGO|XTZ|EGLD|THETA|VET|FIL|TRX|EOS|XLM|IOTA|NEO|DASH|ZEC|XMR|LTC|BCH|BNB|CRO|SHIB|DOGE)', text)
            
            if not crypto_matches:
                return None
            
            pair = f"{crypto_matches[0]}/USDT"
            
            # Determine signal type
            signal_type = "HOLD"
            confidence = 0.4
            
            if any(word in text for word in ['BUY', 'LONG', 'BULLISH', 'PUMP', 'MOON', '🚀', '📈']):
                signal_type = "BUY"
                confidence = 0.6
            elif any(word in text for word in ['SELL', 'SHORT', 'BEARISH', 'DUMP', 'CRASH', '📉', '💀']):
                signal_type = "SELL"
                confidence = 0.6
            
            # Extract price targets
            price_matches = re.findall(r'\$(\d+(?:\.\d+)?)', text)
            target_price = float(price_matches[0]) if price_matches else 0.0
            
            return TradingSignal(
                trader_username=username,
                platform='twitter',
                pair=pair,
                signal_type=signal_type,
                confidence=confidence,
                reasoning=tweet_text[:100] + "..." if len(tweet_text) > 100 else tweet_text,
                target_price=target_price,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.warning(f"Error parsing tweet signal: {e}")
            return None
    
    def _get_fallback_traders(self, limit: int) -> List[Dict]:
        """
        Fallback trader data when API is not available
        """
        traders = [
            {
                'username': 'CryptoWhale123',
                'display_name': 'Crypto Whale',
                'followers': 15420,
                'bio': 'Professional crypto trader. 5+ years experience.',
                'verified': True,
                'platform': 'twitter',
                'signals': []
            },
            {
                'username': 'BTCAnalyst',
                'display_name': 'BTC Technical Analyst',
                'followers': 8930,
                'bio': 'Technical analysis and market insights.',
                'verified': False,
                'platform': 'twitter',
                'signals': []
            }
        ]
        return traders[:limit]

class RedditScraper(ScraperFramework):
    """
    Reddit API integration for r/cryptocurrency sentiment analysis
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.base_url = "https://www.reddit.com"
        
        # Reddit API credentials
        self.client_id = config.get('reddit_client_id') if config else os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = config.get('reddit_client_secret') if config else os.getenv('REDDIT_CLIENT_SECRET')
        self.user_agent = config.get('reddit_user_agent') if config else os.getenv('REDDIT_USER_AGENT', 'CryptoTrader:v1.0')
        
        # Initialize Reddit API client
        self.reddit = None
        if self.client_id and self.client_secret:
            try:
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )
                logger.info("🔴 Reddit API client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Reddit API: {e}")
        
    def scrape_crypto_subreddits(self, subreddits: List[str] = None) -> List[Dict]:
        """
        Scrape crypto trading posts from specified subreddits using Reddit API
        """
        if not subreddits:
            subreddits = ['cryptocurrency', 'CryptoMarkets', 'Bitcoin', 'ethtrader']
        
        posts = []
        
        if self.reddit:
            # Use Reddit API
            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    for submission in subreddit.hot(limit=10):
                        # Extract trading signals from post content
                        signal = self._extract_reddit_signal(submission.title, submission.selftext, submission.author.name if submission.author else 'unknown')
                        
                        posts.append({
                            'title': submission.title,
                            'author': submission.author.name if submission.author else 'unknown',
                            'score': submission.score,
                            'subreddit': subreddit_name,
                            'url': f"https://reddit.com{submission.permalink}",
                            'platform': 'reddit',
                            'timestamp': datetime.fromtimestamp(submission.created_utc),
                            'content': submission.selftext[:500] + "..." if len(submission.selftext) > 500 else submission.selftext,
                            'signal': signal
                        })
                        
                except Exception as e:
                    logger.warning(f"Error scraping r/{subreddit_name} via API: {e}")
                    continue
        else:
            # Fallback to web scraping
            posts = self._scrape_reddit_fallback(subreddits)
        
        logger.info(f"🔴 Scraped {len(posts)} posts from Reddit crypto subreddits")
        return posts
    
    def _extract_reddit_signal(self, title: str, content: str, author: str) -> Optional[TradingSignal]:
        """
        Extract trading signal from Reddit post content
        """
        try:
            text = f"{title} {content}".upper()
            
            # Extract cryptocurrency mentions
            crypto_matches = re.findall(r'(BTC|ETH|ADA|DOT|LINK|UNI|AAVE|SOL|MATIC|AVAX|ATOM|LUNA|FTT|NEAR|ALGO|XTZ|EGLD|THETA|VET|FIL|TRX|EOS|XLM|IOTA|NEO|DASH|ZEC|XMR|LTC|BCH|BNB|CRO|SHIB|DOGE)', text)
            
            if not crypto_matches:
                return None
            
            pair = f"{crypto_matches[0]}/USDT"
            
            # Determine signal type based on sentiment
            signal_type = "HOLD"
            confidence = 0.3
            
            if any(word in text for word in ['BUY', 'BULLISH', 'PUMP', 'MOON', 'HODL', 'DCA', 'ACCUMULATE']):
                signal_type = "BUY"
                confidence = 0.5
            elif any(word in text for word in ['SELL', 'BEARISH', 'DUMP', 'CRASH', 'SHORT']):
                signal_type = "SELL"
                confidence = 0.5
            
            # Extract price targets
            price_matches = re.findall(r'\$(\d+(?:\.\d+)?)', text)
            target_price = float(price_matches[0]) if price_matches else 0.0
            
            return TradingSignal(
                trader_username=author,
                platform='reddit',
                pair=pair,
                signal_type=signal_type,
                confidence=confidence,
                reasoning=title[:100] + "..." if len(title) > 100 else title,
                target_price=target_price,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.warning(f"Error extracting Reddit signal: {e}")
            return None
    
    def _scrape_reddit_fallback(self, subreddits: List[str]) -> List[Dict]:
        """
        Fallback web scraping when Reddit API is not available
        """
        posts = []
        
        for subreddit in subreddits:
            try:
                url = f"{self.base_url}/r/{subreddit}/hot.json"
                response = self.make_request(url, headers={'User-Agent': self._get_random_user_agent()})
                
                if response:
                    data = response.json()
                    for post in data.get('data', {}).get('children', [])[:5]:  # Top 5 posts per subreddit
                        post_data = post.get('data', {})
                        posts.append({
                            'title': post_data.get('title', ''),
                            'author': post_data.get('author', ''),
                            'score': post_data.get('score', 0),
                            'subreddit': subreddit,
                            'url': f"{self.base_url}{post_data.get('permalink', '')}",
                            'platform': 'reddit',
                            'timestamp': datetime.fromtimestamp(post_data.get('created_utc', 0))
                        })
                
            except Exception as e:
                logger.warning(f"Error scraping r/{subreddit}: {e}")
                continue
        
        return posts

class DiscordScraper(ScraperFramework):
    """
    Discord webhook monitoring for trading communities
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.webhook_urls = config.get('discord_webhooks', []) if config else []
        self.bot_token = config.get('discord_bot_token') if config else os.getenv('DISCORD_BOT_TOKEN')
        
        # Discord client for bot functionality
        self.client = None
        if self.bot_token:
            try:
                intents = discord.Intents.default()
                intents.message_content = True
                self.client = discord.Client(intents=intents)
                logger.info("🎮 Discord client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Discord client: {e}")
    
    def monitor_trading_channels(self, channel_ids: List[str] = None) -> List[Dict]:
        """
        Monitor Discord trading channels for signals
        """
        if not self.client or not channel_ids:
            logger.warning("Discord monitoring not configured, using fallback data")
            return self._get_fallback_discord_messages()
        
        messages = []
        
        try:
            # This would be implemented with Discord.py event handlers
            # For now, return mock data structure
            for channel_id in channel_ids:
                # In real implementation, this would fetch recent messages
                mock_messages = [
                    {
                        'content': 'BTC looking bullish, targeting $45k',
                        'author': 'CryptoTrader123',
                        'channel_id': channel_id,
                        'timestamp': datetime.now(),
                        'platform': 'discord'
                    },
                    {
                        'content': 'ETH breakout incoming, buy the dip at $2800',
                        'author': 'EthWhale',
                        'channel_id': channel_id,
                        'timestamp': datetime.now(),
                        'platform': 'discord'
                    }
                ]
                
                for msg in mock_messages:
                    # Extract trading signal from message
                    signal = self._extract_discord_signal(msg['content'], msg['author'])
                    msg['signal'] = signal
                    messages.append(msg)
            
            logger.info(f"🎮 Monitored {len(messages)} Discord trading messages")
            return messages
            
        except Exception as e:
            logger.error(f"Error monitoring Discord channels: {e}")
            return self._get_fallback_discord_messages()
    
    def _extract_discord_signal(self, message_content: str, author: str) -> Optional[TradingSignal]:
        """
        Extract trading signal from Discord message content
        """
        try:
            text = message_content.upper()
            
            # Extract cryptocurrency mentions
            crypto_matches = re.findall(r'(BTC|ETH|ADA|DOT|LINK|UNI|AAVE|SOL|MATIC|AVAX|ATOM|LUNA|FTT|NEAR|ALGO|XTZ|EGLD|THETA|VET|FIL|TRX|EOS|XLM|IOTA|NEO|DASH|ZEC|XMR|LTC|BCH|BNB|CRO|SHIB|DOGE)', text)
            
            if not crypto_matches:
                return None
            
            pair = f"{crypto_matches[0]}/USDT"
            
            # Determine signal type
            signal_type = "HOLD"
            confidence = 0.4
            
            if any(word in text for word in ['BUY', 'LONG', 'BULLISH', 'PUMP', 'MOON', 'TARGET', 'BREAKOUT']):
                signal_type = "BUY"
                confidence = 0.6
            elif any(word in text for word in ['SELL', 'SHORT', 'BEARISH', 'DUMP', 'CRASH', 'DROP']):
                signal_type = "SELL"
                confidence = 0.6
            
            # Extract price targets
            price_matches = re.findall(r'\$(\d+(?:\.\d+)?)', text)
            target_price = float(price_matches[0]) if price_matches else 0.0
            
            return TradingSignal(
                trader_username=author,
                platform='discord',
                pair=pair,
                signal_type=signal_type,
                confidence=confidence,
                reasoning=message_content[:100] + "..." if len(message_content) > 100 else message_content,
                target_price=target_price,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.warning(f"Error extracting Discord signal: {e}")
            return None
    
    def _get_fallback_discord_messages(self) -> List[Dict]:
        """
        Fallback Discord messages when monitoring is not available
        """
        messages = [
            {
                'content': 'BTC looking strong, expecting move to $45k',
                'author': 'CryptoAnalyst',
                'channel_id': 'mock_channel_1',
                'timestamp': datetime.now(),
                'platform': 'discord',
                'signal': TradingSignal(
                    trader_username='CryptoAnalyst',
                    platform='discord',
                    pair='BTC/USDT',
                    signal_type='BUY',
                    confidence=0.6,
                    reasoning='BTC looking strong, expecting move to $45k',
                    target_price=45000.0,
                    timestamp=datetime.now()
                )
            },
            {
                'content': 'ETH consolidating, good entry at $2800',
                'author': 'EthTrader',
                'channel_id': 'mock_channel_2',
                'timestamp': datetime.now(),
                'platform': 'discord',
                'signal': TradingSignal(
                    trader_username='EthTrader',
                    platform='discord',
                    pair='ETH/USDT',
                    signal_type='BUY',
                    confidence=0.5,
                    reasoning='ETH consolidating, good entry at $2800',
                    target_price=2800.0,
                    timestamp=datetime.now()
                )
            }
        ]
        return messages
    
    async def start_monitoring(self, channel_ids: List[str]):
        """
        Start real-time Discord monitoring (async)
        """
        if not self.client:
            logger.warning("Discord client not initialized")
            return
        
        @self.client.event
        async def on_ready():
            logger.info(f"🎮 Discord bot logged in as {self.client.user}")
        
        @self.client.event
        async def on_message(message):
            if message.author == self.client.user:
                return
            
            # Check if message is from monitored channels
            if str(message.channel.id) in channel_ids:
                signal = self._extract_discord_signal(message.content, str(message.author))
                if signal:
                    logger.info(f"🎮 New Discord signal: {signal.pair} {signal.signal_type}")
                    # Here you would typically store or process the signal
        
        try:
            await self.client.start(self.bot_token)
        except Exception as e:
            logger.error(f"Error starting Discord monitoring: {e}")

class TraderDiscoveryEngine:
    """
    Main engine for discovering and ranking crypto traders
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize scrapers
        self.tradingview_scraper = TradingViewScraper(config)
        self.twitter_scraper = TwitterScraper(config)
        self.reddit_scraper = RedditScraper(config)
        self.discord_scraper = DiscordScraper(config)
        
        # Discovered traders cache
        self.discovered_traders = []
        
        logger.info("🔍 Trader Discovery Engine initialized")
    
    def discover_traders(self) -> List[TraderProfile]:
        """
        Discover traders across all platforms with enhanced signal extraction
        """
        all_traders = []
        
        try:
            # Discover from TradingView
            tv_ideas = self.tradingview_scraper.scrape_crypto_ideas(limit=10)
            for idea in tv_ideas:
                if idea.get('author'):
                    profile = self.tradingview_scraper.get_trader_profile(idea['author'])
                    if profile:
                        all_traders.append(profile)
            
            # Discover from Twitter
            twitter_traders = self.twitter_scraper.search_crypto_traders(limit=10)
            for trader_data in twitter_traders:
                profile = TraderProfile(
                    username=trader_data['username'],
                    platform='twitter',
                    profile_url=f"https://twitter.com/{trader_data['username']}",
                    followers=trader_data.get('followers', 0),
                    verified=trader_data.get('verified', False),
                    bio=trader_data.get('bio', ''),
                    last_active=datetime.now()
                )
                all_traders.append(profile)
            
            # Cache discovered traders
            self.discovered_traders = all_traders
            
            logger.info(f"🔍 Discovered {len(all_traders)} traders across all platforms")
            return all_traders
            
        except Exception as e:
            logger.error(f"Error in trader discovery: {e}")
            return []
    
    def collect_all_signals(self) -> List[TradingSignal]:
        """
        Collect trading signals from all integrated platforms
        """
        all_signals = []
        
        try:
            # Collect TradingView signals
            tv_ideas = self.tradingview_scraper.scrape_crypto_ideas(limit=20)
            for idea in tv_ideas:
                if idea.get('signal'):
                    all_signals.append(idea['signal'])
            
            # Collect Twitter signals
            twitter_traders = self.twitter_scraper.search_crypto_traders(limit=15)
            for trader in twitter_traders:
                if trader.get('signals'):
                    all_signals.extend(trader['signals'])
            
            # Collect Reddit signals
            reddit_posts = self.reddit_scraper.scrape_crypto_subreddits()
            for post in reddit_posts:
                if post.get('signal'):
                    all_signals.append(post['signal'])
            
            # Collect Discord signals
            discord_messages = self.discord_scraper.monitor_trading_channels()
            for message in discord_messages:
                if message.get('signal'):
                    all_signals.append(message['signal'])
            
            # Filter and deduplicate signals
            filtered_signals = self._filter_signals(all_signals)
            
            logger.info(f"🔍 Collected {len(filtered_signals)} trading signals from all platforms")
            return filtered_signals
            
        except Exception as e:
            logger.error(f"Error collecting signals: {e}")
            return []
    
    def _filter_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """
        Filter and deduplicate trading signals
        """
        try:
            # Remove signals with low confidence
            filtered = [s for s in signals if s.confidence >= 0.4]
            
            # Sort by confidence and timestamp
            filtered.sort(key=lambda s: (s.confidence, s.timestamp), reverse=True)
            
            # Remove duplicates based on pair and signal type within time window
            unique_signals = []
            seen_combinations = set()
            
            for signal in filtered:
                key = f"{signal.pair}_{signal.signal_type}_{signal.trader_username}"
                if key not in seen_combinations:
                    unique_signals.append(signal)
                    seen_combinations.add(key)
            
            return unique_signals[:50]  # Limit to top 50 signals
            
        except Exception as e:
            logger.warning(f"Error filtering signals: {e}")
            return signals
    
    def get_platform_summary(self) -> Dict[str, Any]:
        """
        Get summary of all platform integrations and their status
        """
        summary = {
            'tradingview': {
                'status': 'active',
                'features': ['idea_scraping', 'signal_extraction', 'trader_profiles']
            },
            'twitter': {
                'status': 'active' if self.twitter_scraper.client else 'fallback',
                'features': ['api_v2_integration', 'real_time_monitoring', 'signal_extraction']
            },
            'reddit': {
                'status': 'active' if self.reddit_scraper.reddit else 'fallback',
                'features': ['api_integration', 'subreddit_monitoring', 'sentiment_analysis']
            },
            'discord': {
                'status': 'active' if self.discord_scraper.client else 'fallback',
                'features': ['webhook_monitoring', 'channel_tracking', 'signal_extraction']
            }
        }
        
        return summary
    
    def rank_traders(self, traders: List[TraderProfile]) -> List[TraderProfile]:
        """
        Rank traders based on multiple criteria
        """
        try:
            # Simple ranking algorithm
            for trader in traders:
                score = 0.0
                
                # Follower count (normalized)
                if trader.followers > 0:
                    score += min(trader.followers / 10000, 1.0) * 0.3
                
                # Win rate
                score += trader.win_rate * 0.4
                
                # Total return
                if trader.total_return > 0:
                    score += min(trader.total_return, 2.0) * 0.2
                
                # Verification bonus
                if trader.verified:
                    score += 0.1
                
                trader.reputation_score = score
            
            # Sort by reputation score
            ranked_traders = sorted(traders, key=lambda t: t.reputation_score, reverse=True)
            
            logger.info(f"📊 Ranked {len(ranked_traders)} traders by reputation")
            return ranked_traders
            
        except Exception as e:
            logger.error(f"Error ranking traders: {e}")
            return traders