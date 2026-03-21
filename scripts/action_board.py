"""
action_board.py — Daily Action Summary Generator
==================================================
Combines all modules into a single actionable daily summary.
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

from scripts.config import CFG
from scripts.utils import ensure_dirs, save_json, setup_logging
from scripts.data_fetcher import (
    get_full_us_universe,
    get_sp500_tickers,
    fast_prefilter,
    download_batch_ohlcv,
)
from scripts.regime_detector import detect_regime
from scripts.breadth_calculator import calculate_breadth, get_breadth_history
from scripts.sector_rotation import calculate_sector_rotation
from scripts.sepa_scanner import scan_universe, get_top_gainers_losers
from scripts.capital_allocator import get_deployment_model

import yfinance as yf
import pandas as pd

logger = logging.getLogger("alpha_engine")


def fetch_macro_kpis() -> list:
    """Fetch macro KPI data: SPY, QQQ, IWM, VIX, 10Y, DXY, Gold."""
    kpis = [
        {"ticker": "SPY", "name": "S&P 500"},
        {"ticker": "QQQ", "name": "NASDAQ 100"},
        {"ticker": "IWM", "name": "RUSSELL 2000"},
        {"ticker": "^VIX", "name": "VIX"},
        {"ticker": "^TNX", "name": "10Y YIELD"},
        {"ticker": "DX-Y.NYB", "name": "US DOLLAR"},
        {"ticker": "GLD", "name": "GOLD"},
    ]
    results = []
    for kpi in kpis:
        try:
            data = yf.download(kpi["ticker"], period="5d", auto_adjust=True, progress=False)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel(1)
            if not data.empty and len(data) >= 2:
                last = float(data["Close"].iloc[-1])
                prev = float(data["Close"].iloc[-2])
                chg = (last - prev) / prev * 100
                results.append({
                    "ticker": kpi["ticker"],
                    "name": kpi["name"],
                    "value": round(last, 2),
                    "change_pct": round(chg, 2),
                })
            else:
                results.append({"ticker": kpi["ticker"], "name": kpi["name"], "value": 0, "change_pct": 0})
        except Exception as e:
            logger.warning(f"Macro KPI {kpi['ticker']}: {e}")
            results.append({"ticker": kpi["ticker"], "name": kpi["name"], "value": 0, "change_pct": 0})
    return results


def run_daily_scan() -> dict:
    """
    Execute the full daily scan pipeline:
    1. Fetch ticker universe
    2. Pre-filter by price/volume
    3. Download history
    4. Run regime detection
    5. Calculate breadth
    6. Sector rotation
    7. SEPA scan
    8. Capital allocation model
    9. Generate action summary

    Returns the complete scan results dict.
    """
    setup_logging()
    ensure_dirs()

    start_time = time.time()
    logger.info("╔══════════════════════════════════════════════════╗")
    logger.info("║     ALPHA ENGINE — DAILY SCAN                    ║")
    logger.info(f"║     {datetime.now().strftime('%Y-%m-%d %H:%M:%S ET')}              ║")
    logger.info("╚══════════════════════════════════════════════════╝")

    # ── Step 1: Fetch Universe ────────────────────────────────────
    logger.info("─── STEP 1: Acquiring ticker universe ───")
    universe = get_full_us_universe()
    logger.info(f"Universe: {len(universe):,} tickers")

    # ── Step 2: Pre-filter ────────────────────────────────────────
    logger.info("─── STEP 2: Fast pre-filter (5-day price/volume) ───")
    filtered_tickers, quick_data = fast_prefilter(universe)
    logger.info(f"Pre-filter passed: {len(filtered_tickers):,} tickers")

    # ── Step 3: Download 1-year history ───────────────────────────
    logger.info("─── STEP 3: Downloading 1-year OHLCV history ───")
    history_cache = download_batch_ohlcv(filtered_tickers, period="1y", min_bars=50)
    logger.info(f"History cache: {len(history_cache):,} tickers")

    # ── Step 4: Regime Detection ──────────────────────────────────
    logger.info("─── STEP 4: Market regime detection ───")
    sp500 = get_sp500_tickers()
    regime = detect_regime(sp500)
    logger.info(f"Regime: {regime['regime_score']}/100 — {regime['label']}")

    # ── Step 5: Market Breadth ────────────────────────────────────
    logger.info("─── STEP 5: Market breadth calculation ───")
    breadth = calculate_breadth(history_cache, quick_data)
    breadth_history = get_breadth_history()

    # ── Step 6: Sector Rotation ───────────────────────────────────
    logger.info("─── STEP 6: Sector rotation heatmap ───")
    sectors = calculate_sector_rotation()

    # ── Step 7: SEPA Scan ─────────────────────────────────────────
    logger.info("─── STEP 7: SEPA universe scan ───")
    sepa_results = scan_universe(history_cache, quick_data)

    # Top gainers/losers
    gainers, losers = get_top_gainers_losers(quick_data, history_cache, n=CFG.TOP_GAINERS_LOSERS)

    # ── Step 8: Capital Allocation ────────────────────────────────
    logger.info("─── STEP 8: Capital allocation model ───")
    deployment = get_deployment_model(regime["regime_score"])
    logger.info(f"Deployment: {deployment['label']} — Risk/trade: {deployment['risk_per_trade_pct']}%")

    # ── Step 9: Macro KPIs ────────────────────────────────────────
    logger.info("─── STEP 9: Macro KPIs ───")
    macro_kpis = fetch_macro_kpis()
    logger.info(f"Macro KPIs: {len(macro_kpis)} fetched")

    # ── Step 10: Compile Results ──────────────────────────────────
    elapsed = round((time.time() - start_time) / 60, 1)
    logger.info(f"─── SCAN COMPLETE in {elapsed} minutes ───")

    results = {
        "scan_date": datetime.now().strftime("%Y-%m-%d"),
        "scan_time": datetime.now().strftime("%H:%M:%S ET"),
        "elapsed_minutes": elapsed,
        "universe_size": len(universe),
        "prefiltered_size": len(filtered_tickers),
        "scanned_size": len(history_cache),
        "macro_kpis": macro_kpis,
        "regime": regime,
        "breadth": breadth,
        "breadth_history": breadth_history,
        "sectors": sectors,
        "deployment": deployment,
        "top_stocks": sepa_results[:CFG.TOP_STOCKS_DISPLAY],
        "all_actionable": [r for r in sepa_results if r["score"] >= CFG.SEPA_ACTIONABLE],
        "all_watchlist": [r for r in sepa_results if CFG.SEPA_WATCHLIST <= r["score"] < CFG.SEPA_ACTIONABLE],
        "top_gainers": gainers,
        "top_losers": losers,
        "scan_stats": {
            "total_actionable": sum(1 for r in sepa_results if r["score"] >= 75),
            "total_watchlist": sum(1 for r in sepa_results if 50 <= r["score"] < 75),
            "total_avoid": sum(1 for r in sepa_results if r["score"] < 50),
        },
    }

    # Save results
    results_path = os.path.join(CFG.DATA_DIR, "scan_results.json")
    save_json(results, results_path)
    logger.info(f"Results saved to {results_path}")

    return results


if __name__ == "__main__":
    run_daily_scan()
