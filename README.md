<div align="center">

# ⚡ ALPHA ENGINE

### US Market Monitor & SEPA Decision Engine

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/VamsiKrishna2021/alpha-engine/actions)
[![GitHub Pages](https://img.shields.io/badge/Dashboard-Live-00e676?style=for-the-badge&logo=github&logoColor=white)](https://vamsikrishna2021.github.io/alpha-engine/)
[![Tests](https://img.shields.io/badge/Tests-111_Passing-4caf50?style=for-the-badge&logo=pytest&logoColor=white)](#-test-coverage)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

**Scans 6,500+ US stocks daily · Scores them 0-100 using Minervini's SEPA criteria · Detects market regime · Zero cost infrastructure**

[**Live Dashboard →**](https://vamsikrishna2021.github.io/alpha-engine/) · [Report Bug](https://github.com/VamsiKrishna2021/alpha-engine/issues) · [Request Feature](https://github.com/VamsiKrishna2021/alpha-engine/issues)

---

</div>

## 🏗️ Architecture

```
┌─────────────────────────────── GITHUB ACTIONS (4:30 PM ET Mon-Fri) ───────────────────────────────┐
│                                                                                                    │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│   │ UNIVERSE │───▸│PRE-FILTER│───▸│ DOWNLOAD │───▸│  REGIME  │───▸│  SEPA    │───▸│DASHBOARD │   │
│   │  FETCH   │    │ $5+ Vol  │    │ 1Y OHLCV │    │ DETECTOR │    │ SCANNER  │    │   GEN    │   │
│   │  6,547   │    │  2,224   │    │  2,203   │    │  0-100   │    │ 7 Criteria│    │ Jinja2   │   │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘   │
│                                                                                       │           │
│   Data Sources:  NASDAQ Trader FTP │ SEC EDGAR │ Alpha Vantage │ yfinance             │           │
│                                                                                       ▼           │
│                                                                              ┌──────────────┐    │
│                                                                              │ GitHub Pages  │    │
│                                                                              │  Dark Theme   │    │
│                                                                              │  Dashboard    │    │
│                                                                              └──────────────┘    │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 📊 Market Regime Detector
5-component weighted score (0-100) tells you whether to be aggressive or defensive:

| Component | Weight |
|-----------|--------|
| EMA Alignment (SPY 21/50/200) | 25% |
| Market Breadth (% > 20d SMA) | 25% |
| Trend Momentum (SPY 10d ROC) | 20% |
| Volatility (VIX Level) | 15% |
| Breadth Thrust Recency | 15% |

**Labels:** `FULL OFFENSE` · `SELECTIVE` · `DEFENSIVE` · `CAPITAL PRESERVATION`

</td>
<td width="50%">

### 🎯 SEPA Scanner (Minervini)
7-criterion scoring for every stock in the universe:

| Criterion | Max |
|-----------|-----|
| 52-Week High Proximity | 15 |
| 52-Week Low Distance | 15 |
| Relative Strength vs SPY | 15 |
| Intraday Price Action | 10 |
| Volatility Contraction (VCP) | 10 |
| Liquidity & Volume | 15 |
| Weinstein Stage Analysis | 20 |

**Verdicts:** `ACTIONABLE (75+)` · `WATCHLIST (50-74)` · `AVOID (<50)`

</td>
</tr>
<tr>
<td>

### 🔥 Sector Rotation Heatmap
11 SPDR ETFs color-coded by performance. **Click any sector** to see the top stocks in that sector from today's scan, sorted by SEPA score.

### 📈 Market Breadth
Daily A/D ratio, % above 10/20/40-day SMAs, 4% movers count. Auto-flags: `WASHOUT` · `CAPITULATION` · `BREADTH THRUST` · `EXTENDED`

</td>
<td>

### 💰 Capital Allocation Model
Regime-adjusted position sizing:

| Regime | Risk/Trade | Max Pos | Deploy |
|--------|-----------|---------|--------|
| Full Offense | 1.0% | 8 | 80% |
| Selective | 0.75% | 5 | 50% |
| Defensive | 0.5% | 3 | 25% |
| Preservation | 0.25% | 1 | 10% |

### 🔬 Stock Analyser
Type any ticker → rich SEPA breakdown with score, verdict, 7 criteria cards, and advice.

</td>
</tr>
</table>

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/VamsiKrishna2021/alpha-engine.git
cd alpha-engine
pip install -r requirements.txt
```

### 2. Configure Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Required | Default | Description |
|--------|----------|---------|-------------|
| `ACCOUNT_EQUITY` | No | `50000` | Your trading account size |
| `EMAIL_SENDER` | No | — | Gmail address for alerts |
| `EMAIL_PASSWORD` | No | — | Gmail app password |
| `EMAIL_TO` | No | — | Alert recipient |
| `TELEGRAM_BOT_TOKEN` | No | — | Telegram bot token |
| `TELEGRAM_CHAT_ID` | No | — | Telegram chat ID |
| `ALPHAVANTAGE_API_KEY` | No | — | Fallback data source |
| `FINNHUB_API_KEY` | No | — | Fallback data source |

### 3. Enable GitHub Pages

**Settings → Pages → Source → GitHub Actions**

### 4. Run Your First Scan

**Actions → Daily Market Scan → Run workflow**

⏱️ Takes 10-18 minutes. Dashboard auto-deploys to:
`https://YOUR-USERNAME.github.io/alpha-engine/`

---

## 📁 Project Structure

```
alpha-engine/
├── .github/workflows/
│   ├── daily_scan.yml          # ⏰ 4:30 PM ET Mon-Fri cron
│   ├── on_demand_scan.yml      # 🔍 Manual ticker analysis
│   └── deploy_dashboard.yml    # 🚀 GitHub Pages deployment
├── scripts/
│   ├── config.py               # ⚙️ All constants & thresholds
│   ├── data_fetcher.py         # 📡 Universe fetch + OHLCV download
│   ├── regime_detector.py      # 🧭 5-component regime scoring
│   ├── breadth_calculator.py   # 📊 Market breadth metrics
│   ├── sector_rotation.py      # 🔥 Sector ETF heatmap
│   ├── sepa_scanner.py         # 🎯 7-criterion SEPA scoring
│   ├── single_stock_analyser.py# 🔬 Deep single-ticker analysis
│   ├── capital_allocator.py    # 💰 Position sizing model
│   ├── action_board.py         # 🎬 Daily scan orchestrator
│   ├── generate_dashboard.py   # 🖥️ Jinja2 → HTML renderer
│   └── utils.py                # 🔧 Helper functions
├── templates/
│   └── index.html              # 🌐 Main dashboard (Jinja2)
├── static/
│   ├── style.css               # 🎨 Dark theme CSS
│   └── script.js               # ⚡ Frontend interactivity
├── tests/                      # ✅ 111 unit tests
├── data/                       # 💾 Persistent CSV/JSON data
├── output/                     # 📤 Generated HTML (deployed)
├── requirements.txt
└── README.md
```

---

## 🧪 Test Coverage

**111 tests** across 5 test files — all passing.

```bash
PYTHONPATH=. python -m pytest tests/ -v
```

| Test File | Tests | What It Covers |
|-----------|-------|----------------|
| `test_config.py` | 23 | Env vars, empty/invalid handling, thresholds, sector ETFs, benchmarks |
| `test_utils.py` | 27 | Number formatting, regime labels/colors, SEPA verdicts, CSV/JSON helpers |
| `test_sepa_scanner.py` | 35 | All 7 criteria scoring with edge cases, score range validation |
| `test_capital_allocator.py` | 18 | Risk per trade, deployment models, position sizing, regime effects |
| `test_regime_detector.py` | 12 | EMA alignment (bull/bear/boundary), momentum ROC, score ranges |

---

## 📡 Data Sources

| Source | What | Priority |
|--------|------|----------|
| [NASDAQ Trader FTP](https://www.nasdaqtrader.com/dynamic/symdir/) | Full US ticker universe (~6,547) | Primary |
| [Alpha Vantage](https://www.alphavantage.co/) | Fallback ticker listing | Secondary |
| [SEC EDGAR](https://www.sec.gov/files/company_tickers.json) | Fallback ticker listing | Tertiary |
| [yfinance](https://github.com/ranaroussi/yfinance) | All OHLCV price/volume data | Primary |
| [Wikipedia](https://en.wikipedia.org/wiki/List_of_S%26P_500_companies) | S&P 500 constituents | Breadth calc |

---

## ⚙️ Configuration

All thresholds in `scripts/config.py` — override via environment variables:

```python
# Regime thresholds
REGIME_FULL_OFFENSE = 80    # Score 80+ → aggressive
REGIME_SELECTIVE = 50        # 50-79 → selective
REGIME_DEFENSIVE = 30        # 30-49 → defensive

# Position sizing
MAX_POSITION_PCT = 0.08      # 8% of equity per position
MAX_SECTOR_PCT = 0.30        # 30% max in one sector
RISK_PER_TRADE_FULL = 0.01   # 1% risk in full offense
TIME_STOP_DAYS = 15           # Exit if no progress

# Universe pre-filter
PREFILTER_MIN_PRICE = 5.0     # $5 minimum
PREFILTER_MIN_VOLUME = 500000 # 500K minimum avg volume
ACCOUNT_EQUITY = 50000        # Default account size
```

---

## 🔄 GitHub Actions Workflows

| Workflow | Trigger | Duration | What It Does |
|----------|---------|----------|-------------|
| `daily_scan.yml` | 4:30 PM ET Mon-Fri + manual | ~10-18 min | Full universe scan + dashboard deploy |
| `on_demand_scan.yml` | Manual (ticker input) | ~2 min | Single stock SEPA analysis |
| `deploy_dashboard.yml` | On push to output/ | ~20 sec | Deploy HTML to GitHub Pages |

---

## ⚠️ Disclaimer

This is a **personal research tool**. Not financial advice. All investment decisions are your own responsibility. Past performance does not guarantee future results. The SEPA scoring system is based on publicly documented trading methodologies and does not constitute a recommendation to buy or sell any security.

---

<div align="center">

**Built by [Vamsi Madhabattula](https://github.com/VamsiKrishna2021)** · Alpha Engine v1.0 · March 2026

MIT License

</div>
