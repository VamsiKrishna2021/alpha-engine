"""
config.py — Alpha Engine Central Configuration
================================================
All constants, thresholds, universe lists, and secrets.
Reads from environment variables for GitHub Actions secrets support.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List


def _env(key: str, default: str) -> str:
    val = os.getenv(key, default)
    return val if val else default


def _env_float(key: str, default: str) -> float:
    val = _env(key, default)
    try:
        return float(val)
    except (ValueError, TypeError):
        return float(default)


def _env_int(key: str, default: str) -> int:
    val = _env(key, default)
    try:
        return int(val)
    except (ValueError, TypeError):
        return int(default)


# ═══════════════════════════════════════════════════════════════════
#  SECTOR ETFs, BENCHMARKS, MACRO
# ═══════════════════════════════════════════════════════════════════

SECTOR_ETFS = {
    "XLK": "Technology",
    "XLV": "Healthcare",
    "XLF": "Financials",
    "XLY": "Consumer Disc.",
    "XLP": "Consumer Staples",
    "XLE": "Energy",
    "XLI": "Industrials",
    "XLB": "Materials",
    "XLU": "Utilities",
    "XLRE": "Real Estate",
    "XLC": "Communication",
}

BENCHMARKS = ["SPY", "QQQ", "IWM"]

MACRO_TICKERS = ["^VIX", "^TNX", "DX-Y.NYB", "GLD", "USO"]

# S&P 500 representative ticker list for breadth calculations
# We fetch this dynamically from Wikipedia, but keep a fallback
SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"


# ═══════════════════════════════════════════════════════════════════
#  THRESHOLDS
# ═══════════════════════════════════════════════════════════════════

@dataclass
class AlphaConfig:
    """All tunables in one place — env vars override defaults."""

    # ── Regime thresholds ─────────────────────────────────────────
    REGIME_FULL_OFFENSE: int = 80
    REGIME_SELECTIVE: int = 50
    REGIME_DEFENSIVE: int = 30

    # ── SEPA thresholds ───────────────────────────────────────────
    SEPA_ACTIONABLE: int = 75
    SEPA_WATCHLIST: int = 50

    # ── Position sizing ───────────────────────────────────────────
    MAX_POSITION_PCT: float = _env_float("MAX_POSITION_PCT", "0.08")
    MAX_SECTOR_PCT: float = _env_float("MAX_SECTOR_PCT", "0.30")
    RISK_PER_TRADE_FULL: float = _env_float("RISK_PER_TRADE_FULL", "0.01")
    RISK_PER_TRADE_SELECTIVE: float = _env_float("RISK_PER_TRADE_SELECTIVE", "0.0075")
    RISK_PER_TRADE_DEFENSIVE: float = _env_float("RISK_PER_TRADE_DEFENSIVE", "0.005")
    TIME_STOP_DAYS: int = _env_int("TIME_STOP_DAYS", "15")
    ACCOUNT_EQUITY: float = _env_float("ACCOUNT_EQUITY", "50000")

    # ── Universe pre-filter ───────────────────────────────────────
    PREFILTER_MIN_PRICE: float = _env_float("PREFILTER_MIN_PRICE", "5.0")
    PREFILTER_MAX_PRICE: float = _env_float("PREFILTER_MAX_PRICE", "10000.0")
    PREFILTER_MIN_VOLUME: int = _env_int("PREFILTER_MIN_VOLUME", "500000")

    # ── Performance tuning ────────────────────────────────────────
    BATCH_SIZE: int = _env_int("BATCH_SIZE", "50")
    MAX_WORKERS: int = _env_int("MAX_WORKERS", "8")
    SLEEP_BETWEEN_BATCHES: float = _env_float("SLEEP_BETWEEN_BATCHES", "0.5")

    # ── Data source API keys (optional fallbacks) ─────────────────
    ALPHAVANTAGE_API_KEY: str = _env("ALPHAVANTAGE_API_KEY", "")
    FINNHUB_API_KEY: str = _env("FINNHUB_API_KEY", "")

    # ── Email alerts (optional) ───────────────────────────────────
    EMAIL_SENDER: str = _env("EMAIL_SENDER", "")
    EMAIL_PASSWORD: str = _env("EMAIL_PASSWORD", "")
    EMAIL_TO: str = _env("EMAIL_TO", "")

    # ── Telegram alerts (optional) ────────────────────────────────
    TELEGRAM_BOT_TOKEN: str = _env("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = _env("TELEGRAM_CHAT_ID", "")

    # ── Output paths ──────────────────────────────────────────────
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    OUTPUT_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
    TEMPLATE_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

    # ── Dashboard config ──────────────────────────────────────────
    TOP_STOCKS_DISPLAY: int = 14
    BREADTH_HISTORY_DAYS: int = 60
    BREADTH_TABLE_ROWS: int = 15
    TOP_GAINERS_LOSERS: int = 10


# Module-level singleton
CFG = AlphaConfig()
