#!/usr/bin/env python3
"""
Persistent caching system for market data to reduce API dependency
"""
import sqlite3
import json
import time
from datetime import datetime
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class PersistentMarketCache:
    """SQLite-based persistent cache for market data"""
    
    def __init__(self, db_path: str = "data/market_cache.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize the database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_prices (
                symbol TEXT PRIMARY KEY,
                price REAL,
                change_24h REAL,
                change_24h_percent REAL,
                volume_24h REAL,
                high_24h REAL,
                low_24h REAL,
                source TEXT,
                timestamp TEXT,
                updated_at INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_data (
                symbol TEXT,
                timeframe TEXT,
                data TEXT,
                updated_at INTEGER,
                PRIMARY KEY (symbol, timeframe)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def cache_prices(self, prices_data: Dict) -> None:
        """Store price data in cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = int(time.time())
        
        for symbol, data in prices_data.items():
            cursor.execute('''
                INSERT OR REPLACE INTO market_prices 
                (symbol, price, change_24h, change_24h_percent, volume_24h, 
                 high_24h, low_24h, source, timestamp, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                data.get('price', 0),
                data.get('change_24h', 0),
                data.get('change_24h_percent', 0),
                data.get('volume_24h', 0),
                data.get('high_24h', 0),
                data.get('low_24h', 0),
                data.get('source', 'Unknown'),
                data.get('timestamp', datetime.now().isoformat()),
                now
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Cached {len(prices_data)} prices to database")
    
    def get_cached_prices(self, max_age_seconds: int = 300) -> Dict:
        """Get cached price data if not too old"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = int(time.time()) - max_age_seconds
        
        cursor.execute('''
            SELECT symbol, price, change_24h, change_24h_percent, volume_24h,
                   high_24h, low_24h, source, timestamp, updated_at
            FROM market_prices
            WHERE updated_at > ?
        ''', (cutoff_time,))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return {}
        
        prices = {}
        for row in results:
            symbol = row[0]
            prices[symbol] = {
                'price': row[1],
                'change_24h': row[2],
                'change_24h_percent': row[3],
                'volume_24h': row[4],
                'high_24h': row[5],
                'low_24h': row[6],
                'source': f"{row[7]} (Cached)",
                'timestamp': row[8],
                'cache_age': int(time.time()) - row[9]
            }
        
        logger.info(f"📦 Retrieved {len(prices)} cached prices")
        return prices
    
    def cache_historical_data(self, symbol: str, timeframe: str, data: list) -> None:
        """Cache historical/chart data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO historical_data 
            (symbol, timeframe, data, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (symbol, timeframe, json.dumps(data), int(time.time())))
        
        conn.commit()
        conn.close()
    
    def get_cached_historical_data(self, symbol: str, timeframe: str, max_age_seconds: int = 3600) -> list:
        """Get cached historical data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = int(time.time()) - max_age_seconds
        
        cursor.execute('''
            SELECT data FROM historical_data
            WHERE symbol = ? AND timeframe = ? AND updated_at > ?
        ''', (symbol, timeframe, cutoff_time))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return []

# Global cache instance
market_cache = PersistentMarketCache()