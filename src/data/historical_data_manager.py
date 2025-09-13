"""
Historical Data Manager

Manages storage, retrieval, and processing of historical market data for backtesting and analysis.
"""

import logging
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import ccxt
import pandas as pd

from .exceptions import DataNotAvailableError, ExchangeConnectionError

logger = logging.getLogger(__name__)


class HistoricalDataManager:
    """Manages historical market data storage and retrieval."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize historical data manager.

        Args:
            config: Configuration dictionary with storage and exchange settings
        """
        self.config = config or {}
        self.storage_config = self.config.get("storage", {})
        self.exchange_config = self.config.get("exchange", {})

        # Storage settings
        self.database_path = self.storage_config.get(
            "database_path", "historical_data.db"
        )
        self.data_directory = self.storage_config.get(
            "data_directory", "data/historical"
        )

        # Exchange connection
        self.exchange: Optional[ccxt.Exchange] = None
        self._initialize_exchange()

        # Initialize storage
        self._initialize_storage()

        logger.info("HistoricalDataManager initialized with config: %s", self.config)

    def _initialize_exchange(self) -> None:
        """Initialize exchange connection for historical data fetching."""
        try:
            exchange_name = self.exchange_config.get("name", "binance")
            exchange_class = getattr(ccxt, exchange_name)
            self.exchange = exchange_class(
                {
                    "enableRateLimit": self.exchange_config.get(
                        "enableRateLimit", True
                    ),
                    "options": self.exchange_config.get("options", {}),
                }
            )

            logger.info("Exchange %s initialized for historical data", exchange_name)
        except Exception as e:
            logger.error("Failed to initialize exchange for historical data: %s", e)
            raise ExchangeConnectionError(f"Failed to initialize exchange: {e}")

    def _initialize_storage(self) -> None:
        """Initialize storage for historical data."""
        # Create data directory if it doesn't exist
        os.makedirs(self.data_directory, exist_ok=True)

        # Initialize database
        self._initialize_database()

        logger.info("Historical data storage initialized")

    def _initialize_database(self) -> None:
        """Initialize SQLite database for historical data."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Create tables for OHLCV data
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ohlcv_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL NOT NULL,
                UNIQUE(symbol, timeframe, timestamp)
            )
        """
        )

        # Create index for faster queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_timeframe 
            ON ohlcv_data (symbol, timeframe, timestamp)
        """
        )

        conn.commit()
        conn.close()

        logger.info("Historical data database initialized")

    def fetch_historical_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        since: Optional[Union[str, int, datetime]] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data from exchange.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframe: Timeframe for OHLCV data (e.g., '1m', '1h', '1d')
            since: Starting timestamp for data fetch
            limit: Maximum number of candles to fetch

        Returns:
            DataFrame with OHLCV data
        """
        if not self.exchange:
            raise ExchangeConnectionError("Exchange not initialized")

        try:
            # Convert since to milliseconds if needed
            if isinstance(since, str):
                since = int(pd.Timestamp(since).timestamp() * 1000)
            elif isinstance(since, datetime):
                since = int(since.timestamp() * 1000)

            # Fetch data from exchange
            ohlcv_data = self.exchange.fetch_ohlcv(
                symbol=symbol, timeframe=timeframe, since=since, limit=limit
            )

            if not ohlcv_data:
                raise DataNotAvailableError(
                    f"No historical data available for {symbol}"
                )

            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv_data,
                columns=["timestamp", "open", "high", "low", "close", "volume"],
            )

            # Convert timestamp to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df["symbol"] = symbol
            df["timeframe"] = timeframe

            # Set timestamp as index
            df.set_index("timestamp", inplace=True)

            logger.info(
                "Fetched %d historical candles for %s (%s) from exchange",
                len(df),
                symbol,
                timeframe,
            )

            return df

        except Exception as e:
            logger.error("Error fetching historical data for %s: %s", symbol, e)
            raise ExchangeConnectionError(f"Error fetching historical data: {e}")

    def store_ohlcv_data(self, df: pd.DataFrame) -> None:
        """Store OHLCV data in database.

        Args:
            df: DataFrame with OHLCV data including symbol and timeframe columns
        """
        if df.empty:
            logger.warning("Attempted to store empty DataFrame")
            return

        try:
            conn = sqlite3.connect(self.database_path)

            # Convert datetime index to milliseconds for storage
            df_to_store = df.reset_index()
            df_to_store["timestamp"] = df_to_store["timestamp"].astype("int64") // 10**6

            # Insert data into database
            df_to_store.to_sql(
                "ohlcv_data", conn, if_exists="append", index=False, method="multi"
            )

            conn.commit()
            conn.close()

            logger.info("Stored %d candles in database", len(df))

        except Exception as e:
            logger.error("Error storing historical data: %s", e)
            raise

    def load_ohlcv_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ) -> pd.DataFrame:
        """Load OHLCV data from database.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe for OHLCV data
            start_date: Start date for data retrieval
            end_date: End date for data retrieval

        Returns:
            DataFrame with OHLCV data
        """
        try:
            conn = sqlite3.connect(self.database_path)

            # Build query
            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM ohlcv_data
                WHERE symbol = ? AND timeframe = ?
            """
            params = [symbol, timeframe]

            # Add date filters if provided
            if start_date:
                if isinstance(start_date, str):
                    start_date = pd.Timestamp(start_date)
                start_timestamp = int(start_date.timestamp() * 1000)
                query += " AND timestamp >= ?"
                params.append(start_timestamp)

            if end_date:
                if isinstance(end_date, str):
                    end_date = pd.Timestamp(end_date)
                end_timestamp = int(end_date.timestamp() * 1000)
                query += " AND timestamp <= ?"
                params.append(end_timestamp)

            query += " ORDER BY timestamp ASC"

            # Execute query
            df = pd.read_sql_query(query, conn, params=params)

            conn.close()

            if df.empty:
                raise DataNotAvailableError(
                    f"No historical data found for {symbol} ({timeframe})"
                )

            # Convert timestamp to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)

            # Add symbol and timeframe columns
            df["symbol"] = symbol
            df["timeframe"] = timeframe

            logger.info(
                "Loaded %d historical candles for %s (%s) from database",
                len(df),
                symbol,
                timeframe,
            )

            return df

        except DataNotAvailableError:
            raise
        except Exception as e:
            logger.error("Error loading historical data for %s: %s", symbol, e)
            raise DataNotAvailableError(f"Error loading historical data: {e}")

    def update_historical_data(
        self, symbol: str, timeframe: str, days_back: int = 365
    ) -> None:
        """Update historical data for a symbol.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe for OHLCV data
            days_back: Number of days of historical data to fetch
        """
        try:
            # Calculate start date
            start_date = datetime.now() - timedelta(days=days_back)

            # Try to load existing data to find the last timestamp
            try:
                existing_data = self.load_ohlcv_data(
                    symbol=symbol, timeframe=timeframe, start_date=start_date
                )
                last_timestamp = existing_data.index[-1]
                # If we have recent data, start from the next period
                start_date = last_timestamp + pd.Timedelta(timeframe)
            except DataNotAvailableError:
                # No existing data, fetch from the beginning
                pass

            # Fetch new data
            new_data = self.fetch_historical_ohlcv(
                symbol=symbol, timeframe=timeframe, since=start_date
            )

            # Store new data
            if not new_data.empty:
                self.store_ohlcv_data(new_data)
                logger.info(
                    "Updated historical data for %s with %d new candles",
                    symbol,
                    len(new_data),
                )
            else:
                logger.info("No new data to update for %s", symbol)

        except Exception as e:
            logger.error("Error updating historical data for %s: %s", symbol, e)
            raise

    def get_available_symbols(self) -> List[str]:
        """Get list of symbols with stored historical data.

        Returns:
            List of symbols
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute("SELECT DISTINCT symbol FROM ohlcv_data")
            symbols = [row[0] for row in cursor.fetchall()]

            conn.close()

            logger.info("Found %d symbols with historical data", len(symbols))
            return symbols

        except Exception as e:
            logger.error("Error getting available symbols: %s", e)
            return []

    def get_available_timeframes(self, symbol: str) -> List[str]:
        """Get list of timeframes with stored historical data for a symbol.

        Args:
            symbol: Trading pair symbol

        Returns:
            List of timeframes
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT DISTINCT timeframe FROM ohlcv_data WHERE symbol = ?", (symbol,)
            )
            timeframes = [row[0] for row in cursor.fetchall()]

            conn.close()

            logger.info(
                "Found %d timeframes for %s with historical data",
                len(timeframes),
                symbol,
            )
            return timeframes

        except Exception as e:
            logger.error("Error getting available timeframes for %s: %s", symbol, e)
            return []

    def close(self) -> None:
        """Close any open connections."""
        logger.info("HistoricalDataManager closed")
