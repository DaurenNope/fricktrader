
from flask import Blueprint, jsonify
import requests
import os
from datetime import datetime
import sqlite3

trades_bp = Blueprint('trades', __name__)

# Freqtrade API configuration
FREQTRADE_API = "http://127.0.0.1:8080/api/v1"
FREQTRADE_AUTH = ("freqtrade", "freqtrade")

def get_trade_reasoning_from_db(pair):
    """Get trade reasoning from database for a specific pair"""
    try:
        db_path = "trade_logic.db"
        if os.path.exists(db_path):
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                # Try to get reasoning from enhanced table
                cursor.execute(
                    """
                    SELECT technical_reasoning, composite_score, entry_price
                    FROM trade_decisions 
                    WHERE pair = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """,
                    (pair,),
                )

                result = cursor.fetchone()
                if result:
                    return {
                        "entry_reasoning": result[0]
                        or f"Multi-signal analysis for {pair}",
                        "technical_score": 0.65,
                        "composite_score": result[1] or 0.68,
                    }

        # Fallback reasoning
        return {
            "entry_reasoning": f"Multi-signal analysis for {pair}",
            "technical_score": 0.65,
            "composite_score": 0.68,
        }
    except Exception as e:
        print(f"⚠️ Error getting trade reasoning: {e}")
        return {
            "entry_reasoning": f"Multi-signal analysis for {pair}",
            "technical_score": 0.65,
            "composite_score": 0.68,
        }

def calculate_avg_duration(trades):
    """Calculate average trade duration"""
    if not trades:
        return "0m"

    total_minutes = 0
    valid_trades = 0

    for trade in trades:
        duration = trade.get("duration", "0m")
        try:
            if "d" in duration:
                days = int(duration.split("d")[0])
                hours = (
                    int(duration.split("d")[1].split("h")[0]) if "h" in duration else 0
                )
                total_minutes += (days * 24 * 60) + (hours * 60)
                valid_trades += 1
            elif "h" in duration:
                hours = int(duration.split("h")[0])
                minutes = (
                    int(duration.split("h")[1].split("m")[0]) if "m" in duration else 0
                )
                total_minutes += (hours * 60) + minutes
                valid_trades += 1
            elif "m" in duration:
                minutes = int(duration.split("m")[0])
                total_minutes += minutes
                valid_trades += 1
        except Exception:
            continue

    if valid_trades == 0:
        return "0m"

    avg_minutes = total_minutes // valid_trades
    if avg_minutes > 1440:  # More than a day
        days = avg_minutes // 1440
        hours = (avg_minutes % 1440) // 60
        return f"{days}d {hours}h"
    elif avg_minutes > 60:  # More than an hour
        hours = avg_minutes // 60
        minutes = avg_minutes % 60
        return f"{hours}h {minutes}m"
    else:
        return f"{avg_minutes}m"

