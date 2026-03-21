"""
test_sepa_scanner.py — SEPA Scanner Scoring Tests
===================================================
Tests each of the 7 SEPA criteria scoring functions with edge cases.
"""
import pytest
import numpy as np
import pandas as pd

from scripts.sepa_scanner import (
    score_52wk_high,
    score_52wk_low,
    score_price_action,
    score_vcp,
    score_liquidity,
    score_stage,
)


def make_close_series(prices):
    """Helper: create a pd.Series of closing prices."""
    return pd.Series(prices, dtype=float)


def make_ohlcv_df(n=250, base_price=100.0, trend=0.001, volatility=0.02):
    """Helper: create a synthetic OHLCV DataFrame."""
    np.random.seed(42)
    closes = [base_price]
    for i in range(1, n):
        change = np.random.normal(trend, volatility)
        closes.append(closes[-1] * (1 + change))

    closes = np.array(closes)
    opens = closes * (1 + np.random.normal(0, 0.005, n))
    highs = np.maximum(opens, closes) * (1 + abs(np.random.normal(0, 0.01, n)))
    lows = np.minimum(opens, closes) * (1 - abs(np.random.normal(0, 0.01, n)))
    volumes = np.random.uniform(500000, 5000000, n)

    df = pd.DataFrame({
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Volume": volumes,
    })
    return df


# ═══════════════════════════════════════════════════════════════
#  CRITERION 1: 52-Week High Proximity
# ═══════════════════════════════════════════════════════════════

class TestScore52WkHigh:
    def test_at_52wk_high(self):
        """Stock at 52-week high gets max score."""
        prices = list(range(50, 100)) + [99]  # 99 is near high of 99
        score, detail = score_52wk_high(make_close_series(prices))
        assert score == 15

    def test_within_5pct(self):
        prices = list(range(50, 100)) + [96]  # 96 is ~3% below 99
        score, _ = score_52wk_high(make_close_series(prices))
        assert score == 15

    def test_within_15pct(self):
        prices = list(range(50, 100)) + [85]  # ~14% below 99
        score, _ = score_52wk_high(make_close_series(prices))
        assert score == 10

    def test_within_25pct(self):
        prices = list(range(50, 100)) + [76]  # ~23% below 99
        score, _ = score_52wk_high(make_close_series(prices))
        assert score == 5

    def test_far_from_high(self):
        prices = list(range(50, 100)) + [50]  # ~49% below 99
        score, _ = score_52wk_high(make_close_series(prices))
        assert score == 0

    def test_insufficient_data(self):
        score, detail = score_52wk_high(make_close_series([100, 101]))
        assert score == 0
        assert "Insufficient" in detail


# ═══════════════════════════════════════════════════════════════
#  CRITERION 2: 52-Week Low Distance
# ═══════════════════════════════════════════════════════════════

class TestScore52WkLow:
    def test_far_above_low(self):
        """Stock 120% above 52-week low gets max score."""
        prices = [50] + list(range(51, 160))  # Low=50, current=159 → 218% above
        score, _ = score_52wk_low(make_close_series(prices))
        assert score == 15

    def test_50pct_above(self):
        prices = [50] * 20 + list(range(51, 80)) * 2  # Low=50, current=79 → 58% above
        score, _ = score_52wk_low(make_close_series(prices))
        assert score == 10

    def test_35pct_above(self):
        prices = [50] * 20 + list(range(51, 70)) * 2  # Low=50, current=69 → 38% above
        score, _ = score_52wk_low(make_close_series(prices))
        assert score == 5

    def test_close_to_low(self):
        prices = [50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 55] * 6  # near low, 72 bars
        score, _ = score_52wk_low(make_close_series(prices))
        assert score <= 5


# ═══════════════════════════════════════════════════════════════
#  CRITERION 4: Intraday Price Action
# ═══════════════════════════════════════════════════════════════

class TestScorePriceAction:
    def test_strong_bullish_close(self):
        """Bullish candle closing in top 25% of range."""
        df = pd.DataFrame([{"Open": 100, "High": 110, "Low": 95, "Close": 109, "Volume": 1e6}])
        score, detail = score_price_action(df)
        assert score == 10
        assert "Strong" in detail or "top 25" in detail

    def test_bullish_upper_half(self):
        df = pd.DataFrame([{"Open": 100, "High": 110, "Low": 95, "Close": 105, "Volume": 1e6}])
        score, _ = score_price_action(df)
        assert score == 7

    def test_bearish_upper_half(self):
        df = pd.DataFrame([{"Open": 105, "High": 110, "Low": 95, "Close": 104, "Volume": 1e6}])
        score, _ = score_price_action(df)
        assert score == 3

    def test_weak_close(self):
        df = pd.DataFrame([{"Open": 105, "High": 110, "Low": 95, "Close": 97, "Volume": 1e6}])
        score, _ = score_price_action(df)
        assert score == 0

    def test_doji(self):
        df = pd.DataFrame([{"Open": 100, "High": 100, "Low": 100, "Close": 100, "Volume": 1e6}])
        score, _ = score_price_action(df)
        assert score == 0

    def test_empty_df(self):
        score, _ = score_price_action(pd.DataFrame())
        assert score == 0


