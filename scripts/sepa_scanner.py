"""
sepa_scanner.py — Minervini SEPA Scoring (0-100)
==================================================
7-criterion batch scanner for the entire US stock universe.
"""
from __future__ import annotations

import logging
import math
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

from scripts.config import CFG

logger = logging.getLogger("alpha_engine")


# ═══════════════════════════════════════════════════════════════════
#  CRITERION 1: 52-WEEK HIGH PROXIMITY (max 15 pts)
# ═══════════════════════════════════════════════════════════════════

def score_52wk_high(close: pd.Series) -> Tuple[int, str]:
    """Score proximity to 52-week high."""
    if len(close) < 50:
        return 0, "Insufficient data"

    current = float(close.iloc[-1])
    high_52 = float(close.tail(252).max()) if len(close) >= 252 else float(close.max())
    pct_from_high = (current - high_52) / high_52 * 100

    if pct_from_high >= -5:
        return 15, f"Within {abs(pct_from_high):.1f}% of 52WH"
    elif pct_from_high >= -15:
        return 10, f"{abs(pct_from_high):.1f}% below 52WH"
    elif pct_from_high >= -25:
        return 5, f"{abs(pct_from_high):.1f}% below 52WH"
    else:
        return 0, f"{abs(pct_from_high):.1f}% below 52WH"


# ═══════════════════════════════════════════════════════════════════
#  CRITERION 2: 52-WEEK LOW DISTANCE (max 15 pts)
# ═══════════════════════════════════════════════════════════════════

def score_52wk_low(close: pd.Series) -> Tuple[int, str]:
    """Score distance from 52-week low."""
    if len(close) < 50:
        return 0, "Insufficient data"

    current = float(close.iloc[-1])
    low_52 = float(close.tail(252).min()) if len(close) >= 252 else float(close.min())
    pct_above_low = (current - low_52) / low_52 * 100

    if pct_above_low > 100:
        return 15, f"{pct_above_low:.0f}% above 52WL"
    elif pct_above_low > 50:
        return 10, f"{pct_above_low:.0f}% above 52WL"
    elif pct_above_low > 30:
        return 5, f"{pct_above_low:.0f}% above 52WL"
    else:
        return 0, f"Only {pct_above_low:.0f}% above 52WL"


# ═══════════════════════════════════════════════════════════════════
#  CRITERION 3: RELATIVE STRENGTH vs SPY (max 15 pts)
# ═══════════════════════════════════════════════════════════════════

def score_relative_strength(
    close: pd.Series, spy_close: pd.Series, all_rs_values: Optional[List[float]] = None
) -> Tuple[int, float, str]:
    """
    Score relative strength vs SPY.
    Returns (score, rs_value, detail).
    If all_rs_values is provided, use it for percentile ranking.
    """
    lookback = min(126, len(close) - 1, len(spy_close) - 1)  # ~6 months
    if lookback < 20:
        return 0, 0.0, "Insufficient data"

    stock_ret = (float(close.iloc[-1]) / float(close.iloc[-lookback]) - 1) * 100
    spy_ret = (float(spy_close.iloc[-1]) / float(spy_close.iloc[-lookback]) - 1) * 100
    rs = stock_ret - spy_ret

    # If we have all RS values, compute percentile
    if all_rs_values and len(all_rs_values) > 10:
        percentile = sum(1 for v in all_rs_values if v <= rs) / len(all_rs_values) * 100
    else:
        percentile = 50  # default

    if percentile >= 80:
        score = 15
    elif percentile >= 60:
        score = 10
    elif percentile >= 40:
        score = 5
    else:
        score = 0

    return score, round(percentile, 1), f"RS Percentile: {percentile:.0f}%"


# ═══════════════════════════════════════════════════════════════════
#  CRITERION 4: INTRADAY PRICE ACTION (max 10 pts)
# ═══════════════════════════════════════════════════════════════════

def score_price_action(df: pd.DataFrame) -> Tuple[int, str]:
    """Score latest candle's price action."""
    if df.empty:
        return 0, "No data"

    last = df.iloc[-1]
    o, h, l, c = float(last["Open"]), float(last["High"]), float(last["Low"]), float(last["Close"])

    if h == l:
        return 0, "Doji candle"

    bullish = c > o
    candle_pos = (c - l) / (h - l)

    if bullish and candle_pos >= 0.75:
        return 10, "Strong bullish close (top 25%)"
    elif bullish and candle_pos >= 0.50:
        return 7, "Bullish close (upper half)"
    elif not bullish and candle_pos >= 0.50:
        return 3, "Bearish but closing upper half"
    else:
        return 0, "Weak close (lower half)"


