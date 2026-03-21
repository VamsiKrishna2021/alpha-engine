"""
data_fetcher.py — Ticker Universe Acquisition & OHLCV Data Download
====================================================================
Fetches the full US equity universe from NASDAQ Trader FTP (primary),
with SEC EDGAR and Alpha Vantage fallbacks.
Downloads OHLCV data via yfinance with batch processing.
"""
from __future__ import annotations

import csv
import io
import json
import logging
import math
import time
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests
import yfinance as yf

from scripts.config import CFG, SP500_URL

logger = logging.getLogger("alpha_engine")


# ═══════════════════════════════════════════════════════════════════
#  TICKER UNIVERSE ACQUISITION
# ═══════════════════════════════════════════════════════════════════

def fetch_nasdaq_trader_tickers() -> List[str]:
    """Pull ALL US-listed tickers from NASDAQ Trader FTP (pipe-delimited).
    Excludes ETFs, test issues, and tickers with special characters.
    """
    base = "https://www.nasdaqtrader.com/dynamic/symdir"
    tickers: set = set()

    for filename in ["nasdaqlisted.txt", "otherlisted.txt"]:
        try:
            resp = requests.get(f"{base}/{filename}", timeout=15)
            resp.raise_for_status()
            lines = resp.text.strip().split("\n")

            for line in lines[1:]:
                parts = line.split("|")
                if len(parts) < 2:
                    continue
                symbol = parts[0].strip()

                if filename == "nasdaqlisted.txt":
                    test_issue = parts[3].strip() if len(parts) > 3 else "N"
                    fin_status = parts[4].strip() if len(parts) > 4 else "N"
                    is_etf = parts[6].strip() if len(parts) > 6 else "N"
                    if test_issue == "Y" or fin_status != "N" or is_etf == "Y":
                        continue
                elif filename == "otherlisted.txt":
                    test_issue = parts[5].strip() if len(parts) > 5 else "N"
                    is_etf = parts[4].strip() if len(parts) > 4 else "N"
                    if test_issue == "Y" or is_etf == "Y":
                        continue

                if any(c in symbol for c in ["$", ".", "-", "^", "+"]):
                    continue
                if symbol.startswith("File"):
                    continue
                tickers.add(symbol)

            logger.info(f"NASDAQ Trader {filename}: {len(tickers)} cumulative tickers")
        except Exception as e:
            logger.warning(f"Failed to fetch {filename}: {e}")

    return sorted(tickers)


