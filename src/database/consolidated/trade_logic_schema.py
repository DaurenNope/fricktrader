"""
Trade Logic Database Schema
Creates tables for storing comprehensive trade decision data
"""

import json
import os
import sqlite3
from datetime import datetime


class TradeLogicDBManager:
    """
    Manages the trade logic database schema and operations
    """

    def __init__(self, db_path="trade_logic.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the trade logic database with all required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create trade_decisions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trade_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                pair TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                
                -- Technical Analysis
                technical_score REAL,
                technical_signals TEXT, -- JSON
                technical_reasoning TEXT, -- JSON array
                
                -- On-Chain Analysis
                onchain_score REAL,
                onchain_signals TEXT, -- JSON
                onchain_reasoning TEXT, -- JSON array
                
                -- Sentiment Analysis
                sentiment_score REAL,
                sentiment_signals TEXT, -- JSON
                sentiment_reasoning TEXT, -- JSON array
                
                -- Market Regime
                market_regime TEXT,
                regime_confidence REAL,
                
                -- Final Decision
                composite_score REAL,
                final_decision INTEGER, -- 0 or 1
                position_size REAL,
                risk_assessment TEXT, -- JSON
                
                -- Decision Logic
                decision_tree TEXT, -- JSON
                threshold_analysis TEXT, -- JSON
                signal_weights TEXT, -- JSON
                
                -- Market Context
                market_conditions TEXT, -- JSON
                volatility_metrics TEXT, -- JSON
                correlation_data TEXT, -- JSON
                
                -- Outcome (filled after trade completion)
                trade_id INTEGER,
                outcome_profit_loss REAL,
                outcome_duration INTEGER, -- minutes
                outcome_success BOOLEAN,
                
                FOREIGN KEY (trade_id) REFERENCES trades (id)
            )
        """
        )

        # Create signal_performance table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS signal_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_type TEXT NOT NULL, -- 'technical', 'onchain', 'sentiment'
                signal_name TEXT NOT NULL, -- 'rsi', 'whale_movement', 'twitter_sentiment'
                decision_id INTEGER NOT NULL,
                signal_value REAL,
                signal_weight REAL,
                contribution_to_decision REAL,
                outcome_correlation REAL,
                
                FOREIGN KEY (decision_id) REFERENCES trade_decisions (id)
            )
        """
        )

        # Create decision_patterns table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS decision_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_description TEXT,
                success_rate REAL,
                avg_profit REAL,
                frequency INTEGER,
                confidence_level REAL,
                pattern_conditions TEXT, -- JSON
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create parameter_optimizations table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS parameter_optimizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                optimization_date DATETIME NOT NULL,
                parameter_set TEXT, -- JSON
                backtest_period TEXT,
                performance_metrics TEXT, -- JSON
                validation_results TEXT, -- JSON
                applied BOOLEAN DEFAULT FALSE,
                notes TEXT
            )
        """
        )

        # Create indexes for efficient querying
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_trade_decisions_timestamp ON trade_decisions(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_trade_decisions_pair ON trade_decisions(pair)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_trade_decisions_composite_score ON trade_decisions(composite_score)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_signal_performance_decision_id ON signal_performance(decision_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_signal_performance_type ON signal_performance(signal_type)"
        )

        conn.commit()
        conn.close()

        print("✅ Trade logic database schema created successfully")

    def store_decision(self, decision_data):
        """Store a complete trade decision with all analysis data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO trade_decisions (
                    timestamp, pair, timeframe,
                    technical_score, technical_signals, technical_reasoning,
                    onchain_score, onchain_signals, onchain_reasoning,
                    sentiment_score, sentiment_signals, sentiment_reasoning,
                    market_regime, regime_confidence,
                    composite_score, final_decision, position_size, risk_assessment,
                    decision_tree, threshold_analysis, signal_weights,
                    market_conditions, volatility_metrics, correlation_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    decision_data["timestamp"],
                    decision_data["pair"],
                    decision_data["timeframe"],
                    decision_data.get("technical_score"),
                    json.dumps(decision_data.get("technical_signals", {})),
                    json.dumps(decision_data.get("technical_reasoning", [])),
                    decision_data.get("onchain_score"),
                    json.dumps(decision_data.get("onchain_signals", {})),
                    json.dumps(decision_data.get("onchain_reasoning", [])),
                    decision_data.get("sentiment_score"),
                    json.dumps(decision_data.get("sentiment_signals", {})),
                    json.dumps(decision_data.get("sentiment_reasoning", [])),
                    decision_data.get("market_regime"),
                    decision_data.get("regime_confidence"),
                    decision_data.get("composite_score"),
                    decision_data.get("final_decision"),
                    decision_data.get("position_size"),
                    json.dumps(decision_data.get("risk_assessment", {})),
                    json.dumps(decision_data.get("decision_tree", {})),
                    json.dumps(decision_data.get("threshold_analysis", {})),
                    json.dumps(decision_data.get("signal_weights", {})),
                    json.dumps(decision_data.get("market_conditions", {})),
                    json.dumps(decision_data.get("volatility_metrics", {})),
                    json.dumps(decision_data.get("correlation_data", {})),
                ),
            )

            decision_id = cursor.lastrowid

            # Store individual signal performance data
            for signal_type in ["technical", "onchain", "sentiment"]:
                signals = decision_data.get(f"{signal_type}_signals", {})
                for signal_name, signal_data in signals.items():
                    if isinstance(signal_data, dict) and "value" in signal_data:
                        cursor.execute(
                            """
                            INSERT INTO signal_performance (
                                signal_type, signal_name, decision_id,
                                signal_value, signal_weight, contribution_to_decision
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                            (
                                signal_type,
                                signal_name,
                                decision_id,
                                signal_data.get("value", 0),
                                signal_data.get("weight", 0),
                                signal_data.get("contribution", 0),
                            ),
                        )

            conn.commit()
            print(f"✅ Stored trade decision {decision_id} for {decision_data['pair']}")
            return decision_id

        except Exception as e:
            conn.rollback()
            print(f"❌ Error storing decision: {e}")
            return None
        finally:
            conn.close()

    def get_decision(self, decision_id):
        """Retrieve a specific trade decision by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM trade_decisions WHERE id = ?", (decision_id,))
        row = cursor.fetchone()

        if row:
            columns = [description[0] for description in cursor.description]
            decision = dict(zip(columns, row))

            # Parse JSON fields
            json_fields = [
                "technical_signals",
                "technical_reasoning",
                "onchain_signals",
                "onchain_reasoning",
                "sentiment_signals",
                "sentiment_reasoning",
                "risk_assessment",
                "decision_tree",
                "threshold_analysis",
                "signal_weights",
                "market_conditions",
                "volatility_metrics",
                "correlation_data",
            ]

            for field in json_fields:
                if decision[field]:
                    try:
                        decision[field] = json.loads(decision[field])
                    except json.JSONDecodeError:
                        decision[field] = {}

            conn.close()
            return decision

        conn.close()
        return None

    def get_decisions(self, filters=None, limit=100):
        """Get trade decisions with optional filters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM trade_decisions"
        params = []

        if filters:
            conditions = []
            if "pair" in filters:
                conditions.append("pair = ?")
                params.append(filters["pair"])
            if "start_date" in filters:
                conditions.append("timestamp >= ?")
                params.append(filters["start_date"])
            if "end_date" in filters:
                conditions.append("timestamp <= ?")
                params.append(filters["end_date"])
            if "min_score" in filters:
                conditions.append("composite_score >= ?")
                params.append(filters["min_score"])

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        decisions = []
        if rows:
            columns = [description[0] for description in cursor.description]
            for row in rows:
                decision = dict(zip(columns, row))
                decisions.append(decision)

        conn.close()
        return decisions

    def get_decision_by_trade_id(self, trade_id):
        """Retrieve a trade decision by trade ID"""
        if not trade_id:
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT * FROM trade_decisions WHERE trade_id = ?", (trade_id,)
            )
            row = cursor.fetchone()

            if row:
                columns = [description[0] for description in cursor.description]
                decision = dict(zip(columns, row))

                # Parse JSON fields
                json_fields = [
                    "technical_signals",
                    "technical_reasoning",
                    "onchain_signals",
                    "onchain_reasoning",
                    "sentiment_signals",
                    "sentiment_reasoning",
                    "decision_tree",
                    "threshold_analysis",
                    "signal_weights",
                    "market_conditions",
                    "volatility_metrics",
                    "correlation_data",
                    "risk_assessment",
                ]

                for field in json_fields:
                    if decision.get(field):
                        try:
                            decision[field] = json.loads(decision[field])
                        except (json.JSONDecodeError, TypeError):
                            decision[field] = {}

                return decision

        except Exception as e:
            print(f"❌ Error retrieving decision by trade ID {trade_id}: {e}")
        finally:
            conn.close()

        return None

    def update_trade_outcome(
        self, decision_id, trade_id, profit_loss, duration, success
    ):
        """Update decision with actual trade outcome"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE trade_decisions 
            SET trade_id = ?, outcome_profit_loss = ?, outcome_duration = ?, outcome_success = ?
            WHERE id = ?
        """,
            (trade_id, profit_loss, duration, success, decision_id),
        )

        conn.commit()
        conn.close()

        print(f"✅ Updated decision {decision_id} with trade outcome")


if __name__ == "__main__":
    # Test the database schema
    db_manager = TradeLogicDBManager("test_trade_logic.db")

    # Test storing a decision
    test_decision = {
        "timestamp": datetime.now(),
        "pair": "BTC/USDT",
        "timeframe": "1h",
        "technical_score": 0.75,
        "technical_signals": {
            "rsi": {"value": 35, "signal": "oversold", "weight": 0.3},
            "macd": {"value": 0.05, "signal": "bullish", "weight": 0.4},
        },
        "technical_reasoning": [
            "RSI at 35 indicates oversold conditions",
            "MACD bullish crossover detected",
        ],
        "onchain_score": 0.65,
        "sentiment_score": 0.55,
        "composite_score": 0.68,
        "final_decision": 1,
        "position_size": 0.1,
        "market_regime": "bullish",
    }

    decision_id = db_manager.store_decision(test_decision)
    if decision_id:
        retrieved = db_manager.get_decision(decision_id)
        print(f"✅ Successfully stored and retrieved decision: {retrieved['pair']}")

    # Clean up test database
    os.remove("test_trade_logic.db")
