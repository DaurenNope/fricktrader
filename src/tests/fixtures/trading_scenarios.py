"""
Complex trading scenario fixtures for comprehensive testing.

Provides realistic market data scenarios including bull markets,
bear markets, high volatility, flash crashes, and more.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest


class TradingScenarios:
    """Factory class for generating complex trading scenarios."""

    @staticmethod
    def generate_bull_market_scenario(
        duration_days: int = 30,
        start_price: float = 40000.0,
        end_price: float = 60000.0,
        timeframe_minutes: int = 60,
    ) -> pd.DataFrame:
        """Generate bull market scenario with steady uptrend."""

        # Calculate number of data points
        points_per_day = 24 * (60 // timeframe_minutes)
        total_points = duration_days * points_per_day

        # Generate timestamps
        start_date = datetime(2024, 1, 1)
        timestamps = [
            start_date + timedelta(minutes=i * timeframe_minutes)
            for i in range(total_points)
        ]

        # Generate progressive price increase with realistic volatility
        price_progression = np.linspace(start_price, end_price, total_points)

        data = []
        for i, timestamp in enumerate(timestamps):
            base_price = price_progression[i]

            # Add realistic intraday volatility (0.5% - 2%)
            volatility = np.random.uniform(0.005, 0.02)
            daily_change = np.random.normal(0, volatility)

            open_price = base_price * (1 + daily_change)

            # OHLC relationships for bull market (generally positive)
            high_multiplier = np.random.uniform(1.001, 1.015)  # 0.1% to 1.5% above
            low_multiplier = np.random.uniform(0.985, 0.999)  # 1.5% to 0.1% below
            close_bias = np.random.uniform(0.995, 1.01)  # Slight upward bias

            high = open_price * high_multiplier
            low = open_price * low_multiplier
            close = open_price * close_bias

            # Ensure OHLC relationships are valid
            high = max(high, open_price, close)
            low = min(low, open_price, close)

            # Bull market typically has higher volume
            base_volume = np.random.uniform(10000, 50000)
            volume_multiplier = 1 + (i / total_points) * 0.5  # Increasing volume
            volume = base_volume * volume_multiplier

            data.append(
                {
                    "timestamp": timestamp,
                    "open": round(open_price, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "close": round(close, 2),
                    "volume": int(volume),
                }
            )

        return pd.DataFrame(data)

    @staticmethod
    def generate_bear_market_scenario(
        duration_days: int = 45,
        start_price: float = 60000.0,
        end_price: float = 35000.0,
        timeframe_minutes: int = 60,
    ) -> pd.DataFrame:
        """Generate bear market scenario with declining trend."""

        points_per_day = 24 * (60 // timeframe_minutes)
        total_points = duration_days * points_per_day

        start_date = datetime(2024, 2, 1)
        timestamps = [
            start_date + timedelta(minutes=i * timeframe_minutes)
            for i in range(total_points)
        ]

        # Generate progressive price decrease
        price_progression = np.linspace(start_price, end_price, total_points)

        data = []
        for i, timestamp in enumerate(timestamps):
            base_price = price_progression[i]

            # Bear market volatility (often higher)
            volatility = np.random.uniform(0.01, 0.03)
            daily_change = np.random.normal(-0.005, volatility)  # Negative bias

            open_price = base_price * (1 + daily_change)

            # OHLC for bear market (generally negative bias)
            high_multiplier = np.random.uniform(1.001, 1.012)
            low_multiplier = np.random.uniform(0.98, 0.995)  # Deeper lows
            close_bias = np.random.uniform(0.985, 1.005)  # Downward bias

            high = open_price * high_multiplier
            low = open_price * low_multiplier
            close = open_price * close_bias

            # Ensure OHLC relationships are valid
            high = max(high, open_price, close)
            low = min(low, open_price, close)

            # Bear market often has panic selling (higher volume on red days)
            base_volume = np.random.uniform(15000, 80000)
            if close < open:  # Red candle
                volume_multiplier = np.random.uniform(1.2, 2.5)
            else:
                volume_multiplier = np.random.uniform(0.8, 1.2)

            volume = base_volume * volume_multiplier

            data.append(
                {
                    "timestamp": timestamp,
                    "open": round(open_price, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "close": round(close, 2),
                    "volume": int(volume),
                }
            )

        return pd.DataFrame(data)

    @staticmethod
    def generate_flash_crash_scenario(
        normal_duration_hours: int = 24,
        crash_duration_minutes: int = 15,
        recovery_duration_hours: int = 6,
        start_price: float = 45000.0,
        crash_depth_pct: float = 20.0,
    ) -> pd.DataFrame:
        """Generate flash crash scenario with rapid decline and recovery."""

        data = []
        current_time = datetime(2024, 3, 1)

        # Phase 1: Normal trading before crash
        normal_points = normal_duration_hours * 4  # 15-minute candles
        for i in range(normal_points):
            # Stable sideways movement
            price_noise = np.random.uniform(-0.5, 0.5) / 100
            open_price = start_price * (1 + price_noise)

            high = open_price * np.random.uniform(1.001, 1.008)
            low = open_price * np.random.uniform(0.992, 0.999)
            close = open_price * np.random.uniform(0.998, 1.002)

            high = max(high, open_price, close)
            low = min(low, open_price, close)

            volume = np.random.uniform(8000, 15000)

            data.append(
                {
                    "timestamp": current_time,
                    "open": round(open_price, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "close": round(close, 2),
                    "volume": int(volume),
                }
            )

            current_time += timedelta(minutes=15)

        # Phase 2: Flash crash (1-minute candles for detail)
        crash_price = start_price * (1 - crash_depth_pct / 100)
        crash_points = crash_duration_minutes
        price_drop_per_minute = (start_price - crash_price) / crash_points

        current_crash_price = start_price
        for i in range(crash_points):
            current_crash_price -= price_drop_per_minute

            # Extreme selling pressure
            open_price = current_crash_price + price_drop_per_minute
            close_price = current_crash_price

            # Massive spread during crash
            high = open_price * 1.002
            low = close_price * 0.95  # Flash crash wicks

            # Extreme volume during crash
            volume = np.random.uniform(100000, 500000)

            data.append(
                {
                    "timestamp": current_time,
                    "open": round(open_price, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "close": round(close_price, 2),
                    "volume": int(volume),
                }
            )

            current_time += timedelta(minutes=1)

        # Phase 3: Recovery (15-minute candles)
        recovery_points = recovery_duration_hours * 4
        recovery_target = start_price * 0.95  # 95% recovery
        price_recovery_per_candle = (recovery_target - crash_price) / recovery_points

        current_recovery_price = crash_price
        for i in range(recovery_points):
            current_recovery_price += price_recovery_per_candle

            # Recovery volatility
            volatility = max(0.03 - (i / recovery_points) * 0.02, 0.01)
            open_price = current_recovery_price
            close_price = current_recovery_price * (
                1 + np.random.uniform(-volatility, volatility)
            )

            high = max(open_price, close_price) * np.random.uniform(1.005, 1.02)
            low = min(open_price, close_price) * np.random.uniform(0.98, 0.995)

            # High volume during recovery
            volume = np.random.uniform(30000, 100000)

            data.append(
                {
                    "timestamp": current_time,
                    "open": round(open_price, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "close": round(close_price, 2),
                    "volume": int(volume),
                }
            )

            current_time += timedelta(minutes=15)

        return pd.DataFrame(data)

    @staticmethod
    def generate_high_volatility_scenario(
        duration_days: int = 7,
        base_price: float = 42000.0,
        volatility_factor: float = 0.05,
    ) -> pd.DataFrame:
        """Generate high volatility scenario with extreme price swings."""

        points_per_day = 96  # 15-minute candles
        total_points = duration_days * points_per_day

        start_date = datetime(2024, 4, 1)
        timestamps = [
            start_date + timedelta(minutes=i * 15) for i in range(total_points)
        ]

        data = []
        current_price = base_price

        for i, timestamp in enumerate(timestamps):
            # Extreme price movements
            price_change = np.random.normal(0, volatility_factor)
            new_price = current_price * (1 + price_change)

            # Ensure price doesn't go negative or too extreme
            new_price = max(new_price, base_price * 0.5)
            new_price = min(new_price, base_price * 1.5)

            open_price = current_price
            close_price = new_price

            # Wide spreads in high volatility
            high_extra = np.random.uniform(0.01, 0.03)
            low_extra = np.random.uniform(0.01, 0.03)

            high = max(open_price, close_price) * (1 + high_extra)
            low = min(open_price, close_price) * (1 - low_extra)

            # High volatility = high volume
            volume = np.random.uniform(50000, 200000)

            data.append(
                {
                    "timestamp": timestamp,
                    "open": round(open_price, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "close": round(close_price, 2),
                    "volume": int(volume),
                }
            )

            current_price = close_price

        return pd.DataFrame(data)

    @staticmethod
    def generate_consolidation_scenario(
        duration_days: int = 14, center_price: float = 48000.0, range_pct: float = 3.0
    ) -> pd.DataFrame:
        """Generate sideways consolidation scenario."""

        points_per_day = 24  # 1-hour candles
        total_points = duration_days * points_per_day

        start_date = datetime(2024, 5, 1)
        timestamps = [start_date + timedelta(hours=i) for i in range(total_points)]

        # Define consolidation range
        upper_bound = center_price * (1 + range_pct / 100)
        lower_bound = center_price * (1 - range_pct / 100)

        data = []
        for i, timestamp in enumerate(timestamps):
            # Price tends to stay within range with occasional tests of boundaries
            if np.random.random() < 0.1:  # 10% chance of testing boundaries
                if np.random.random() < 0.5:
                    target_price = upper_bound * np.random.uniform(0.995, 1.002)
                else:
                    target_price = lower_bound * np.random.uniform(0.998, 1.005)
            else:
                # Stay within range
                target_price = np.random.uniform(lower_bound, upper_bound)

            # Small movements within consolidation
            open_price = target_price
            close_price = target_price * np.random.uniform(0.998, 1.002)

            high = max(open_price, close_price) * np.random.uniform(1.001, 1.005)
            low = min(open_price, close_price) * np.random.uniform(0.995, 0.999)

            # Lower volume during consolidation
            volume = np.random.uniform(5000, 20000)

            data.append(
                {
                    "timestamp": timestamp,
                    "open": round(open_price, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "close": round(close_price, 2),
                    "volume": int(volume),
                }
            )

        return pd.DataFrame(data)


# Pytest fixtures using the scenarios
@pytest.fixture
def bull_market_data():
    """Bull market scenario fixture."""
    return TradingScenarios.generate_bull_market_scenario(
        duration_days=20, start_price=40000, end_price=55000
    )


@pytest.fixture
def bear_market_data():
    """Bear market scenario fixture."""
    return TradingScenarios.generate_bear_market_scenario(
        duration_days=30, start_price=55000, end_price=35000
    )


@pytest.fixture
def flash_crash_data():
    """Flash crash scenario fixture."""
    return TradingScenarios.generate_flash_crash_scenario(
        normal_duration_hours=12,
        crash_duration_minutes=10,
        recovery_duration_hours=4,
        start_price=50000,
        crash_depth_pct=25.0,
    )


@pytest.fixture
def high_volatility_data():
    """High volatility scenario fixture."""
    return TradingScenarios.generate_high_volatility_scenario(
        duration_days=5, base_price=45000, volatility_factor=0.06
    )


@pytest.fixture
def consolidation_data():
    """Consolidation scenario fixture."""
    return TradingScenarios.generate_consolidation_scenario(
        duration_days=10, center_price=47000, range_pct=2.5
    )


@pytest.fixture
def multi_scenario_dataset():
    """Combined dataset with multiple market scenarios."""
    scenarios = TradingScenarios()

    # Generate different scenarios
    bull_data = scenarios.generate_bull_market_scenario(10, 40000, 50000)
    consolidation_data = scenarios.generate_consolidation_scenario(7, 50000, 2.0)
    bear_data = scenarios.generate_bear_market_scenario(15, 50000, 40000)
    flash_crash_data = scenarios.generate_flash_crash_scenario(6, 5, 2, 40000, 15.0)

    # Combine all scenarios chronologically
    combined_data = pd.concat(
        [bull_data, consolidation_data, bear_data, flash_crash_data], ignore_index=True
    )

    # Ensure timestamps are sequential
    start_time = datetime(2024, 1, 1)
    for i in range(len(combined_data)):
        combined_data.loc[i, "timestamp"] = start_time + timedelta(hours=i)

    return combined_data


@pytest.fixture
def realistic_trading_year():
    """Generate a full year of realistic trading data."""
    scenarios = TradingScenarios()
    year_data = []

    # Q1: Bull market
    q1_data = scenarios.generate_bull_market_scenario(90, 30000, 45000)
    year_data.append(q1_data)

    # Q2: Consolidation
    q2_data = scenarios.generate_consolidation_scenario(90, 45000, 5.0)
    year_data.append(q2_data)

    # Q3: Bear market with flash crash
    q3_bear = scenarios.generate_bear_market_scenario(60, 45000, 35000)
    q3_crash = scenarios.generate_flash_crash_scenario(12, 15, 6, 35000, 30.0)
    q3_recovery = scenarios.generate_bull_market_scenario(15, 24500, 35000)
    year_data.extend([q3_bear, q3_crash, q3_recovery])

    # Q4: High volatility into year end rally
    q4_vol = scenarios.generate_high_volatility_scenario(30, 35000, 0.04)
    q4_rally = scenarios.generate_bull_market_scenario(60, 35000, 50000)
    year_data.extend([q4_vol, q4_rally])

    # Combine all quarters
    combined_year = pd.concat(year_data, ignore_index=True)

    # Fix timestamps to span full year
    start_date = datetime(2024, 1, 1)
    for i in range(len(combined_year)):
        combined_year.loc[i, "timestamp"] = start_date + timedelta(hours=i)

    return combined_year