def fetch_sec_edgar_tickers() -> List[str]:
    """Fallback: SEC EDGAR company_tickers.json."""
    try:
        resp = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers={"User-Agent": "AlphaEngine vamsi@example.com"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        tickers = set()
        for entry in data.values():
            sym = entry.get("ticker", "").strip().upper()
            if sym and not any(c in sym for c in ["$", ".", "-", "^"]):
                tickers.add(sym)
        logger.info(f"SEC EDGAR: {len(tickers)} tickers")
        return sorted(tickers)
    except Exception as e:
        logger.warning(f"SEC EDGAR fetch failed: {e}")
        return []


def fetch_alphavantage_listing() -> List[str]:
    """Fallback #2: Alpha Vantage free listing CSV."""
    try:
        url = "https://www.alphavantage.co/query?function=LISTING_STATUS&apikey=demo"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        reader = csv.DictReader(io.StringIO(resp.text))
        tickers = set()
        for row in reader:
            sym = row.get("symbol", "").strip().upper()
            asset_type = row.get("assetType", "")
            exchange = row.get("exchange", "")
            status = row.get("status", "")
            if (
                sym
                and asset_type == "Stock"
                and exchange in ("NYSE", "NASDAQ", "NYSE ARCA", "AMEX", "BATS", "NYSE American")
                and status == "Active"
                and not any(c in sym for c in ["$", ".", "-", "^"])
            ):
                tickers.add(sym)
        logger.info(f"Alpha Vantage: {len(tickers)} tickers")
        return sorted(tickers)
    except Exception as e:
        logger.warning(f"Alpha Vantage fetch failed: {e}")
        return []


def get_full_us_universe() -> List[str]:
    """3-layer fallback to get broadest US equity universe."""
    tickers = fetch_nasdaq_trader_tickers()
    if len(tickers) > 1000:
        logger.info(f"Universe source: NASDAQ Trader ({len(tickers)} tickers)")
        return tickers

    tickers = fetch_alphavantage_listing()
    if len(tickers) > 1000:
        logger.info(f"Universe source: Alpha Vantage ({len(tickers)} tickers)")
        return tickers

    tickers = fetch_sec_edgar_tickers()
    if len(tickers) > 1000:
        logger.info(f"Universe source: SEC EDGAR ({len(tickers)} tickers)")
        return tickers

    logger.error("All universe sources failed. Using empty list.")
    return []


def get_sp500_tickers() -> List[str]:
    """Fetch S&P 500 constituents from Wikipedia."""
    try:
        tables = pd.read_html(SP500_URL)
        df = tables[0]
        tickers = df["Symbol"].str.replace(".", "-", regex=False).tolist()
        logger.info(f"S&P 500: {len(tickers)} tickers from Wikipedia")
        return tickers
    except Exception as e:
        logger.warning(f"S&P 500 fetch failed: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════
#  FAST PRE-FILTER (5-day price/volume)
# ═══════════════════════════════════════════════════════════════════

def fast_prefilter(tickers: List[str]) -> Tuple[List[str], Dict[str, dict]]:
    """
    Download 5-day data in batches to eliminate stocks outside
    price/volume bounds. Returns (passed_tickers, quick_data_dict).
    quick_data_dict = {ticker: {"price": float, "volume": float, "change_pct": float}}
    """
    logger.info(
        f"Pre-filtering {len(tickers)} tickers "
        f"(price ${CFG.PREFILTER_MIN_PRICE}-${CFG.PREFILTER_MAX_PRICE}, "
        f"vol >{CFG.PREFILTER_MIN_VOLUME:,})"
    )
    passed: List[str] = []
    quick_data: Dict[str, dict] = {}
    total_batches = math.ceil(len(tickers) / CFG.BATCH_SIZE)

    for i in range(0, len(tickers), CFG.BATCH_SIZE):
        batch = tickers[i : i + CFG.BATCH_SIZE]
        batch_num = i // CFG.BATCH_SIZE + 1
        try:
            data = yf.download(
                batch,
                period="5d",
                interval="1d",
                auto_adjust=True,
                threads=True,
                progress=False,
            )
            if data.empty:
                continue

            for sym in batch:
                try:
                    if len(batch) == 1:
                        close = data["Close"].dropna()
                        vol = data["Volume"].dropna()
                    else:
                        close = data["Close"][sym].dropna()
                        vol = data["Volume"][sym].dropna()

                    if close.empty or vol.empty or len(close) < 2:
                        continue

                    last_price = float(close.iloc[-1])
                    avg_vol = float(vol.mean())
                    change_pct = (
                        (float(close.iloc[-1]) - float(close.iloc[-2]))
                        / float(close.iloc[-2])
                        * 100
                    )

                    if (
                        CFG.PREFILTER_MIN_PRICE <= last_price <= CFG.PREFILTER_MAX_PRICE
                        and avg_vol >= CFG.PREFILTER_MIN_VOLUME
                    ):
                        passed.append(sym)
                        quick_data[sym] = {
                            "price": last_price,
                            "volume": avg_vol,
                            "change_pct": change_pct,
                        }
                except (KeyError, IndexError):
                    continue
        except Exception as e:
            logger.warning(f"Pre-filter batch {batch_num}/{total_batches}: {e}")

        if batch_num % 10 == 0:
            logger.info(
                f"Pre-filter: {batch_num}/{total_batches} batches, {len(passed)} passed"
            )
        time.sleep(CFG.SLEEP_BETWEEN_BATCHES)

    logger.info(f"Pre-filter done: {len(passed)}/{len(tickers)} passed")
    return passed, quick_data


# ═══════════════════════════════════════════════════════════════════
#  OHLCV DATA DOWNLOAD
# ═══════════════════════════════════════════════════════════════════

def download_batch_ohlcv(
    tickers: List[str],
    period: str = "1y",
    interval: str = "1d",
    min_bars: int = 50,
) -> Dict[str, pd.DataFrame]:
    """
    Download OHLCV data for a batch of tickers via yfinance.
    Returns {ticker: DataFrame} for tickers with at least min_bars.
    """
    logger.info(f"Downloading {period} history for {len(tickers)} tickers...")
    cache: Dict[str, pd.DataFrame] = {}
    total_batches = math.ceil(len(tickers) / CFG.BATCH_SIZE)

    for i in range(0, len(tickers), CFG.BATCH_SIZE):
        batch = tickers[i : i + CFG.BATCH_SIZE]
        batch_num = i // CFG.BATCH_SIZE + 1
        try:
            data = yf.download(
                batch,
                period=period,
                interval=interval,
                auto_adjust=True,
                threads=True,
                progress=False,
            )
            if data.empty:
                continue

            for sym in batch:
                try:
                    if len(batch) == 1:
                        hist = data[["Open", "High", "Low", "Close", "Volume"]].dropna()
                    else:
                        hist = (
                            data.xs(sym, axis=1, level=1)[
                                ["Open", "High", "Low", "Close", "Volume"]
                            ].dropna()
                        )
                    if len(hist) >= min_bars:
                        cache[sym] = hist
                except (KeyError, IndexError):
                    continue
        except Exception as e:
            logger.warning(f"History batch {batch_num}/{total_batches}: {e}")

        if batch_num % 5 == 0:
            logger.info(
                f"History: {batch_num}/{total_batches} batches, {len(cache)} cached"
            )
        time.sleep(CFG.SLEEP_BETWEEN_BATCHES)

    logger.info(f"History cache: {len(cache)} tickers with >= {min_bars} bars")
    return cache


def download_single_ticker(
    ticker: str,
    period: str = "1y",
    interval: str = "1d",
) -> Optional[pd.DataFrame]:
    """Download OHLCV for a single ticker. Returns DataFrame or None."""
    try:
        data = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
        )
        if data.empty:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
        return data.dropna()
    except Exception as e:
        logger.error(f"Failed to download {ticker}: {e}")
        return None


def get_current_price(ticker: str) -> Optional[float]:
    """Get the latest price for a ticker."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1d")
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception:
        return None
