# Alpha Engine — US Market Monitor & Decision Engine

A production-ready US equities swing trading dashboard and decision engine built with Python, GitHub Actions, and GitHub Pages.

![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Scan](https://img.shields.io/badge/scan-daily_4:30PM_ET-orange)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GITHUB ACTIONS (Compute)                   │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Universe  │→ │Pre-filter│→ │ Download │→ │  SEPA    │    │
│  │ Fetch     │  │Price/Vol │  │ 1Y OHLCV │  │ Scanner  │    │
│  │ ~6,500    │  │ ~1,500   │  │          │  │ 7-Criteria│    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│       │              │              │              │          │
│       ▼              ▼              ▼              ▼          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Regime   │  │ Breadth  │  │ Sector   │  │ Capital  │    │
│  │ Detector │  │Calculator│  │ Rotation │  │Allocator │    │
│  │ 0-100    │  │ A/D, %MA │  │ Heatmap  │  │ Sizing   │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                        │                                      │
│                        ▼                                      │
│              ┌─────────────────┐                             │
│              │  Dashboard Gen  │ → output/index.html         │
│              │  (Jinja2)       │                             │
│              └─────────────────┘                             │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  GITHUB PAGES (Frontend)                      │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Dark Dashboard: Regime • Breadth • Sectors • SEPA    │   │
│  │ Top 14 Stocks • Gainers/Losers • Single Analyser     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

### Market Regime Detector (0-100 Score)
5-component weighted analysis:
| Component | Weight | What It Measures |
|-----------|--------|-----------------|
| EMA Alignment | 25% | SPY vs 21/50/200 EMA stack |
| Market Breadth | 25% | % of S&P 500 above 20-day SMA |
| Trend Momentum | 20% | SPY 10-day Rate of Change |
| Volatility | 15% | VIX level (fear gauge) |
| Breadth Thrust | 15% | Recent A/D ratio > 3x event |

**Regime Labels:** FULL OFFENSE (80+) · SELECTIVE (50-79) · DEFENSIVE (30-49) · CAPITAL PRESERVATION (0-29)

### SEPA Scanner (Minervini-Style, 7 Criteria)
| Criterion | Max | What It Checks |
|-----------|-----|---------------|
| 52-Week High Proximity | 15 | Distance from highs |
| 52-Week Low Distance | 15 | Distance from lows |
| Relative Strength vs SPY | 15 | 6-month outperformance percentile |
| Intraday Price Action | 10 | Candle position & direction |
| Volatility Contraction (VCP) | 10 | Range tightening signal |
| Liquidity & Volume | 15 | Average dollar volume |
| Weinstein Stage Analysis | 20 | 150/200 SMA stage |

**Verdicts:** ACTIONABLE (75+) · WATCHLIST (50-74) · AVOID (25-49) · NO (0-24)

### Market Breadth
- Advance/Decline count & ratio
- Up/Down 4% movers
- % above 10/20/40-day SMAs
- Threshold flags: WASHOUT, EXTENDED, CAPITULATION, BREADTH THRUST

### Sector Rotation Heatmap
11 SPDR Sector ETFs ranked by daily and weekly performance with color-coded tiles.

### Capital Allocation Model
Regime-adjusted position sizing:
| Regime | Risk/Trade | Max Positions | Deploy |
|--------|-----------|--------------|--------|
| Full Offense | 1.0% | 8 | 80% |
| Selective | 0.75% | 5 | 50% |
| Defensive | 0.5% | 3 | 25% |
| Preservation | 0.25% | 1 | 10% |

---

## Repository Structure

```
alpha-engine/
├── .github/workflows/
│   ├── daily_scan.yml          # 4:30 PM ET Mon-Fri cron
│   ├── on_demand_scan.yml      # Manual ticker analysis
│   └── deploy_dashboard.yml    # GitHub Pages deployment
├── scripts/
│   ├── config.py               # All constants & thresholds
│   ├── data_fetcher.py         # Universe fetch + OHLCV download
│   ├── regime_detector.py      # 5-component regime scoring
│   ├── breadth_calculator.py   # Market breadth metrics
│   ├── sector_rotation.py      # Sector ETF heatmap
│   ├── sepa_scanner.py         # 7-criterion SEPA scoring
│   ├── single_stock_analyser.py# Deep single-ticker analysis
│   ├── capital_allocator.py    # Position sizing model
│   ├── action_board.py         # Daily scan orchestrator
│   ├── generate_dashboard.py   # Jinja2 → HTML renderer
│   └── utils.py                # Helper functions
├── templates/
│   ├── index.html              # Main dashboard template
│   └── analyse.html            # Single stock analyser
├── static/
│   ├── style.css               # Dark theme CSS
│   └── script.js               # Frontend interactivity
├── data/                       # Persistent CSV/JSON data
├── output/                     # Generated HTML (deployed)
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Fork/Clone the Repository

```bash
git clone https://github.com/VamsiKrishna2021/alpha-engine.git
cd alpha-engine
pip install -r requirements.txt
```

### 2. Configure GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Required | Description |
|--------|----------|-------------|
| `ACCOUNT_EQUITY` | Optional | Trading account size (default: $50,000) |
| `ALPHAVANTAGE_API_KEY` | Optional | Fallback data source API key |
| `FINNHUB_API_KEY` | Optional | Fallback data source API key |
| `EMAIL_SENDER` | Optional | Gmail address for alerts |
| `EMAIL_PASSWORD` | Optional | Gmail app password |
| `EMAIL_TO` | Optional | Alert recipient email |
| `TELEGRAM_BOT_TOKEN` | Optional | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Optional | Telegram chat ID |

### 3. Enable GitHub Pages

Go to **Settings → Pages → Source → GitHub Actions**

### 4. Run Your First Scan

Go to **Actions → Daily Market Scan → Run workflow**

---

## Usage

### Automated Daily Scan
Runs automatically at **4:30 PM ET** (after market close) every weekday via GitHub Actions cron.

### Manual Full Scan
Go to **Actions → Daily Market Scan → Run workflow** to trigger an on-demand full scan.

### Single Stock Analysis
Go to **Actions → On-Demand Stock Analysis → Run workflow** and enter a ticker symbol.

### Dashboard
After any scan completes, the dashboard auto-deploys to GitHub Pages at:
`https://vamsikrishna2021.github.io/alpha-engine/`

---

## Configurable Thresholds

All thresholds are defined in `scripts/config.py` and can be overridden via environment variables:

```python
MAX_POSITION_PCT = 0.08      # 8% of equity per position
MAX_SECTOR_PCT = 0.30         # 30% max in one sector
RISK_PER_TRADE_FULL = 0.01   # 1% risk in full offense
RISK_PER_TRADE_SELECTIVE = 0.0075
RISK_PER_TRADE_DEFENSIVE = 0.005
TIME_STOP_DAYS = 15           # Exit if no progress in 15 days
ACCOUNT_EQUITY = 50000        # Default account size
```

---

## Data Sources

| Source | What | Priority |
|--------|------|----------|
| NASDAQ Trader FTP | Full US ticker universe (~6,500) | Primary |
| Alpha Vantage | Fallback ticker listing | Secondary |
| SEC EDGAR | Fallback ticker listing | Tertiary |
| yfinance | All OHLCV price/volume data | Primary |
| Wikipedia | S&P 500 constituents | Breadth calc |

---

## Disclaimer

This is a personal research tool. Not financial advice. All investment decisions are your own responsibility. Past performance does not guarantee future results.

---

## Author

**Vamsi Madhabattula** — DevOps Engineer & Quantitative Trading Enthusiast

---

## License

MIT License