# ═══════════════════════════════════════════════════════════════════
#  CRITERION 5: VOLATILITY CONTRACTION / VCP (max 10 pts)
# ═══════════════════════════════════════════════════════════════════

def score_vcp(df: pd.DataFrame) -> Tuple[int, str]:
    """Score volatility contraction pattern."""
    if len(df) < 21:
        return 0, "Insufficient data"

    # Today's range
    last = df.iloc[-1]
    today_range = (float(last["High"]) - float(last["Low"])) / max(float(last["Low"]), 0.01) * 100

    # 20-day average range
    recent = df.tail(20)
    avg_range = ((recent["High"] - recent["Low"]) / recent["Low"].replace(0, np.nan) * 100).mean()

    if avg_range == 0 or np.isnan(avg_range):
        return 0, "Cannot compute range"

    ratio = today_range / avg_range

    if ratio < 0.6:
        return 10, f"Tight range — VCP signal ({ratio:.1%} of avg)"
    elif ratio < 0.8:
        return 7, f"Contracting ({ratio:.1%} of avg)"
    elif ratio < 1.0:
        return 4, f"Slightly tight ({ratio:.1%} of avg)"
    else:
        return 0, f"Expanding range ({ratio:.1%} of avg)"


# ═══════════════════════════════════════════════════════════════════
#  CRITERION 6: LIQUIDITY & VOLUME (max 15 pts)
# ═══════════════════════════════════════════════════════════════════

def score_liquidity(df: pd.DataFrame) -> Tuple[int, str]:
    """Score average dollar volume."""
    if len(df) < 50:
        return 0, "Insufficient data"

    avg_vol = float(df["Volume"].tail(50).mean())
    last_price = float(df["Close"].iloc[-1])
    avg_dollar_vol = avg_vol * last_price

    if avg_dollar_vol > 50e6:
        return 15, f"Excellent — institutional (${avg_dollar_vol/1e6:.0f}M/day)"
    elif avg_dollar_vol > 10e6:
        return 10, f"Good (${avg_dollar_vol/1e6:.0f}M/day)"
    elif avg_dollar_vol > 2e6:
        return 5, f"Adequate (${avg_dollar_vol/1e6:.1f}M/day)"
    else:
        return 0, f"Too thin (${avg_dollar_vol/1e6:.1f}M/day)"


# ═══════════════════════════════════════════════════════════════════
#  CRITERION 7: WEINSTEIN STAGE ANALYSIS (max 20 pts)
# ═══════════════════════════════════════════════════════════════════

def score_stage(df: pd.DataFrame) -> Tuple[int, str, str]:
    """
    Weinstein Stage Analysis using 150-day and 200-day SMAs.
    Returns (score, stage_label, detail).
    """
    if len(df) < 200:
        return 0, "Unknown", "Insufficient data for stage analysis"

    close = df["Close"]
    sma150 = close.rolling(150).mean()
    sma200 = close.rolling(200).mean()

    last_close = float(close.iloc[-1])
    last_sma150 = float(sma150.iloc[-1])
    last_sma200 = float(sma200.iloc[-1])

    # Slope of 150 SMA (current vs 30 days ago)
    sma150_30d_ago = float(sma150.iloc[-30]) if len(sma150) > 30 else last_sma150
    sma150_rising = last_sma150 > sma150_30d_ago

    if last_close > last_sma150 and sma150_rising:
        return 20, "Stage 2", "Uptrend — price > rising 150 SMA"
    elif abs(last_close - last_sma150) / last_sma150 < 0.05:
        if sma150_rising or abs(last_sma150 - sma150_30d_ago) / sma150_30d_ago < 0.02:
            return 5, "Stage 1", "Basing — price near flattening 150 SMA"
        else:
            return 0, "Stage 3", "Top — price near declining 150 SMA"
    elif last_close < last_sma150 and not sma150_rising:
        return 0, "Stage 4", "Downtrend — price < declining 150 SMA"
    else:
        return 0, "Stage 3", "Distribution zone"


# ═══════════════════════════════════════════════════════════════════
#  BATCH SEPA SCANNER
# ═══════════════════════════════════════════════════════════════════