# ═══════════════════════════════════════════════════════════════
#  CRITERION 5: VCP / Volatility Contraction
# ═══════════════════════════════════════════════════════════════

class TestScoreVcp:
    def test_tight_range(self):
        """Very tight range compared to 20-day average → 10 pts."""
        df = make_ohlcv_df(30, volatility=0.03)
        # Make the last day very tight
        df.iloc[-1, df.columns.get_loc("High")] = df.iloc[-1]["Close"] * 1.001
        df.iloc[-1, df.columns.get_loc("Low")] = df.iloc[-1]["Close"] * 0.999
        score, detail = score_vcp(df)
        assert score >= 7  # Should be high due to very tight last bar

    def test_expanding_range(self):
        """Wide range relative to average → 0 pts."""
        df = make_ohlcv_df(30, volatility=0.01)
        # Make the last day very wide
        df.iloc[-1, df.columns.get_loc("High")] = df.iloc[-1]["Close"] * 1.10
        df.iloc[-1, df.columns.get_loc("Low")] = df.iloc[-1]["Close"] * 0.90
        score, _ = score_vcp(df)
        assert score == 0

    def test_insufficient_data(self):
        score, _ = score_vcp(make_ohlcv_df(10))
        assert score == 0


# ═══════════════════════════════════════════════════════════════
#  CRITERION 6: Liquidity & Volume
# ═══════════════════════════════════════════════════════════════

class TestScoreLiquidity:
    def test_institutional_volume(self):
        """$50M+ daily dollar volume → 15 pts."""
        df = make_ohlcv_df(60, base_price=200)
        df["Volume"] = 1_000_000  # 200 * 1M = $200M/day
        score, detail = score_liquidity(df)
        assert score == 15
        assert "institutional" in detail.lower() or "Excellent" in detail

    def test_good_volume(self):
        df = make_ohlcv_df(60, base_price=50)
        df["Volume"] = 500_000  # 50 * 500K = $25M/day
        score, _ = score_liquidity(df)
        assert score == 10

    def test_adequate_volume(self):
        df = make_ohlcv_df(60, base_price=10)
        df["Volume"] = 500_000  # 10 * 500K = $5M/day
        score, _ = score_liquidity(df)
        assert score == 5

    def test_thin_volume(self):
        df = make_ohlcv_df(60, base_price=5)
        df["Volume"] = 50_000  # 5 * 50K = $250K/day
        score, _ = score_liquidity(df)
        assert score == 0

    def test_insufficient_data(self):
        score, _ = score_liquidity(make_ohlcv_df(20))
        assert score == 0


# ═══════════════════════════════════════════════════════════════
#  CRITERION 7: Weinstein Stage Analysis
# ═══════════════════════════════════════════════════════════════

class TestScoreStage:
    def test_stage2_uptrend(self):
        """Price above rising 150 SMA → Stage 2, 20 pts."""
        # Strong uptrend
        df = make_ohlcv_df(250, base_price=50, trend=0.003, volatility=0.01)
        score, stage, _ = score_stage(df)
        assert score == 20
        assert stage == "Stage 2"

    def test_stage4_downtrend(self):
        """Price below declining 150 SMA → Stage 4, 0 pts."""
        df = make_ohlcv_df(250, base_price=200, trend=-0.003, volatility=0.01)
        score, stage, _ = score_stage(df)
        assert score == 0
        assert stage in ("Stage 4", "Stage 3")

    def test_insufficient_data(self):
        score, stage, detail = score_stage(make_ohlcv_df(100))
        assert score == 0
        assert "Insufficient" in detail


# ═══════════════════════════════════════════════════════════════
#  SCORE RANGE VALIDATION
# ═══════════════════════════════════════════════════════════════

class TestScoreRanges:
    """Ensure all scores are within their defined max."""

    def test_52wk_high_max_15(self):
        prices = list(range(50, 300))
        score, _ = score_52wk_high(make_close_series(prices))
        assert 0 <= score <= 15

    def test_52wk_low_max_15(self):
        prices = [10] + list(range(11, 300))
        score, _ = score_52wk_low(make_close_series(prices))
        assert 0 <= score <= 15

    def test_price_action_max_10(self):
        df = make_ohlcv_df(5)
        score, _ = score_price_action(df)
        assert 0 <= score <= 10

    def test_vcp_max_10(self):
        df = make_ohlcv_df(30)
        score, _ = score_vcp(df)
        assert 0 <= score <= 10

    def test_liquidity_max_15(self):
        df = make_ohlcv_df(60)
        score, _ = score_liquidity(df)
        assert 0 <= score <= 15

    def test_stage_max_20(self):
        df = make_ohlcv_df(250)
        score, _, _ = score_stage(df)
        assert 0 <= score <= 20
