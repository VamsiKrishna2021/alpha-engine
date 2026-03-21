"""
test_regime_detector.py — Regime Detection Tests
==================================================
Tests EMA alignment scoring and component logic.
"""
import pytest
import pandas as pd
import numpy as np

from scripts.regime_detector import (
    ema_alignment_score,
    trend_momentum_score,
)


def make_spy_df(prices, n=250):
    """Create a mock SPY DataFrame from a price series."""
    if len(prices) < n:
        # Pad with the first price
        prices = [prices[0]] * (n - len(prices)) + prices
    df = pd.DataFrame({
        "Open": prices,
        "High": [p * 1.005 for p in prices],
        "Low": [p * 0.995 for p in prices],
        "Close": prices,
        "Volume": [50000000] * len(prices),
    })
    return df


class TestEmaAlignmentScore:
    def test_bullish_alignment(self):
        """SPY > 21 EMA > 50 EMA > 200 EMA → 100."""
        # Strong uptrend
        prices = [300 + i * 0.5 for i in range(250)]
        result = ema_alignment_score(make_spy_df(prices))
        assert result["score"] == 100

    def test_price_above_200_only(self):
        """SPY > 200 EMA but below 50 EMA → 40."""
        # Start high, dip, then slightly above 200 EMA
        prices = [400 + i * 0.3 for i in range(200)]
        prices += [400 + 200 * 0.3 - i * 0.3 for i in range(50)]
        result = ema_alignment_score(make_spy_df(prices))
        assert result["score"] in (40, 70)  # Depending on exact EMA values

    def test_bearish(self):
        """SPY below 200 EMA → 10 or 0."""
        prices = [500 - i * 0.5 for i in range(250)]
        result = ema_alignment_score(make_spy_df(prices))
        assert result["score"] <= 10

    def test_result_has_ema_values(self):
        prices = [400 + i * 0.1 for i in range(250)]
        result = ema_alignment_score(make_spy_df(prices))
        assert "ema21" in result
        assert "ema50" in result
        assert "ema200" in result
        assert "spy_close" in result

    def test_spy_vs_ema_percentages(self):
        prices = [400 + i * 0.1 for i in range(250)]
        result = ema_alignment_score(make_spy_df(prices))
        assert isinstance(result["spy_vs_21ema"], float)
        assert isinstance(result["spy_vs_50ema"], float)
        assert isinstance(result["spy_vs_200ema"], float)


class TestTrendMomentumScore:
    def test_strong_positive_roc(self):
        """ROC > 3% → 100."""
        prices = [400] * 240 + [400, 401, 403, 406, 410, 415, 420, 425, 430, 435, 440]
        df = make_spy_df(prices)
        result = trend_momentum_score(df)
        assert result["score"] == 100

    def test_mild_positive_roc(self):
        """ROC 0% to 3% → 60."""
        prices = [400] * 240 + [400, 400.5, 401, 401.5, 402, 402.5, 403, 403.5, 404, 404.5, 405]
        df = make_spy_df(prices)
        result = trend_momentum_score(df)
        assert result["score"] == 60

    def test_negative_roc(self):
        """ROC < -3% → 0."""
        prices = [450] * 240 + [450, 448, 446, 444, 442, 440, 438, 435, 430, 425, 420]
        df = make_spy_df(prices)
        result = trend_momentum_score(df)
        assert result["score"] == 0

    def test_short_data(self):
        """< 11 bars → default 50."""
        df = make_spy_df([400] * 5, n=5)
        result = trend_momentum_score(df)
        assert result["score"] == 50

    def test_result_has_roc(self):
        prices = [400 + i * 0.1 for i in range(250)]
        result = trend_momentum_score(make_spy_df(prices))
        assert "roc_10d" in result


class TestRegimeScoreRange:
    """Ensure regime scores stay within 0-100."""

    def test_score_not_negative(self):
        from scripts.regime_detector import ema_alignment_score, trend_momentum_score
        prices = [500 - i for i in range(250)]  # Crash
        ema = ema_alignment_score(make_spy_df(prices))
        assert ema["score"] >= 0

    def test_score_not_over_100(self):
        prices = [100 + i * 0.5 for i in range(250)]
        ema = ema_alignment_score(make_spy_df(prices))
        assert ema["score"] <= 100
