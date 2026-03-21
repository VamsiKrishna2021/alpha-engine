"""
test_config.py — Configuration Tests
======================================
Tests for config.py: env var handling, thresholds, defaults.
"""
import os
import pytest


class TestEnvVarHandling:
    """Test that config reads env vars with fallback to defaults."""

    def test_default_account_equity(self):
        """ACCOUNT_EQUITY defaults to 50000 when env var not set."""
        os.environ.pop("ACCOUNT_EQUITY", None)
        # Re-import to pick up fresh env
        import importlib
        import scripts.config as cfg_mod
        importlib.reload(cfg_mod)
        assert cfg_mod.CFG.ACCOUNT_EQUITY == 50000.0

    def test_custom_account_equity(self):
        """ACCOUNT_EQUITY reads from env var."""
        os.environ["ACCOUNT_EQUITY"] = "100000"
        import importlib
        import scripts.config as cfg_mod
        importlib.reload(cfg_mod)
        assert cfg_mod.CFG.ACCOUNT_EQUITY == 100000.0
        os.environ.pop("ACCOUNT_EQUITY", None)

    def test_empty_env_var_uses_default(self):
        """Empty string env var falls back to default."""
        os.environ["ACCOUNT_EQUITY"] = ""
        import importlib
        import scripts.config as cfg_mod
        importlib.reload(cfg_mod)
        assert cfg_mod.CFG.ACCOUNT_EQUITY == 50000.0
        os.environ.pop("ACCOUNT_EQUITY", None)

    def test_invalid_env_var_uses_default(self):
        """Non-numeric env var falls back to default."""
        os.environ["ACCOUNT_EQUITY"] = "not_a_number"
        import importlib
        import scripts.config as cfg_mod
        importlib.reload(cfg_mod)
        assert cfg_mod.CFG.ACCOUNT_EQUITY == 50000.0
        os.environ.pop("ACCOUNT_EQUITY", None)


class TestThresholds:
    """Test all threshold values are correctly defined."""

    def test_regime_thresholds_order(self):
        from scripts.config import CFG
        assert CFG.REGIME_FULL_OFFENSE > CFG.REGIME_SELECTIVE > CFG.REGIME_DEFENSIVE

    def test_regime_full_offense(self):
        from scripts.config import CFG
        assert CFG.REGIME_FULL_OFFENSE == 80

    def test_regime_selective(self):
        from scripts.config import CFG
        assert CFG.REGIME_SELECTIVE == 50

    def test_regime_defensive(self):
        from scripts.config import CFG
        assert CFG.REGIME_DEFENSIVE == 30

    def test_sepa_actionable_above_watchlist(self):
        from scripts.config import CFG
        assert CFG.SEPA_ACTIONABLE > CFG.SEPA_WATCHLIST

    def test_risk_per_trade_decreasing(self):
        """Risk per trade decreases as regime gets more defensive."""
        from scripts.config import CFG
        assert CFG.RISK_PER_TRADE_FULL > CFG.RISK_PER_TRADE_SELECTIVE > CFG.RISK_PER_TRADE_DEFENSIVE

    def test_max_position_pct(self):
        from scripts.config import CFG
        assert CFG.MAX_POSITION_PCT == 0.08

    def test_max_sector_pct(self):
        from scripts.config import CFG
        assert CFG.MAX_SECTOR_PCT == 0.30


class TestSectorETFs:
    """Test sector ETF definitions."""

    def test_eleven_sectors(self):
        from scripts.config import SECTOR_ETFS
        assert len(SECTOR_ETFS) == 11

    def test_all_spdr_etfs_present(self):
        from scripts.config import SECTOR_ETFS
        expected = {"XLK", "XLV", "XLF", "XLY", "XLP", "XLE", "XLI", "XLB", "XLU", "XLRE", "XLC"}
        assert set(SECTOR_ETFS.keys()) == expected

    def test_sector_names_not_empty(self):
        from scripts.config import SECTOR_ETFS
        for etf, name in SECTOR_ETFS.items():
            assert len(name) > 0, f"Sector name empty for {etf}"


class TestBenchmarks:
    """Test benchmark definitions."""

    def test_benchmarks_contain_spy(self):
        from scripts.config import BENCHMARKS
        assert "SPY" in BENCHMARKS

    def test_benchmarks_contain_qqq(self):
        from scripts.config import BENCHMARKS
        assert "QQQ" in BENCHMARKS
