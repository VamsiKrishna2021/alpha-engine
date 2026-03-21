"""
capital_allocator.py — Position Sizing & Capital Deployment Model
==================================================================
Determines how much capital to deploy per trade based on regime.
"""
from __future__ import annotations

import logging
from typing import Dict, List

from scripts.config import CFG

logger = logging.getLogger("alpha_engine")


def get_risk_per_trade(regime_score: float) -> float:
    """Get risk % per trade based on market regime."""
    if regime_score >= CFG.REGIME_FULL_OFFENSE:
        return CFG.RISK_PER_TRADE_FULL
    elif regime_score >= CFG.REGIME_SELECTIVE:
        return CFG.RISK_PER_TRADE_SELECTIVE
    elif regime_score >= CFG.REGIME_DEFENSIVE:
        return CFG.RISK_PER_TRADE_DEFENSIVE
    else:
        return CFG.RISK_PER_TRADE_DEFENSIVE * 0.5  # Capital preservation: half defensive


def get_deployment_model(regime_score: float) -> dict:
    """
    Get the capital deployment model based on regime score.
    Returns deployment parameters.
    """
    equity = CFG.ACCOUNT_EQUITY
    risk_pct = get_risk_per_trade(regime_score)
    risk_dollar = equity * risk_pct
    max_position = equity * CFG.MAX_POSITION_PCT

    if regime_score >= CFG.REGIME_FULL_OFFENSE:
        max_positions = 8
        equity_deployed_pct = 0.80  # Deploy up to 80% of capital
        label = "FULL OFFENSE"
        advice = "Aggressively deploy. Buy breakouts with conviction."
    elif regime_score >= CFG.REGIME_SELECTIVE:
        max_positions = 5
        equity_deployed_pct = 0.50
        label = "SELECTIVE"
        advice = "Be selective. Only A+ setups. Reduce size on weaker signals."
    elif regime_score >= CFG.REGIME_DEFENSIVE:
        max_positions = 3
        equity_deployed_pct = 0.25
        label = "DEFENSIVE"
        advice = "Minimal exposure. Only highest-conviction trades. Tight stops."
    else:
        max_positions = 1
        equity_deployed_pct = 0.10
        label = "CAPITAL PRESERVATION"
        advice = "Preserve capital. Cash is a position. Wait for regime improvement."

    return {
        "label": label,
        "equity": equity,
        "risk_per_trade_pct": round(risk_pct * 100, 2),
        "risk_per_trade_dollar": round(risk_dollar, 2),
        "max_position_size": round(max_position, 2),
        "max_positions": max_positions,
        "equity_deployed_pct": round(equity_deployed_pct * 100, 1),
        "max_capital_deployed": round(equity * equity_deployed_pct, 2),
        "max_sector_pct": round(CFG.MAX_SECTOR_PCT * 100, 1),
        "time_stop_days": CFG.TIME_STOP_DAYS,
        "advice": advice,
    }


def calculate_position_size(
    entry_price: float,
    stop_loss: float,
    regime_score: float,
) -> dict:
    """
    Calculate exact position size for a trade.
    Uses ATR-based or fixed stop to determine shares.
    """
    equity = CFG.ACCOUNT_EQUITY
    risk_pct = get_risk_per_trade(regime_score)
    risk_dollar = equity * risk_pct
    max_position = equity * CFG.MAX_POSITION_PCT

    risk_per_share = abs(entry_price - stop_loss)
    if risk_per_share <= 0:
        return {
            "shares": 0,
            "risk_dollar": 0,
            "position_value": 0,
            "pct_of_equity": 0,
            "error": "Invalid stop loss",
        }

    # Shares based on risk
    shares_from_risk = int(risk_dollar / risk_per_share)

    # Shares based on max position size
    shares_from_position = int(max_position / entry_price)

    # Take the lesser
    shares = min(shares_from_risk, shares_from_position)
    position_value = shares * entry_price
    actual_risk = shares * risk_per_share

    return {
        "shares": shares,
        "risk_dollar": round(actual_risk, 2),
        "position_value": round(position_value, 2),
        "pct_of_equity": round(position_value / equity * 100, 2),
        "risk_per_share": round(risk_per_share, 2),
        "entry": round(entry_price, 2),
        "stop_loss": round(stop_loss, 2),
    }