def scan_universe(
    history_cache: Dict[str, pd.DataFrame],
    quick_data: Dict[str, dict],
    spy_df: Optional[pd.DataFrame] = None,
) -> List[dict]:
    """
    Run SEPA analysis on all stocks in history_cache.
    Returns list of scored stocks sorted by score descending.
    """
    logger.info(f"═══ SEPA SCANNER ({len(history_cache)} stocks) ═══")

    # Get SPY data for relative strength
    if spy_df is None:
        spy_df = yf.download("SPY", period="1y", auto_adjust=True, progress=False)
        if isinstance(spy_df.columns, pd.MultiIndex):
            spy_df.columns = spy_df.columns.droplevel(1)

    spy_close = spy_df["Close"] if not spy_df.empty else pd.Series()

    # First pass: calculate all RS values for percentile ranking
    all_rs = []
    for ticker, df in history_cache.items():
        try:
            close = df["Close"]
            lookback = min(126, len(close) - 1, len(spy_close) - 1)
            if lookback >= 20:
                stock_ret = (float(close.iloc[-1]) / float(close.iloc[-lookback]) - 1) * 100
                spy_ret = (float(spy_close.iloc[-1]) / float(spy_close.iloc[-lookback]) - 1) * 100
                all_rs.append(stock_ret - spy_ret)
        except Exception:
            pass

    # Second pass: score each stock
    results = []
    processed = 0

    for ticker, df in history_cache.items():
        try:
            close = df["Close"]

            # Criterion 1: 52-Week High Proximity
            s1, d1 = score_52wk_high(close)

            # Criterion 2: 52-Week Low Distance
            s2, d2 = score_52wk_low(close)

            # Criterion 3: Relative Strength
            s3, rs_pct, d3 = score_relative_strength(close, spy_close, all_rs)

            # Criterion 4: Intraday Price Action
            s4, d4 = score_price_action(df)

            # Criterion 5: VCP
            s5, d5 = score_vcp(df)

            # Criterion 6: Liquidity
            s6, d6 = score_liquidity(df)

            # Criterion 7: Weinstein Stage
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

            # Get price info from quick_data
            qd = quick_data.get(ticker, {})
            price = qd.get("price", float(close.iloc[-1]))
            change_pct = qd.get("change_pct", 0.0)
            avg_vol = qd.get("volume", float(df["Volume"].tail(50).mean()))

            criteria_passed = sum(1 for s in [s1, s2, s3, s4, s5, s6, s7] if s > 0)

            results.append({
                "ticker": ticker,
                "price": round(price, 2),
                "change_pct": round(change_pct, 2),
                "score": total_score,
                "verdict": verdict,
                "verdict_class": verdict_class,
                "criteria_passed": f"{criteria_passed}/7",
                "stage": stage,
                "rs_percentile": rs_pct,
                "avg_dollar_volume": round(avg_vol * price / 1e6, 1),
                "details": {
                    "52wk_high": {"score": s1, "max": 15, "detail": d1},
                    "52wk_low": {"score": s2, "max": 15, "detail": d2},
                    "rel_strength": {"score": s3, "max": 15, "detail": d3},
                    "price_action": {"score": s4, "max": 10, "detail": d4},
                    "vcp": {"score": s5, "max": 10, "detail": d5},
                    "liquidity": {"score": s6, "max": 15, "detail": d6},
                    "stage": {"score": s7, "max": 20, "detail": d7},
                },
            })

            processed += 1
            if processed % 200 == 0:
                logger.info(f"  Scored {processed}/{len(history_cache)} stocks")

        except Exception as e:
            continue

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)

    logger.info(f"  SEPA scan complete: {len(results)} stocks scored")
    actionable = sum(1 for r in results if r["score"] >= 75)
    watchlist = sum(1 for r in results if 50 <= r["score"] < 75)
    logger.info(f"  Actionable: {actionable} | Watchlist: {watchlist}")

    return results


def get_top_gainers_losers(
    quick_data: Dict[str, dict],
    history_cache: Dict[str, pd.DataFrame],
    n: int = 10,
) -> Tuple[List[dict], List[dict]]:
    """
    Get top N gainers and losers by daily % change.
    Only includes stocks with avg dollar volume > $5M.
    """
    candidates = []

    for ticker, qd in quick_data.items():
        df = history_cache.get(ticker)
        if df is None or len(df) < 50:
            continue

        avg_vol = float(df["Volume"].tail(50).mean())
        price = qd.get("price", 0)
        avg_dollar_vol = avg_vol * price

        if avg_dollar_vol < 5e6:
            continue

        candidates.append({
            "ticker": ticker,
            "price": round(price, 2),
            "change_pct": round(qd.get("change_pct", 0), 2),
            "volume": round(avg_vol),
            "dollar_volume": round(avg_dollar_vol / 1e6, 1),
        })

    # Sort for gainers (descending) and losers (ascending)
    gainers = sorted(candidates, key=lambda x: x["change_pct"], reverse=True)[:n]
    losers = sorted(candidates, key=lambda x: x["change_pct"])[:n]

    return gainers, losers
