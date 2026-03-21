"""
single_stock_analyser.py — Deep SEPA Analysis for a Single Ticker
==================================================================
On-demand analysis with full criterion breakdown and chart data.
"""
from __future__ import annotations

import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd
import yfinance as yf

from scripts.sepa_scanner import (
    score_52wk_high,
    score_52wk_low,
    score_relative_strength,
    score_price_action,
    score_vcp,
    score_liquidity,
    score_stage,
)
from scripts.config import CFG

logger = logging.getLogger("alpha_engine")


def analyse_single_stock(ticker: str) -> Optional[dict]:
    """
    Run deep SEPA analysis on a single ticker.
    Returns comprehensive analysis dict or None on failure.
    """
    logger.info(f"═══ SINGLE STOCK ANALYSIS: {ticker} ═══")

    # Download 1 year of daily data
    try:
        df = yf.download(ticker, period="1y", auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        df = df.dropna()

        if df.empty or len(df) < 50:
            logger.error(f"{ticker}: Insufficient data ({len(df)} bars)")
            return None
    except Exception as e:
        logger.error(f"{ticker}: Download failed: {e}")
        return None

    # Download SPY for relative strength
    try:
        spy_df = yf.download("SPY", period="1y", auto_adjust=True, progress=False)
        if isinstance(spy_df.columns, pd.MultiIndex):
            spy_df.columns = spy_df.columns.droplevel(1)
        spy_close = spy_df["Close"]
    except Exception:
        spy_close = pd.Series()

    close = df["Close"]

    # Get ticker info
    try:
        info = yf.Ticker(ticker).info
        company_name = info.get("longName", info.get("shortName", ticker))
        sector = info.get("sector", "Unknown")
        industry = info.get("industry", "Unknown")
        market_cap = info.get("marketCap", 0)
        pe_ratio = info.get("trailingPE", None)
        forward_pe = info.get("forwardPE", None)
        eps = info.get("trailingEps", None)
        dividend_yield = info.get("dividendYield", None)
        beta = info.get("beta", None)
        avg_volume = info.get("averageVolume", 0)
        fifty_two_wk_high = info.get("fiftyTwoWeekHigh", 0)
        fifty_two_wk_low = info.get("fiftyTwoWeekLow", 0)
    except Exception:
        company_name = ticker
        sector = industry = "Unknown"
        market_cap = pe_ratio = forward_pe = eps = dividend_yield = beta = avg_volume = 0
        fifty_two_wk_high = fifty_two_wk_low = 0

    # ── Run all 7 SEPA criteria ──────────────────────────────────
    s1, d1 = score_52wk_high(close)
    s2, d2 = score_52wk_low(close)
    s3, rs_pct, d3 = score_relative_strength(close, spy_close)
    s4, d4 = score_price_action(df)
    s5, d5 = score_vcp(df)
    s6, d6 = score_liquidity(df)
    s7, stage, d7 = score_stage(df)

    total_score = s1 + s2 + s3 + s4 + s5 + s6 + s7

    # Verdict
    if total_score >= 75:
        verdict = "ACTIONABLE — LOOK FOR ENTRY"
        verdict_class = "badge-green"
    elif total_score >= 50:
        verdict = "WATCHLIST — WAIT FOR SETUP"
        verdict_class = "badge-yellow"
    elif total_score >= 25:
        verdict = "AVOID — WEAK STRUCTURE"
        verdict_class = "badge-orange"
    else:
        verdict = "NO — STAGE 4 DECLINE"
        verdict_class = "badge-red"

    # ── Technical indicators for chart ─────────────────────────────
    ema21 = close.ewm(span=21, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()
    sma150 = close.rolling(150).mean()
    sma200 = close.rolling(200).mean()

    # Volume analysis
    vol = df["Volume"]
    vol_sma50 = vol.rolling(50).mean()
    vol_ratio = float(vol.iloc[-1]) / float(vol_sma50.iloc[-1]) if float(vol_sma50.iloc[-1]) > 0 else 1

    # ATR
    high = df["High"]
    low = df["Low"]
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs(),
    ], axis=1).max(axis=1)
    atr14 = tr.rolling(14).mean()
    last_atr = float(atr14.iloc[-1]) if not atr14.empty else 0
    atr_pct = last_atr / float(close.iloc[-1]) * 100

    # Chart data (last 120 days for the chart)
    chart_data = []
    chart_df = df.tail(120)
    for idx, row in chart_df.iterrows():
        date_str = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)
        chart_data.append({
            "date": date_str,
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]),
        })

    # Moving average data for chart overlay
    ma_data = {
        "ema21": [round(float(v), 2) for v in ema21.tail(120).values if not np.isnan(v)],
        "ema50": [round(float(v), 2) for v in ema50.tail(120).values if not np.isnan(v)],
        "sma150": [round(float(v), 2) for v in sma150.tail(120).values if not np.isnan(v)],
        "sma200": [round(float(v), 2) for v in sma200.tail(120).values if not np.isnan(v)],
    }

    criteria_passed = sum(1 for s in [s1, s2, s3, s4, s5, s6, s7] if s > 0)

    result = {
        "ticker": ticker,
        "company_name": company_name,
        "sector": sector,
        "industry": industry,
        "market_cap": market_cap,
        "pe_ratio": pe_ratio,
        "forward_pe": forward_pe,
        "eps": eps,
        "dividend_yield": dividend_yield,
        "beta": beta,
        "avg_volume": avg_volume,
        "fifty_two_wk_high": fifty_two_wk_high,
        "fifty_two_wk_low": fifty_two_wk_low,
        "price": round(float(close.iloc[-1]), 2),
        "change_pct": round(
            (float(close.iloc[-1]) - float(close.iloc[-2])) / float(close.iloc[-2]) * 100, 2
        ) if len(close) >= 2 else 0,
        "score": total_score,
        "verdict": verdict,
        "verdict_class": verdict_class,
        "criteria_passed": f"{criteria_passed}/7",
        "stage": stage,
        "rs_percentile": rs_pct,
        "atr": round(last_atr, 2),
        "atr_pct": round(atr_pct, 2),
        "vol_ratio": round(vol_ratio, 2),
        "criteria": [
            {"name": "52-Week High Proximity", "score": s1, "max": 15, "detail": d1},
            {"name": "52-Week Low Distance", "score": s2, "max": 15, "detail": d2},
            {"name": "Relative Strength vs SPY", "score": s3, "max": 15, "detail": d3},
            {"name": "Intraday Price Action", "score": s4, "max": 10, "detail": d4},
            {"name": "Volatility Contraction (VCP)", "score": s5, "max": 10, "detail": d5},
            {"name": "Liquidity & Volume", "score": s6, "max": 15, "detail": d6},
            {"name": "Weinstein Stage Analysis", "score": s7, "max": 20, "detail": d7},
        ],
        "chart_data": chart_data,
        "ma_data": ma_data,
    }

    logger.info(f"  Score: {total_score}/100 — {verdict}")
    logger.info(f"  Stage: {stage} | RS%: {rs_pct} | ATR%: {atr_pct:.1f}")

    return result
