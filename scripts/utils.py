"""
utils.py — Helper functions for Alpha Engine
=============================================
"""
from __future__ import annotations

import csv
import io
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from scripts.config import CFG

logger = logging.getLogger("alpha_engine")


def ensure_dirs():
    """Create data and output directories if they don't exist."""
    os.makedirs(CFG.DATA_DIR, exist_ok=True)
    os.makedirs(CFG.OUTPUT_DIR, exist_ok=True)


def load_json(filepath: str) -> Any:
    """Load JSON file, return empty dict on failure."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_json(data: Any, filepath: str):
    """Save data as JSON."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)


def append_csv(filepath: str, row: Dict[str, Any], max_rows: int = 0):
    """
    Append a row to a CSV file. Creates the file with headers if it doesn't exist.
    If max_rows > 0, trims to keep only the last max_rows rows.
    """
    file_exists = os.path.isfile(filepath)

    if file_exists:
        df = pd.read_csv(filepath)
        new_row = pd.DataFrame([row])
        df = pd.concat([df, new_row], ignore_index=True)
    else:
        df = pd.DataFrame([row])

    if max_rows > 0 and len(df) > max_rows:
        df = df.tail(max_rows)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)


def format_number(n: float, decimals: int = 2) -> str:
    """Format a number with commas and specified decimals."""
    if abs(n) >= 1e12:
        return f"${n/1e12:.1f}T"
    elif abs(n) >= 1e9:
        return f"${n/1e9:.1f}B"
    elif abs(n) >= 1e6:
        return f"${n/1e6:.1f}M"
    elif abs(n) >= 1e3:
        return f"${n/1e3:.1f}K"
    else:
        return f"{n:.{decimals}f}"


def pct_change_str(val: float) -> str:
    """Format percentage change with color hint."""
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.2f}%"


def regime_label(score: float) -> str:
    """Convert regime score to label."""
    if score >= CFG.REGIME_FULL_OFFENSE:
        return "FULL OFFENSE"
    elif score >= CFG.REGIME_SELECTIVE:
        return "SELECTIVE"
    elif score >= CFG.REGIME_DEFENSIVE:
        return "DEFENSIVE"
    else:
        return "CAPITAL PRESERVATION"


def regime_color(score: float) -> str:
    """Convert regime score to CSS color."""
    if score >= CFG.REGIME_FULL_OFFENSE:
        return "#00e676"
    elif score >= CFG.REGIME_SELECTIVE:
        return "#ffeb3b"
    elif score >= CFG.REGIME_DEFENSIVE:
        return "#ff9800"
    else:
        return "#ef5350"


def sepa_verdict(score: float) -> tuple:
    """Return (verdict_text, css_class) based on SEPA score."""
    if score >= 75:
        return "ACTIONABLE — LOOK FOR ENTRY", "badge-green"
    elif score >= 50:
        return "WATCHLIST — WAIT FOR SETUP", "badge-yellow"
    elif score >= 25:
        return "AVOID — WEAK STRUCTURE", "badge-orange"
    else:
        return "NO — STAGE 4 DECLINE", "badge-red"


def today_str() -> str:
    """Return today's date as YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


def now_str() -> str:
    """Return current datetime as human-readable string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S ET")


def setup_logging():
    """Configure logging for the entire application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
