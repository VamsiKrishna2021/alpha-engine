"""
test_utils.py — Utility Function Tests
========================================
"""
import os
import json
import pytest
import tempfile
import pandas as pd

from scripts.utils import (
    format_number,
    pct_change_str,
    regime_label,
    regime_color,
    sepa_verdict,
    today_str,
    save_json,
    load_json,
    append_csv,
)


class TestFormatNumber:
    def test_trillion(self):
        assert format_number(2.5e12) == "$2.5T"

    def test_billion(self):
        assert format_number(150e9) == "$150.0B"

    def test_million(self):
        assert format_number(42e6) == "$42.0M"

    def test_thousand(self):
        assert format_number(8500) == "$8.5K"

    def test_small(self):
        assert format_number(42.567) == "42.57"

    def test_zero(self):
        assert format_number(0) == "0.00"


class TestPctChangeStr:
    def test_positive(self):
        assert pct_change_str(3.45) == "+3.45%"

    def test_negative(self):
        assert pct_change_str(-2.10) == "-2.10%"

    def test_zero(self):
        assert pct_change_str(0) == "+0.00%"


class TestRegimeLabel:
    def test_full_offense(self):
        assert regime_label(85) == "FULL OFFENSE"
        assert regime_label(100) == "FULL OFFENSE"
        assert regime_label(80) == "FULL OFFENSE"

    def test_selective(self):
        assert regime_label(79) == "SELECTIVE"
        assert regime_label(50) == "SELECTIVE"
        assert regime_label(65) == "SELECTIVE"

    def test_defensive(self):
        assert regime_label(49) == "DEFENSIVE"
        assert regime_label(30) == "DEFENSIVE"
        assert regime_label(40) == "DEFENSIVE"

    def test_capital_preservation(self):
        assert regime_label(29) == "CAPITAL PRESERVATION"
        assert regime_label(0) == "CAPITAL PRESERVATION"
        assert regime_label(10) == "CAPITAL PRESERVATION"


class TestRegimeColor:
    def test_full_offense_green(self):
        assert regime_color(85) == "#00e676"

    def test_selective_yellow(self):
        assert regime_color(65) == "#ffeb3b"

    def test_defensive_orange(self):
        assert regime_color(40) == "#ff9800"

    def test_preservation_red(self):
        assert regime_color(10) == "#ef5350"


class TestSepaVerdict:
    def test_actionable(self):
        text, css = sepa_verdict(80)
        assert "ACTIONABLE" in text
        assert css == "badge-green"

    def test_watchlist(self):
        text, css = sepa_verdict(60)
        assert "WATCHLIST" in text
        assert css == "badge-yellow"

    def test_avoid(self):
        text, css = sepa_verdict(35)
        assert "AVOID" in text
        assert css == "badge-orange"

    def test_no(self):
        text, css = sepa_verdict(10)
        assert "NO" in text
        assert css == "badge-red"

    def test_boundary_75(self):
        text, _ = sepa_verdict(75)
        assert "ACTIONABLE" in text

    def test_boundary_50(self):
        text, _ = sepa_verdict(50)
        assert "WATCHLIST" in text

    def test_boundary_25(self):
        text, _ = sepa_verdict(25)
        assert "AVOID" in text


class TestTodayStr:
    def test_format(self):
        result = today_str()
        assert len(result) == 10
        assert result[4] == "-" and result[7] == "-"


class TestJsonHelpers:
    def test_save_and_load(self, tmp_path):
        data = {"key": "value", "num": 42}
        path = str(tmp_path / "test.json")
        save_json(data, path)
        loaded = load_json(path)
        assert loaded["key"] == "value"
        assert loaded["num"] == 42

    def test_load_missing_file(self):
        result = load_json("/nonexistent/file.json")
        assert result == {}


class TestAppendCsv:
    def test_creates_new_file(self, tmp_path):
        path = str(tmp_path / "test.csv")
        append_csv(path, {"a": 1, "b": 2})
        df = pd.read_csv(path)
        assert len(df) == 1
        assert df.iloc[0]["a"] == 1

    def test_appends_to_existing(self, tmp_path):
        path = str(tmp_path / "test.csv")
        append_csv(path, {"a": 1, "b": 2})
        append_csv(path, {"a": 3, "b": 4})
        df = pd.read_csv(path)
        assert len(df) == 2

    def test_max_rows_trims(self, tmp_path):
        path = str(tmp_path / "test.csv")
        for i in range(10):
            append_csv(path, {"val": i}, max_rows=5)
        df = pd.read_csv(path)
        assert len(df) == 5
        assert df.iloc[-1]["val"] == 9  # Last row is most recent
