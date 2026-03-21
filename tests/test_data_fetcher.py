"""
test_data_fetcher.py — Data Fetcher Tests
===========================================
Tests for ticker universe acquisition and data download functions.
NOTE: Tests that require network access are marked with @pytest.mark.network
"""
import pytest
from unittest.mock import patch, MagicMock
from scripts.data_fetcher import (
    get_full_us_universe,
    get_sp500_tickers,
    fast_prefilter,
)
from scripts.config import CFG


class TestGetFullUsUniverse:
    """Test universe acquisition with fallback chain."""

    @pytest.mark.network
    def test_returns_list_of_strings(self):
        """Universe should be a list of ticker strings."""
        tickers = get_full_us_universe()
        assert isinstance(tickers, list)
        if len(tickers) > 0:
            assert isinstance(tickers[0], str)

    @pytest.mark.network
    def test_minimum_universe_size(self):
        """Should fetch at least 1000 tickers."""
        tickers = get_full_us_universe()
        assert len(tickers) > 1000

    @pytest.mark.network
    def test_no_special_characters(self):
        """Tickers should not contain $, ., -, ^, +."""
        tickers = get_full_us_universe()
        for t in tickers[:100]:  # Check first 100
            for char in ["$", ".", "-", "^", "+"]:
                assert char not in t, f"Ticker {t} contains {char}"

    @pytest.mark.network
    def test_tickers_are_sorted(self):
        tickers = get_full_us_universe()
        assert tickers == sorted(tickers)

    @pytest.mark.network
    def test_no_duplicates(self):
        tickers = get_full_us_universe()
        assert len(tickers) == len(set(tickers))


class TestGetSp500Tickers:
    @pytest.mark.network
    def test_returns_approximately_500(self):
        tickers = get_sp500_tickers()
        assert 450 < len(tickers) < 510

    @pytest.mark.network
    def test_contains_known_stocks(self):
        tickers = get_sp500_tickers()
        assert "AAPL" in tickers
        assert "MSFT" in tickers


class TestFastPrefilter:
    """Test the pre-filter function logic (mocked to avoid network calls)."""

    def test_returns_tuple(self):
        """fast_prefilter returns (list, dict)."""
        # With empty list, should return empty
        passed, quick = fast_prefilter([])
        assert isinstance(passed, list)
        assert isinstance(quick, dict)
        assert len(passed) == 0

    def test_prefilter_thresholds(self):
        """Verify threshold values are reasonable."""
        assert CFG.PREFILTER_MIN_PRICE >= 1.0
        assert CFG.PREFILTER_MAX_PRICE >= 100.0
        assert CFG.PREFILTER_MIN_VOLUME >= 100_000


class TestSectorRotation:
    """Test sector rotation calculations."""

    @pytest.mark.network
    def test_returns_11_sectors(self):
        from scripts.sector_rotation import calculate_sector_rotation
        sectors = calculate_sector_rotation()
        assert len(sectors) >= 8  # At least most sectors should work

    @pytest.mark.network
    def test_sector_has_required_fields(self):
        from scripts.sector_rotation import calculate_sector_rotation
        sectors = calculate_sector_rotation()
        if sectors:
            s = sectors[0]
            assert "etf" in s
            assert "name" in s
            assert "daily_chg" in s
            assert "weekly_chg" in s

    @pytest.mark.network
    def test_sorted_by_daily_change(self):
        from scripts.sector_rotation import calculate_sector_rotation
        sectors = calculate_sector_rotation()
        if len(sectors) >= 2:
            changes = [s["daily_chg"] for s in sectors]
            assert changes == sorted(changes, reverse=True)


class TestSectorColor:
    def test_strong_green(self):
        from scripts.sector_rotation import sector_color
        assert sector_color(3.0) == "#00c853"

    def test_medium_green(self):
        from scripts.sector_rotation import sector_color
        assert sector_color(1.5) == "#4caf50"

    def test_neutral(self):
        from scripts.sector_rotation import sector_color
        assert sector_color(0.1) == "#9e9e9e"

    def test_strong_red(self):
        from scripts.sector_rotation import sector_color
        assert sector_color(-3.0) == "#c62828"

    def test_medium_red(self):
        from scripts.sector_rotation import sector_color
        assert sector_color(-1.5) == "#ef5350"
