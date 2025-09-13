"""
Seed the local trade logic database with rich demo data so the dashboard shows content.

This creates the `enhanced_trade_reasoning` table (if missing) and inserts
multiple realistic rows across different pairs and timeframes. It also seeds a
few entries in `trade_decisions` so the decisions endpoints are populated.
"""

from __future__ import annotations

import json
import random
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "src/web_ui/trade_logic.db"


def ensure_tables(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    # Enhanced reasoning table (used by advanced UI queries)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS enhanced_trade_reasoning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pair TEXT NOT NULL,
            entry_price REAL,
            entry_time TEXT,
            current_price REAL,
            profit_pct REAL,
            stop_loss REAL,
            amount REAL,
            duration_hours REAL,
            risk_percentage REAL,
            timeframe TEXT,
            technical_reasoning TEXT,
            onchain_reasoning TEXT,
            sentiment_reasoning TEXT,
            risk_management_reasoning TEXT,
            timeframe_analysis TEXT,
            indicator_values TEXT,
            composite_score REAL,
            signal_weights TEXT,
            exit_conditions TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Core decisions table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS trade_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            pair TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            technical_score REAL,
            technical_signals TEXT,
            technical_reasoning TEXT,
            onchain_score REAL,
            onchain_signals TEXT,
            onchain_reasoning TEXT,
            sentiment_score REAL,
            sentiment_signals TEXT,
            sentiment_reasoning TEXT,
            market_regime TEXT,
            regime_confidence REAL,
            composite_score REAL,
            final_decision INTEGER,
            position_size REAL,
            risk_assessment TEXT,
            decision_tree TEXT,
            threshold_analysis TEXT,
            signal_weights TEXT,
            market_conditions TEXT,
            volatility_metrics TEXT,
            correlation_data TEXT,
            trade_id INTEGER,
            outcome_profit_loss REAL,
            outcome_duration INTEGER,
            outcome_success BOOLEAN
        )
        """
    )

    conn.commit()


def seed_enhanced_reasoning(conn: sqlite3.Connection, num_rows: int = 24) -> int:
    cursor = conn.cursor()

    pairs = [
        "BTC/USDT",
        "ETH/USDT",
        "SOL/USDT",
        "LINK/USDT",
        "AVAX/USDT",
        "ATOM/USDT",
        "ADA/USDT",
        "DOT/USDT",
        "UNI/USDT",
    ]
    timeframes = ["15m", "1h", "4h", "1d"]

    inserted = 0
    now = datetime.utcnow()
    for _ in range(num_rows):
        pair = random.choice(pairs)
        timeframe = random.choice(timeframes)

        base_price = {
            "BTC/USDT": 48000,
            "ETH/USDT": 2600,
            "SOL/USDT": 145,
            "LINK/USDT": 18,
            "AVAX/USDT": 30,
            "ATOM/USDT": 9,
            "ADA/USDT": 0.65,
            "DOT/USDT": 7.5,
            "UNI/USDT": 8.2,
        }[pair]

        entry_price = round(base_price * random.uniform(0.97, 1.03), 4)
        current_price = round(base_price * random.uniform(0.95, 1.06), 4)
        profit_pct = round((current_price - entry_price) / entry_price * 100, 3)
        stop_loss = round(entry_price * random.uniform(0.9, 0.98), 4)
        amount = round(random.uniform(0.1, 2.5), 6)
        duration_hours = round(random.uniform(0.3, 72.0), 2)
        risk_percentage = round(random.uniform(0.3, 2.5), 2)
        entry_time = (now - timedelta(hours=duration_hours)).isoformat(timespec="seconds") + "Z"
        composite_score = round(random.uniform(0.45, 0.82), 3)

        technical_reasoning = [
            "EMA(20) > EMA(50) trend continuation",
            "RSI crossing midline from below",
            "MACD histogram turning positive",
        ]
        onchain_reasoning = [
            "Exchange outflows increased last 24h",
            "Whale accumulation clusters detected",
        ]
        sentiment_reasoning = [
            "Positive social sentiment uptick",
            "News momentum improving",
        ]
        risk_management_reasoning = [
            "2% risk per position",
            "Stop below swing low",
        ]
        timeframe_analysis = {
            "15m": {"bias": "neutral"},
            "1h": {"bias": "bullish"},
            "4h": {"bias": "bullish"},
            "1d": {"bias": "neutral"},
        }
        indicator_values = {
            "rsi": round(random.uniform(35, 65), 1),
            "macd": round(random.uniform(-0.5, 0.8), 3),
            "atr_percent": round(random.uniform(1.2, 4.0), 2),
            "volume_ratio": round(random.uniform(0.7, 1.6), 2),
        }
        signal_weights = {"technical": 0.5, "onchain": 0.25, "sentiment": 0.25}
        exit_conditions = [
            "Take-profit at +6%",
            "Trail stop once +3%",
            "Exit if RSI > 75 with divergence",
        ]

        cursor.execute(
            """
            INSERT INTO enhanced_trade_reasoning (
                pair, entry_price, entry_time, current_price, profit_pct, stop_loss, amount,
                duration_hours, risk_percentage, timeframe, technical_reasoning, onchain_reasoning,
                sentiment_reasoning, risk_management_reasoning, timeframe_analysis, indicator_values,
                composite_score, signal_weights, exit_conditions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pair,
                entry_price,
                entry_time,
                current_price,
                profit_pct,
                stop_loss,
                amount,
                duration_hours,
                risk_percentage,
                timeframe,
                "\n".join(technical_reasoning),
                "\n".join(onchain_reasoning),
                "\n".join(sentiment_reasoning),
                "\n".join(risk_management_reasoning),
                json.dumps(timeframe_analysis),
                json.dumps(indicator_values),
                composite_score,
                json.dumps(signal_weights),
                "\n".join(exit_conditions),
            ),
        )
        inserted += 1

    conn.commit()
    return inserted