@trades_bp.route("/api/trades/active")
def get_active_trades():
    """Get active trades from Freqtrade API with enhanced data and precise formatting"""
    try:
        print("🔄 Fetching active trades from Freqtrade API...")

        # Get real data from Freqtrade API
        response = requests.get(
            f"{FREQTRADE_API}/status", auth=FREQTRADE_AUTH, timeout=10
        )

        if response.status_code == 200:
            trades_data = response.json()
            print(f"📊 Received {len(trades_data)} active trades from Freqtrade")

            # Format trades for UI with enhanced data and precise formatting
            formatted_trades = []
            total_profit = 0.0

            for trade in trades_data:
                profit_abs = trade.get("profit_abs", 0) or 0
                profit_pct = trade.get("profit_pct", 0) or 0
                total_profit += profit_abs

                # Calculate precise duration
                open_date = trade.get("open_date")
                duration = "Unknown"
                if open_date:
                    try:
                        from dateutil import parser

                        open_dt = parser.parse(open_date)
                        now = (
                            datetime.now(open_dt.tzinfo)
                            if open_dt.tzinfo
                            else datetime.now()
                        )
                        duration_delta = now - open_dt

                        total_hours = duration_delta.total_seconds() / 3600
                        if total_hours >= 24:
                            days = int(total_hours // 24)
                            hours = int(total_hours % 24)
                            duration = f"{days}d {hours}h"
                        elif total_hours >= 1:
                            hours = int(total_hours)
                            minutes = int((total_hours % 1) * 60)
                            duration = f"{hours}h {minutes}m"
                        else:
                            minutes = int(total_hours * 60)
                            duration = f"{minutes}m"
                    except Exception as e:
                        print(f"⚠️ Error calculating duration: {e}")
                        duration = "Unknown"

                # Get trade reasoning from database
                pair = trade.get("pair", "Unknown")
                reasoning = get_trade_reasoning_from_db(pair)

                # Determine side (LONG/SHORT)
                side = "SHORT" if trade.get("is_short", False) else "LONG"

                # Get precise rates
                open_rate = trade.get("open_rate", 0) or 0
                current_rate = trade.get("current_rate", open_rate) or open_rate
                amount = trade.get("amount", 0) or 0

                # Calculate risk level based on profit percentage and stop loss distance
                stop_loss_pct = trade.get("stop_loss_pct", 0) or 0
                if abs(profit_pct) < 1 and abs(stop_loss_pct) < 5:
                    risk_level = "LOW"
                elif abs(profit_pct) < 3 and abs(stop_loss_pct) < 10:
                    risk_level = "MEDIUM"
                else:
                    risk_level = "HIGH"

                formatted_trade = {
                    "trade_id": trade.get("trade_id"),
                    "pair": pair,
                    "side": side,
                    "amount": round(amount, 8),  # High precision for crypto amounts
                    "open_rate": round(open_rate, 6),  # 6 decimal places for prices
                    "current_rate": round(current_rate, 6),
                    "profit_pct": round(
                        profit_pct, 3
                    ),  # 3 decimal places for percentages
                    "profit_abs": round(profit_abs, 4),  # 4 decimal places for USDT
                    "profit_fiat": round(profit_abs, 4),
                    "open_date": open_date,
                    "duration": duration,
                    "strategy": trade.get("strategy", "MultiSignalStrategy"),
                    "is_open": trade.get("is_open", True),
                    "stop_loss": round(trade.get("stop_loss_abs", 0) or 0, 6),
                    "stop_loss_pct": round(stop_loss_pct, 2),
                    "entry_reasoning": reasoning.get(
                        "entry_reasoning",
                        f"Multi-signal {side} entry at ${open_rate:,.6f}",
                    ),
                    "current_status": f"${current_rate:,.6f} ({profit_pct:+.3f}%)",
                    "technical_score": reasoning.get("technical_score", 0.65),
                    "composite_score": reasoning.get("composite_score", 0.68),
                    "risk_level": risk_level,
                    "max_rate": round(
                        trade.get("max_rate", current_rate) or current_rate, 6
                    ),
                    "min_rate": round(
                        trade.get("min_rate", current_rate) or current_rate, 6
                    ),
                    "stake_amount": round(trade.get("stake_amount", 0) or 0, 4),
                    "fee_open": trade.get("fee_open", 0.001) or 0.001,
                    "leverage": trade.get("leverage", 1.0) or 1.0,
                }
                formatted_trades.append(formatted_trade)

            # Enhanced summary with precise calculations
            winning_trades = len([t for t in formatted_trades if t["profit_pct"] > 0])
            losing_trades = len([t for t in formatted_trades if t["profit_pct"] < 0])
            neutral_trades = len([t for t in formatted_trades if t["profit_pct"] == 0])

            # Calculate average profit percentage
            avg_profit_pct = (
                sum([t["profit_pct"] for t in formatted_trades]) / len(formatted_trades)
                if formatted_trades
                else 0
            )

            # Find best and worst trades
            best_trade = (
                max(formatted_trades, key=lambda x: x["profit_pct"])
                if formatted_trades
                else None
            )
            worst_trade = (
                min(formatted_trades, key=lambda x: x["profit_pct"])
                if formatted_trades
                else None
            )

            result = {
                "trades": formatted_trades,
                "summary": {
                    "total_trades": len(formatted_trades),
                    "winning_trades": winning_trades,
                    "losing_trades": losing_trades,
                    "neutral_trades": neutral_trades,
                    "win_rate": (
                        round((winning_trades / len(formatted_trades) * 100), 2)
                        if formatted_trades
                        else 0
                    ),
                    "total_profit_abs": round(total_profit, 4),
                    "total_profit_pct": round(avg_profit_pct, 3),
                    "best_trade": (
                        {
                            "pair": best_trade["pair"],
                            "profit_pct": best_trade["profit_pct"],
                            "profit_abs": best_trade["profit_abs"],
                        }
                        if best_trade
                        else None
                    ),
                    "worst_trade": (
                        {
                            "pair": worst_trade["pair"],
                            "profit_pct": worst_trade["profit_pct"],
                            "profit_abs": worst_trade["profit_abs"],
                        }
                        if worst_trade
                        else None
                    ),
                    "avg_duration": calculate_avg_duration(formatted_trades),
                    "total_stake": round(
                        sum([t["stake_amount"] for t in formatted_trades]), 4
                    ),
                    "data_source": "Freqtrade API",
                    "last_updated": datetime.now().isoformat(),
                },
            }

            print(
                f"✅ Retrieved {len(formatted_trades)} active trades with ${total_profit:.4f} total P&L"
            )
            print(
                f"📈 Win Rate: {result['summary']['win_rate']:.2f}% ({winning_trades}W/{losing_trades}L)"
            )

            return jsonify(result)

        else:
            print(
                f"❌ Freqtrade API returned status {response.status_code}: {response.text}"
            )
            # Return error with fallback structure
            return (
                jsonify(
                    {
                        "trades": [],
                        "summary": {
                            "total_trades": 0,
                            "winning_trades": 0,
                            "losing_trades": 0,
                            "win_rate": 0,
                            "total_profit_abs": 0,
                            "total_profit_pct": 0,
                            "data_source": "Error - API Unavailable",
                            "error": f"API returned {response.status_code}",
                        },
                    }
                ),
                503,
            )

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error connecting to Freqtrade API: {e}")
        return (
            jsonify(
                {
                    "trades": [],
                    "summary": {
                        "total_trades": 0,
                        "total_profit_abs": 0,
                        "data_source": "Error - Connection Failed",
                        "error": str(e),
                    },
                }
            ),
            503,
        )

    except Exception as e:
        print(f"❌ Unexpected error in get_active_trades: {e}")
        import traceback

        traceback.print_exc()
        return (
            jsonify(
                {
                    "trades": [],
                    "summary": {
                        "total_trades": 0,
                        "total_profit_abs": 0,
                        "data_source": "Error - Internal Server Error",
                        "error": str(e),
                    },
                }
            ),
            500,
        )

    except Exception as e:
        print(f"❌ Error getting active trades: {e}")
        return jsonify(
            {
                "trades": [],
                "summary": {
                    "total_trades": 0,
                    "total_profit_abs": 0,
                    "total_profit_pct": 0,
                },
                "error": str(e),
            }
        )

