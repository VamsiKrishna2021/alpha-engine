"""
breadth_calculator.py — Market Breadth Metrics
================================================
Calculates daily A/D, % above various SMAs, and flags thresholds.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

from scripts.config import CFG
from scripts.utils import append_csv

logger = logging.getLogger("alpha_engine")


def calculate_breadth(
    history_cache: Dict[str, pd.DataFrame],
    quick_data: Dict[str, dict],
) -> dict:
    """
    Calculate all breadth metrics from the history cache.

    Returns dict with all breadth data + threshold flags.
    """
    logger.info(f"═══ BREADTH CALCULATION ({len(history_cache)} stocks) ═══")

    adv = 0
    dec = 0
    up4pct = 0
    dn4pct = 0
    above_10d = 0
    above_20d = 0
    above_40d = 0
    total_with_enough_data = 0

    spy_close = 0.0
    spy_chg_pct = 0.0

    for ticker, df in history_cache.items():
        try:
            if len(df) < 40:
                continue

            close = df["Close"]
            last_close = float(close.iloc[-1])

            # A/D: today's change
            if len(close) >= 2:
                prev_close = float(close.iloc[-2])
                daily_chg = (last_close - prev_close) / prev_close * 100

                if daily_chg > 0:
                    adv += 1
                else:
                    dec += 1

                # 4% movers
                if daily_chg > 4:
                    up4pct += 1
                elif daily_chg < -4:
                    dn4pct += 1

            # % above SMAs
            sma10 = float(close.rolling(10).mean().iloc[-1])
            sma20 = float(close.rolling(20).mean().iloc[-1])
            sma40 = float(close.rolling(40).mean().iloc[-1])

            total_with_enough_data += 1

            if last_close > sma10:
                above_10d += 1
            if last_close > sma20:
                above_20d += 1
            if last_close > sma40:
                above_40d += 1

        except Exception:
            continue

    # SPY data
    try:
        spy_data = yf.download("SPY", period="5d", auto_adjust=True, progress=False)
        if isinstance(spy_data.columns, pd.MultiIndex):
            spy_data.columns = spy_data.columns.droplevel(1)
        if not spy_data.empty and len(spy_data) >= 2:
            spy_close = float(spy_data["Close"].iloc[-1])
            spy_prev = float(spy_data["Close"].iloc[-2])
            spy_chg_pct = (spy_close - spy_prev) / spy_prev * 100
    except Exception as e:
        logger.warning(f"SPY data fetch failed: {e}")

    # Calculate percentages
    total = max(total_with_enough_data, 1)
    pct_above_10d = round(above_10d / total * 100, 1)
    pct_above_20d = round(above_20d / total * 100, 1)
    pct_above_40d = round(above_40d / total * 100, 1)

    ad_ratio = round(adv / max(dec, 1), 2)

    # Threshold flags
    flags = []
    if pct_above_20d < 15:
        flags.append({"type": "WASHOUT", "msg": "WASHOUT — potential reversal zone", "color": "#ffeb3b"})
    if pct_above_20d > 70:
        flags.append({"type": "EXTENDED", "msg": "EXTENDED — tighten stops", "color": "#ff9800"})
    if dn4pct > 200:
        flags.append({"type": "CAPITULATION", "msg": "CAPITULATION DAY", "color": "#ef5350"})
    if up4pct > 200:
        flags.append({"type": "EXPLOSION", "msg": "BREADTH EXPLOSION", "color": "#00e676"})

    # Check for breadth thrust (cross above 30% from below within 2 days)
    breadth_hist_path = os.path.join(CFG.DATA_DIR, "breadth_history.csv")
    if os.path.exists(breadth_hist_path):
        try:
            hist = pd.read_csv(breadth_hist_path)
            if len(hist) >= 3:
                recent_pct20 = hist["pct_above_20d"].tail(3).tolist()
                if len(recent_pct20) >= 2:
                    if recent_pct20[-2] < 30 and pct_above_20d >= 30:
                        flags.append({
                            "type": "THRUST",
                            "msg": "BREADTH THRUST — %> 20D crossed above 30%",
                            "color": "#00e676",
                        })
        except Exception:
            pass

    breadth_data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "day_of_week": datetime.now().strftime("%A"),
        "adv": adv,
        "dec": dec,
        "ad_ratio": ad_ratio,
        "up4pct": up4pct,
        "dn4pct": dn4pct,
        "pct_above_10d": pct_above_10d,
        "pct_above_20d": pct_above_20d,
        "pct_above_40d": pct_above_40d,
        "spy_close": round(spy_close, 2),
        "spy_chg_pct": round(spy_chg_pct, 2),
        "total_stocks": total_with_enough_data,
        "flags": flags,
    }

    # Append to breadth_history.csv
    history_row = {
        "date": breadth_data["date"],
        "day_of_week": breadth_data["day_of_week"],
        "adv": adv,
        "dec": dec,
        "up4pct": up4pct,
        "dn4pct": dn4pct,
        "pct_above_10d": pct_above_10d,
        "pct_above_20d": pct_above_20d,
        "pct_above_40d": pct_above_40d,
        "spy_close": round(spy_close, 2),
        "spy_chg_pct": round(spy_chg_pct, 2),
    }
    append_csv(breadth_hist_path, history_row, max_rows=CFG.BREADTH_HISTORY_DAYS)

    logger.info(f"  Advancers: {adv} | Decliners: {dec} | A/D Ratio: {ad_ratio}")
    logger.info(f"  Up 4%+: {up4pct} | Down 4%+: {dn4pct}")
    logger.info(f"  %>10D: {pct_above_10d} | %>20D: {pct_above_20d} | %>40D: {pct_above_40d}")
    for flag in flags:
        logger.info(f"  FLAG: {flag['msg']}")

    return breadth_data


def get_breadth_history() -> List[dict]:
    """Load breadth history for dashboard display."""
    path = os.path.join(CFG.DATA_DIR, "breadth_history.csv")
    if not os.path.exists(path):
        return []
    try:
        df = pd.read_csv(path)
        return df.tail(CFG.BREADTH_TABLE_ROWS).to_dict("records")
    except Exception:
        return []