def seed_trade_decisions(conn: sqlite3.Connection, num_rows: int = 12) -> int:
    cursor = conn.cursor()

    pairs = [
        "BTC/USDT",
        "ETH/USDT",
        "SOL/USDT",
        "LINK/USDT",
        "AVAX/USDT",
        "ATOM/USDT",
    ]
    timeframes = ["1h", "4h", "1d"]

    inserted = 0
    now = datetime.utcnow()
    for _ in range(num_rows):
        pair = random.choice(pairs)
        timeframe = random.choice(timeframes)
        ts = now - timedelta(hours=random.uniform(1, 120))

        technical_score = round(random.uniform(0.45, 0.85), 2)
        onchain_score = round(random.uniform(0.3, 0.8), 2)
        sentiment_score = round(random.uniform(0.3, 0.8), 2)
        composite_score = round(
            0.5 * technical_score + 0.25 * onchain_score + 0.25 * sentiment_score, 2
        )
        final_decision = 1 if composite_score >= 0.6 else 0
        position_size = round(random.uniform(0.05, 0.3), 4)

        technical_signals = {"rsi": {"value": random.randint(35, 65), "weight": 0.3, "contribution": 0.15}}
        onchain_signals = {"whale": {"value": random.uniform(0.1, 0.9), "weight": 0.25, "contribution": 0.1}}
        sentiment_signals = {"twitter": {"value": random.uniform(0.4, 0.7), "weight": 0.25, "contribution": 0.1}}

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
                market_conditions, volatility_metrics, correlation_data,
                trade_id, outcome_profit_loss, outcome_duration, outcome_success
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts.isoformat(timespec="seconds"),
                pair,
                timeframe,
                technical_score,
                json.dumps(technical_signals),
                json.dumps(["RSI improving", "MACD momentum building"]),
                onchain_score,
                json.dumps(onchain_signals),
                json.dumps(["Exchange outflows", "Decreasing exchange supply"]),
                sentiment_score,
                json.dumps(sentiment_signals),
                json.dumps(["Positive social mentions"]),
                random.choice(["bullish", "neutral", "bearish"]),
                round(random.uniform(0.55, 0.9), 2),
                composite_score,
                final_decision,
                position_size,
                json.dumps({"max_risk_pct": 2}),
                json.dumps({"nodes": ["entry", "manage", "exit"]}),
                json.dumps({"entry": 0.6}),
                json.dumps({"technical": 0.5, "onchain": 0.25, "sentiment": 0.25}),
                json.dumps({"vol_profile": "balanced"}),
                json.dumps({"atr_pct": round(random.uniform(1.2, 4.0), 2)}),
                json.dumps({"btc_correlation": round(random.uniform(0.2, 0.9), 2)}),
                None,
                None,
                None,
                None,
            ),
        )
        inserted += 1

    conn.commit()
    return inserted


def main(db_path: str | None = None) -> None:
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    ensure_tables(conn)

    # Only seed if tables are empty to avoid duplicates on repeated runs
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM enhanced_trade_reasoning")
    enhanced_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM trade_decisions")
    decisions_count = cur.fetchone()[0]

    ins_enhanced = 0
    ins_decisions = 0
    if enhanced_count == 0:
        ins_enhanced = seed_enhanced_reasoning(conn, num_rows=28)
    if decisions_count == 0:
        ins_decisions = seed_trade_decisions(conn, num_rows=18)

    print(
        f"Seed complete. DB={path} enhanced_trade_reasoning+{ins_enhanced}, trade_decisions+{ins_decisions}."
    )
    conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seed demo data into dashboard DB")
    parser.add_argument("--db", dest="db", default=None, help="Path to sqlite DB (defaults to src/web_ui/trade_logic.db)")
    args = parser.parse_args()
    main(args.db)


