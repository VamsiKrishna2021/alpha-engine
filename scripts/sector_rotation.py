"""
sector_rotation.py — Sector ETF Performance Heatmap
=====================================================
Calculates daily and weekly momentum for 11 sector ETFs.
"""
from __future__ import annotations

import logging
from typing import Dict, List

import pandas as pd
import yfinance as yf

from scripts.config import SECTOR_ETFS

logger = logging.getLogger("alpha_engine")


def calculate_sector_rotation() -> List[dict]:
    """
    Calculate daily % change and 5-day % change for all sector ETFs.
    Returns list sorted by daily performance (strongest first).
    """
    logger.info("═══ SECTOR ROTATION ═══")

    etf_tickers = list(SECTOR_ETFS.keys())

    try:
        data = yf.download(
            etf_tickers,
            period="1mo",
            interval="1d",
            auto_adjust=True,
            threads=True,
            progress=False,
        )
    except Exception as e:
        logger.error(f"Sector ETF download failed: {e}")
        return []

    if data.empty:
        return []

    sectors = []
    for etf in etf_tickers:
        try:
            if len(etf_tickers) == 1:
                close = data["Close"].dropna()
            else:
                close = data["Close"][etf].dropna()

            if len(close) < 6:
                continue

            last_close = float(close.iloc[-1])
            prev_close = float(close.iloc[-2])
            week_ago_close = float(close.iloc[-6]) if len(close) >= 6 else float(close.iloc[0])

            daily_chg = (last_close - prev_close) / prev_close * 100
            weekly_chg = (last_close - week_ago_close) / week_ago_close * 100

            sectors.append({
                "etf": etf,
                "name": SECTOR_ETFS[etf],
                "price": round(last_close, 2),
                "daily_chg": round(daily_chg, 2),
                "weekly_chg": round(weekly_chg, 2),
            })
        except (KeyError, IndexError) as e:
            logger.warning(f"Sector {etf}: {e}")
            continue

    # Sort by daily change descending
    sectors.sort(key=lambda x: x["daily_chg"], reverse=True)

    # Add rank
    for i, s in enumerate(sectors):
        s["rank"] = i + 1

    for s in sectors:
        sign_d = "+" if s["daily_chg"] >= 0 else ""
        sign_w = "+" if s["weekly_chg"] >= 0 else ""
        logger.info(
            f"  #{s['rank']} {s['etf']} ({s['name']}): "
            f"Day {sign_d}{s['daily_chg']:.2f}% | Week {sign_w}{s['weekly_chg']:.2f}%"
        )

    return sectors


def sector_color(change_pct: float) -> str:
    """Return a CSS color based on the magnitude of change."""
    if change_pct >= 2.0:
        return "#00c853"  # strong green
    elif change_pct >= 1.0:
        return "#4caf50"  # medium green
    elif change_pct >= 0.25:
        return "#81c784"  # light green
    elif change_pct >= -0.25:
        return "#9e9e9e"  # neutral gray
    elif change_pct >= -1.0:
        return "#ef9a9a"  # light red
    elif change_pct >= -2.0:
        return "#ef5350"  # medium red
    else:
        return "#c62828"  # strong red
