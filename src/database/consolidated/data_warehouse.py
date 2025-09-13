"""
Data Warehouse

Centralized data storage for all trading system data with optimized time-series storage.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)


class DataWarehouse:
    """Centralized data warehouse for trading system data."""

    def __init__(self, db_path: str = "data_warehouse.db") -> None:
        """Initialize data warehouse.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._initialize_database()

        logger.info("DataWarehouse initialized with database: %s", db_path)

    def _initialize_database(self) -> None:
        """Initialize the data warehouse database with all required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create OHLCV data table with optimized schema for time-series data
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
                trades INTEGER,
                vwap REAL,
                UNIQUE(symbol, timeframe, timestamp)
            )
        """
        )

        # Create index for faster time-series queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_timeframe_timestamp
            ON ohlcv_data (symbol, timeframe, timestamp)
        """
        )

        # Create market data table for alternative data sources
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_type TEXT NOT NULL, -- 'sentiment', 'onchain', 'economic', etc.
                symbol TEXT,
                timestamp INTEGER NOT NULL,
                data TEXT NOT NULL, -- JSON formatted data
                source TEXT,
                UNIQUE(data_type, symbol, timestamp)
            )
        """
        )

        # Create index for market data queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_market_data_type_symbol_timestamp
            ON market_data (data_type, symbol, timestamp)
        """
        )

        # Create trading signals table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trading_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                signal_type TEXT NOT NULL, -- 'BUY', 'SELL', 'HOLD'
                confidence REAL,
                technical_score REAL,
                sentiment_score REAL,
                onchain_score REAL,
                metadata TEXT, -- JSON formatted additional data
                UNIQUE(strategy_name, symbol, timestamp)
            )
        """
        )

        # Create index for trading signals
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_trading_signals_strategy_symbol_timestamp
            ON trading_signals (strategy_name, symbol, timestamp)
        """
        )

        # Create trades table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                trade_type TEXT NOT NULL, -- 'ENTRY', 'EXIT'
                price REAL NOT NULL,
                amount REAL NOT NULL,
                fee REAL,
                profit_loss REAL,
                profit_loss_pct REAL,
                metadata TEXT, -- JSON formatted additional data
                UNIQUE(strategy_name, symbol, timestamp, trade_type)
            )
        """
        )

        # Create index for trades
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_trades_strategy_symbol_timestamp
            ON trades (strategy_name, symbol, timestamp)
        """
        )

        # Create performance metrics table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                symbol TEXT,
                period_start INTEGER NOT NULL,
                period_end INTEGER NOT NULL,
                metric_type TEXT NOT NULL, -- 'sharpe_ratio', 'win_rate', 'max_drawdown', etc.
                value REAL NOT NULL,
                metadata TEXT, -- JSON formatted additional data
                UNIQUE(strategy_name, symbol, period_start, period_end, metric_type)
            )
        """
        )

        # Create index for performance metrics
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_performance_metrics_strategy_symbol_period
            ON performance_metrics (strategy_name, symbol, period_start, period_end)
        """
        )

        conn.commit()
        conn.close()

        logger.info("Data warehouse database initialized")

    def store_ohlcv_data(self, df: pd.DataFrame) -> None:
        """Store OHLCV data in the data warehouse.

        Args:
            df: DataFrame with OHLCV data including symbol and timeframe columns
        """
        if df.empty:
            logger.warning("Attempted to store empty OHLCV DataFrame")
            return

        try:
            conn = sqlite3.connect(self.db_path)

            # Convert datetime index to milliseconds for storage
            df_to_store = df.reset_index()
            if "timestamp" in df_to_store.columns:
                df_to_store["timestamp"] = pd.to_datetime(df_to_store["timestamp"])
                df_to_store["timestamp"] = (
                    df_to_store["timestamp"].astype("int64") // 10**6
                )

            # Insert data into database
            df_to_store.to_sql(
                "ohlcv_data", conn, if_exists="append", index=False, method="multi"
            )

            conn.commit()
            conn.close()

            logger.info("Stored %d OHLCV data points in warehouse", len(df))

        except Exception as e:
            logger.error("Error storing OHLCV data in warehouse: %s", e)
            raise

    def load_ohlcv_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ) -> pd.DataFrame:
        """Load OHLCV data from the data warehouse.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe for OHLCV data
            start_date: Start date for data retrieval
            end_date: End date for data retrieval

        Returns:
            DataFrame with OHLCV data
        """
        try:
            conn = sqlite3.connect(self.db_path)

            # Build query
            query = """
                SELECT timestamp, open, high, low, close, volume, trades, vwap
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
                logger.info("No OHLCV data found for %s (%s)", symbol, timeframe)
                return df

            # Convert timestamp to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)

            # Add symbol and timeframe columns
            df["symbol"] = symbol
            df["timeframe"] = timeframe

            logger.info(
                "Loaded %d OHLCV data points for %s (%s) from warehouse",
                len(df),
                symbol,
                timeframe,
            )

            return df

        except Exception as e:
            logger.error(
                "Error loading OHLCV data from warehouse for %s: %s", symbol, e
            )
            raise

    def store_market_data(
        self,
        data_type: str,
        data: Dict[str, Any],
        symbol: Optional[str] = None,
        timestamp: Optional[int] = None,
        source: Optional[str] = None,
    ) -> None:
        """Store alternative market data in the data warehouse.

        Args:
            data_type: Type of market data (e.g., 'sentiment', 'onchain')
            data: Dictionary with market data
            symbol: Trading pair symbol (optional)
            timestamp: Timestamp in milliseconds (optional, defaults to current time)
            source: Source of the data (optional)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Convert data to JSON
            import json

            data_json = json.dumps(data)

            # Use current timestamp if not provided
            if timestamp is None:
                timestamp = int(datetime.now().timestamp() * 1000)

            # Insert data
            cursor.execute(
                """
                INSERT OR REPLACE INTO market_data 
                (data_type, symbol, timestamp, data, source)
                VALUES (?, ?, ?, ?, ?)
            """,
                (data_type, symbol, timestamp, data_json, source),
            )

            conn.commit()
            conn.close()

            logger.info(
                "Stored %s market data for %s in warehouse",
                data_type,
                symbol or "all symbols",
            )

        except Exception as e:
            logger.error("Error storing market data in warehouse: %s", e)
            raise

    def load_market_data(
        self,
        data_type: str,
        symbol: Optional[str] = None,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ) -> pd.DataFrame:
        """Load alternative market data from the data warehouse.

        Args:
            data_type: Type of market data to load
            symbol: Trading pair symbol (optional)
            start_date: Start date for data retrieval
            end_date: End date for data retrieval

        Returns:
            DataFrame with market data
        """
        try:
            conn = sqlite3.connect(self.db_path)

            # Build query
            query = "SELECT timestamp, symbol, data, source FROM market_data WHERE data_type = ?"
            params = [data_type]

            # Add symbol filter if provided
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)

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
                logger.info("No %s market data found", data_type)
                return df

            # Convert timestamp to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)

            # Parse JSON data
            import json

            df["data"] = df["data"].apply(json.loads)

            logger.info(
                "Loaded %d %s market data points from warehouse", len(df), data_type
            )

            return df

        except Exception as e:
            logger.error("Error loading market data from warehouse: %s", e)
            raise

    def store_trading_signal(
        self,
        strategy_name: str,
        symbol: str,
        timestamp: int,
        signal_type: str,
        confidence: Optional[float] = None,
        technical_score: Optional[float] = None,
        sentiment_score: Optional[float] = None,
        onchain_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store a trading signal in the data warehouse.

        Args:
            strategy_name: Name of the strategy that generated the signal
            symbol: Trading pair symbol
            timestamp: Timestamp in milliseconds
            signal_type: Type of signal (BUY, SELL, HOLD)
            confidence: Confidence level of the signal (0.0-1.0)
            technical_score: Technical analysis score
            sentiment_score: Sentiment analysis score
            onchain_score: On-chain analysis score
            metadata: Additional metadata about the signal
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Convert metadata to JSON
            import json

            metadata_json = json.dumps(metadata) if metadata else None

            # Insert signal
            cursor.execute(
                """
                INSERT OR REPLACE INTO trading_signals 
                (strategy_name, symbol, timestamp, signal_type, confidence, 
                 technical_score, sentiment_score, onchain_score, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    strategy_name,
                    symbol,
                    timestamp,
                    signal_type,
                    confidence,
                    technical_score,
                    sentiment_score,
                    onchain_score,
                    metadata_json,
                ),
            )

            conn.commit()
            conn.close()

            logger.info(
                "Stored %s signal for %s from %s strategy in warehouse",
                signal_type,
                symbol,
                strategy_name,
            )

        except Exception as e:
            logger.error("Error storing trading signal in warehouse: %s", e)
            raise

    def load_trading_signals(
        self,
        strategy_name: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
    ) -> pd.DataFrame:
        """Load trading signals from the data warehouse.

        Args:
            strategy_name: Name of the strategy (optional)
            symbol: Trading pair symbol (optional)
            start_date: Start date for data retrieval
            end_date: End date for data retrieval

        Returns:
            DataFrame with trading signals
        """
        try:
            conn = sqlite3.connect(self.db_path)

            # Build query
            query = "SELECT * FROM trading_signals WHERE 1=1"
            params = []

            # Add filters if provided
            if strategy_name:
                query += " AND strategy_name = ?"
                params.append(strategy_name)

            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)

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
                logger.info("No trading signals found")
                return df

            # Convert timestamp to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)

            # Parse JSON metadata
            import json

            df["metadata"] = df["metadata"].apply(
                lambda x: json.loads(x) if x else None
            )

            logger.info("Loaded %d trading signals from warehouse", len(df))

            return df

        except Exception as e:
            logger.error("Error loading trading signals from warehouse: %s", e)
            raise

    def get_data_summary(self) -> Dict[str, Any]:
        """Get a summary of data stored in the warehouse.

        Returns:
            Dictionary with data summary statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get OHLCV data summary
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT symbol) as unique_symbols,
                    COUNT(DISTINCT timeframe) as unique_timeframes,
                    MIN(timestamp) as earliest_timestamp,
                    MAX(timestamp) as latest_timestamp
                FROM ohlcv_data
            """
            )
            ohlcv_summary = cursor.fetchone()

            # Get market data summary
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT data_type) as unique_data_types,
                    COUNT(DISTINCT symbol) as unique_symbols,
                    MIN(timestamp) as earliest_timestamp,
                    MAX(timestamp) as latest_timestamp
                FROM market_data
            """
            )
            market_summary = cursor.fetchone()

            # Get trading signals summary
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT strategy_name) as unique_strategies,
                    COUNT(DISTINCT symbol) as unique_symbols,
                    MIN(timestamp) as earliest_timestamp,
                    MAX(timestamp) as latest_timestamp
                FROM trading_signals
            """
            )
            signals_summary = cursor.fetchone()

            conn.close()

            summary = {
                "ohlcv_data": {
                    "total_records": ohlcv_summary[0] if ohlcv_summary else 0,
                    "unique_symbols": ohlcv_summary[1] if ohlcv_summary else 0,
                    "unique_timeframes": ohlcv_summary[2] if ohlcv_summary else 0,
                    "date_range": (
                        {
                            "earliest": (
                                pd.to_datetime(ohlcv_summary[3], unit="ms")
                                if ohlcv_summary and ohlcv_summary[3]
                                else None
                            ),
                            "latest": (
                                pd.to_datetime(ohlcv_summary[4], unit="ms")
                                if ohlcv_summary and ohlcv_summary[4]
                                else None
                            ),
                        }
                        if ohlcv_summary
                        else {}
                    ),
                },
                "market_data": {
                    "total_records": market_summary[0] if market_summary else 0,
                    "unique_data_types": market_summary[1] if market_summary else 0,
                    "unique_symbols": market_summary[2] if market_summary else 0,
                    "date_range": (
                        {
                            "earliest": (
                                pd.to_datetime(market_summary[3], unit="ms")
                                if market_summary and market_summary[3]
                                else None
                            ),
                            "latest": (
                                pd.to_datetime(market_summary[4], unit="ms")
                                if market_summary and market_summary[4]
                                else None
                            ),
                        }
                        if market_summary
                        else {}
                    ),
                },
                "trading_signals": {
                    "total_records": signals_summary[0] if signals_summary else 0,
                    "unique_strategies": signals_summary[1] if signals_summary else 0,
                    "unique_symbols": signals_summary[2] if signals_summary else 0,
                    "date_range": (
                        {
                            "earliest": (
                                pd.to_datetime(signals_summary[3], unit="ms")
                                if signals_summary and signals_summary[3]
                                else None
                            ),
                            "latest": (
                                pd.to_datetime(signals_summary[4], unit="ms")
                                if signals_summary and signals_summary[4]
                                else None
                            ),
                        }
                        if signals_summary
                        else {}
                    ),
                },
            }

            logger.info("Generated data warehouse summary")
            return summary

        except Exception as e:
            logger.error("Error generating data warehouse summary: %s", e)
            raise

    def close(self) -> None:
        """Close any open connections."""
        logger.info("DataWarehouse closed")
