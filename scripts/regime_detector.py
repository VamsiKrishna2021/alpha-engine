"""
regime_detector.py — Market Regime Scoring (0-100)
====================================================
5-component weighted score determining market environment.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf

from scripts.config import CFG
from scripts.utils import append_csv, regime_label, regime_color

logger = logging.getLogger("alpha_engine")


def _download(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Helper to download data for a single ticker."""
    data = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)
    return data.dropna()


# ═══════════════════════════════════════════════════════════════════
#  COMPONENT 1: EMA Alignment Score (weight: 25%)
# ═══════════════════════════════════════════════════════════════════

def ema_alignment_score(spy_df: pd.DataFrame) -> dict:
    """Score SPY's EMA alignment (21/50/200)."""
    close = spy_df["Close"]
    ema21 = close.ewm(span=21, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()

    last_close = float(close.iloc[-1])
    last_ema21 = float(ema21.iloc[-1])
    last_ema50 = float(ema50.iloc[-1])
    last_ema200 = float(ema200.iloc[-1])

    # Check if 200 EMA is declining
    ema200_slope = float(ema200.iloc[-1]) - float(ema200.iloc[-20]) if len(ema200) > 20 else 0

    if last_close > last_ema21 > last_ema50 > last_ema200:
        score = 100
    elif last_close > last_ema50 > last_ema200:
        score = 70
    elif last_close > last_ema200:
        score = 40
    else:
        score = 10

    # Penalize declining 200 EMA
    if ema200_slope < 0:
        score = max(0, score - 10)

    return {
        "score": score,
        "spy_close": last_close,
        "spy_vs_21ema": round((last_close / last_ema21 - 1) * 100, 2),
        "spy_vs_50ema": round((last_close / last_ema50 - 1) * 100, 2),
        "spy_vs_200ema": round((last_close / last_ema200 - 1) * 100, 2),
        "ema21": last_ema21,
        "ema50": last_ema50,
        "ema200": last_ema200,
    }


# ═══════════════════════════════════════════════════════════════════
#  COMPONENT 2: Breadth Score (weight: 25%)
# ═══════════════════════════════════════════════════════════════════

def breadth_score(sp500_tickers: list, period: str = "2mo") -> dict:
    """Calculate % of S&P 500 stocks above their 20-day SMA."""
    try:
        data = yf.download(
            sp500_tickers,
            period=period,
            interval="1d",
            auto_adjust=True,
            threads=True,
            progress=False,
        )
        if data.empty:
            return {"score": 50, "pct_above_20d": 50.0}

        above_count = 0
        total = 0

        for sym in sp500_tickers:
            try:
                if len(sp500_tickers) == 1:
                    close = data["Close"].dropna()
                else:
                    close = data["Close"][sym].dropna()

                if len(close) < 20:
                    continue

                sma20 = close.rolling(20).mean()
                if float(close.iloc[-1]) > float(sma20.iloc[-1]):
                    above_count += 1
                total += 1
            except (KeyError, IndexError):
                continue

        if total == 0:
            return {"score": 50, "pct_above_20d": 50.0}

        pct = (above_count / total) * 100

        # Normalize: 0% → 0, 50% → 50, 80%+ → 100
        if pct >= 80:
            score = 100
        else:
            score = min(100, pct * (100 / 80))

        return {"score": round(score), "pct_above_20d": round(pct, 1)}
    except Exception as e:
        logger.warning(f"Breadth score calculation failed: {e}")
        return {"score": 50, "pct_above_20d": 50.0}


# ═══════════════════════════════════════════════════════════════════
#  COMPONENT 3: Trend Momentum (weight: 20%)
# ═══════════════════════════════════════════════════════════════════

def trend_momentum_score(spy_df: pd.DataFrame) -> dict:
    """SPY 10-day Rate of Change."""
    close = spy_df["Close"]
    if len(close) < 11:
        return {"score": 50, "roc_10d": 0.0}

    roc = (float(close.iloc[-1]) / float(close.iloc[-11]) - 1) * 100

    if roc > 3:
        score = 100
    elif roc > 0:
        score = 60
    elif roc > -3:
        score = 30
    else:
        score = 0

    return {"score": score, "roc_10d": round(roc, 2)}


# ═══════════════════════════════════════════════════════════════════
#  COMPONENT 4: Volatility Score (weight: 15%)
# ═══════════════════════════════════════════════════════════════════

def volatility_score() -> dict:
    """Score based on VIX level."""
    try:
        vix_data = _download("^VIX", period="5d")
        if vix_data.empty:
            return {"score": 50, "vix": 20.0}

        vix = float(vix_data["Close"].iloc[-1])

        if vix < 15:
            score = 100
        elif vix < 20:
            score = 75
        elif vix < 30:
            score = 40
        else:
            score = 10

        return {"score": score, "vix": round(vix, 2)}
    except Exception as e:
        logger.warning(f"VIX fetch failed: {e}")
        return {"score": 50, "vix": 20.0}


# ═══════════════════════════════════════════════════════════════════
#  COMPONENT 5: Breadth Thrust Recency (weight: 15%)
# ═══════════════════════════════════════════════════════════════════

def breadth_thrust_score(breadth_history_path: str) -> dict:
    """Check if there was a breadth thrust recently (A/D ratio > 3)."""
    try:
        if not os.path.exists(breadth_history_path):
            return {"score": 20, "thrust_days_ago": None}

        df = pd.read_csv(breadth_history_path)
        if df.empty or "adv" not in df.columns or "dec" not in df.columns:
            return {"score": 20, "thrust_days_ago": None}

        # Calculate A/D ratio for recent days
        df["ad_ratio"] = df["adv"] / df["dec"].replace(0, 1)

        # Check last 10 trading days
        recent = df.tail(10)
        thrust_days = recent[recent["ad_ratio"] > 3.0]

        if len(thrust_days) == 0:
            return {"score": 20, "thrust_days_ago": None}

        # How recent was the thrust?
        last_thrust_idx = thrust_days.index[-1]
        days_ago = len(df) - 1 - last_thrust_idx

        if days_ago <= 5:
            score = 100
        elif days_ago <= 10:
            score = 60
        else:
            score = 20

        return {"score": score, "thrust_days_ago": int(days_ago)}
    except Exception as e:
        logger.warning(f"Breadth thrust calculation failed: {e}")
        return {"score": 20, "thrust_days_ago": None}


# ═══════════════════════════════════════════════════════════════════
#  MASTER REGIME DETECTOR
# ═══════════════════════════════════════════════════════════════════

def detect_regime(sp500_tickers: list = None) -> dict:
    """
    Calculate the full regime score (0-100) using 5 weighted components.

    Returns dict with:
      - regime_score, label, color
      - All component details
      - breakouts_likely (bool)
    """
    logger.info("═══ REGIME DETECTION ═══")

    # Download SPY data
    spy_df = _download("SPY", period="1y")
    if spy_df.empty:
        logger.error("Failed to download SPY data")
        return {
            "regime_score": 50,
            "label": "SELECTIVE",
            "color": "#ffeb3b",
            "breakouts_likely": False,
        }

    # Component 1: EMA Alignment (25%)
    ema_result = ema_alignment_score(spy_df)
    logger.info(f"  EMA Alignment: {ema_result['score']}/100")

    # Component 2: Breadth (25%)
    if sp500_tickers and len(sp500_tickers) > 0:
        # Sample 100 tickers for speed in GitHub Actions
        sample = sp500_tickers[:100] if len(sp500_tickers) > 100 else sp500_tickers
        breadth_result = breadth_score(sample)
    else:
        breadth_result = {"score": 50, "pct_above_20d": 50.0}
    logger.info(f"  Breadth Score: {breadth_result['score']}/100 ({breadth_result['pct_above_20d']}% > 20d SMA)")

    # Component 3: Trend Momentum (20%)
    momentum_result = trend_momentum_score(spy_df)
    logger.info(f"  Trend Momentum: {momentum_result['score']}/100 (ROC: {momentum_result['roc_10d']}%)")

    # Component 4: Volatility (15%)
    vol_result = volatility_score()
    logger.info(f"  Volatility: {vol_result['score']}/100 (VIX: {vol_result['vix']})")

    # Component 5: Breadth Thrust (15%)
    breadth_hist_path = os.path.join(CFG.DATA_DIR, "breadth_history.csv")
    thrust_result = breadth_thrust_score(breadth_hist_path)
    logger.info(f"  Breadth Thrust: {thrust_result['score']}/100")

    # Weighted sum
    regime_score = round(
        ema_result["score"] * 0.25
        + breadth_result["score"] * 0.25
        + momentum_result["score"] * 0.20
        + vol_result["score"] * 0.15
        + thrust_result["score"] * 0.15
    )

    label = regime_label(regime_score)
    color = regime_color(regime_score)

    # Breakouts likely?
    breakouts_likely = regime_score >= 70 and ema_result["spy_vs_50ema"] > 0

    logger.info(f"  ══ REGIME: {regime_score}/100 — {label} ══")
    logger.info(f"  Breakouts likely: {'YES' if breakouts_likely else 'NO'}")

    result = {
        "regime_score": regime_score,
        "label": label,
        "color": color,
        "breakouts_likely": breakouts_likely,
        "spy_close": ema_result["spy_close"],
        "spy_vs_21ema": ema_result["spy_vs_21ema"],
        "spy_vs_50ema": ema_result["spy_vs_50ema"],
        "spy_vs_200ema": ema_result["spy_vs_200ema"],
        "ema21": ema_result["ema21"],
        "ema50": ema_result["ema50"],
        "ema200": ema_result["ema200"],
        "vix": vol_result["vix"],
        "breadth_pct_20d": breadth_result["pct_above_20d"],
        "roc_10d": momentum_result["roc_10d"],
        "thrust_days_ago": thrust_result["thrust_days_ago"],
        "components": {
            "ema_alignment": {"score": ema_result["score"], "weight": 0.25},
            "breadth": {"score": breadth_result["score"], "weight": 0.25},
            "trend_momentum": {"score": momentum_result["score"], "weight": 0.20},
            "volatility": {"score": vol_result["score"], "weight": 0.15},
            "breadth_thrust": {"score": thrust_result["score"], "weight": 0.15},
        },
    }

    # Save to history
    history_row = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "regime_score": regime_score,
        "label": label,
        "spy_close": round(ema_result["spy_close"], 2),
        "spy_vs_21ema": ema_result["spy_vs_21ema"],
        "spy_vs_50ema": ema_result["spy_vs_50ema"],
        "spy_vs_200ema": ema_result["spy_vs_200ema"],
        "vix": vol_result["vix"],
        "breadth_pct_20d": breadth_result["pct_above_20d"],
    }
    history_path = os.path.join(CFG.DATA_DIR, "regime_history.csv")
    append_csv(history_path, history_row, max_rows=CFG.BREADTH_HISTORY_DAYS)

    return result
