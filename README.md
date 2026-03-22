<div align="center">

# ⚡ ALPHA ENGINE

### US Market Monitor & SEPA Decision Engine + AI Trading Agent

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/VamsiKrishna2021/alpha-engine/actions)
[![GitHub Pages](https://img.shields.io/badge/Dashboard-Live-00e676?style=for-the-badge&logo=github&logoColor=white)](https://vamsikrishna2021.github.io/alpha-engine/)
[![AI Pipeline](https://img.shields.io/badge/AI_Pipeline-Live-6c5ce7?style=for-the-badge&logo=openai&logoColor=white)](https://vamsikrishna2021.github.io/alpha-engine/pipeline.html)
[![Tests](https://img.shields.io/badge/Tests-111_Passing-4caf50?style=for-the-badge&logo=pytest&logoColor=white)](#-test-coverage)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

**Scans 6,500+ US stocks daily · Scores them 0-100 using Minervini's SEPA criteria · AI-powered 10-agent debate for final trade decisions · Zero to $30/mo infrastructure**

[**Live Dashboard →**](https://vamsikrishna2021.github.io/alpha-engine/) · [**AI Pipeline View →**](https://vamsikrishna2021.github.io/alpha-engine/pipeline.html) · [Report Bug](https://github.com/VamsiKrishna2021/alpha-engine/issues) · [Request Feature](https://github.com/VamsiKrishna2021/alpha-engine/issues)

---

</div>

## 🧠 System Overview

This project is the data engine behind a **3-repo trading system** that combines quantitative screening with AI reasoning:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        COMPLETE TRADING SYSTEM                               │
│                                                                              │
│  ┌─────────────────┐   ┌─────────────────┐   ┌──────────────────────────┐  │
│  │  ALPHA ENGINE    │   │   TRADE-BOT     │   │   AI TRADING AGENT       │  │
│  │  (this repo)     │   │   (private)     │   │   (private)              │  │
│  │                  │   │                  │   │                          │  │
│  │  6,500+ stocks   │   │  6 strategies   │   │  4-tier AI pipeline      │  │
│  │  SEPA scoring    │   │  Position sizing│   │  10-agent LLM debate     │  │
│  │  Regime detect   │   │  Entry/SL/T1/T2│   │  Capital allocation      │  │
│  │  Sector rotation │   │  Risk mgmt     │   │  TradingView + alerts    │  │
│  │  Market breadth  │   │  Telegram/Email │   │  Pipeline dashboard      │  │
│  │                  │   │                  │   │                          │  │
│  │  Runs: 4:30PM ET │   │  Runs: Sun 6PM │   │  Runs: Mon-Fri 4:30PM   │  │
│  └────────┬─────────┘   └────────┬────────┘   └──────────┬───────────────┘  │
│           │                       │                       │                  │
│           └───────────────────────┴───────────────────────┘                  │
│                                   │                                          │
│                      ┌────────────▼──────────────┐                          │
│                      │     TWO DASHBOARDS         │                          │
│                      │  Market Overview (index)    │                          │
│                      │  AI Pipeline (pipeline)     │                          │
│                      └───────────────────────────┘                          │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🖥️ Live Dashboards

### 📊 Market Overview Dashboard
**[vamsikrishna2021.github.io/alpha-engine/](https://vamsikrishna2021.github.io/alpha-engine/)**

Daily market intelligence: regime score, SEPA top stocks, sector heatmap, breadth metrics, capital allocation model, single stock analyser.

### 🤖 AI Pipeline Dashboard
**[vamsikrishna2021.github.io/alpha-engine/pipeline.html](https://vamsikrishna2021.github.io/alpha-engine/pipeline.html)**

AI trading agent results across all 4 tiers:
- **Pipeline funnel**: 214 → 22 → 8 → 5 stocks (visual)
- **Tier 1**: Full actionable universe, sortable, searchable
- **Tier 2**: Filtered candidates with sector leader & priority badges
- **Tier 3**: LLM-ranked stocks with entry/stop/target suggestions
- **Tier 4**: Full AI analysis cards — SEPA bars, trade levels, R:R, position sizing, AI thesis, bull vs bear summaries, conviction meter
- **Every ticker**: Clickable link → opens directly in TradingView
- **Copy Levels**: One-click copy entry/SL/T1/T2 for quick order entry
- Auto-refreshes every 60 seconds

---

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
                                            │
                                            ▼ scan_results.json
┌────────────────────────────── AI TRADING AGENT (runs after Alpha Engine) ──────────────────────────┐
│                                                                                                    │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐                   │
│   │ TIER 1   │───▸│ TIER 2   │───▸│ TIER 3   │───▸│ TIER 4   │───▸│ OUTPUT   │                   │
│   │Alpha Eng.│    │Smart Filt│    │LLM Rank  │    │10-Agent  │    │Telegram  │                   │
│   │214 stocks│    │SEPA+RS+  │    │gpt-4o-   │    │ Debate   │    │Email     │                   │
│   │+ TradeBot│    │Sector    │    │mini batch │    │Bull/Bear │    │Dashboard │                   │
│   │3 picks   │    │22 stocks │    │8 ranked  │    │Risk Mgmt │    │TradingView│                  │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘                   │
│                                                                                                    │
│   Budget: $30/mo │ Cost tracker │ Auto-throttle │ 89 tests passing                                │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 AI Trading Agent — 4-Tier Pipeline

The AI layer (separate private repo) reads this repo's `scan_results.json` and processes it through 4 tiers:

| Tier | What | Stocks | Cost |
|------|------|--------|------|
| **Tier 1** | Alpha Engine actionable (SEPA ≥ 75) + Trade-bot picks | ~214 | Free |
| **Tier 2** | Smart filter: SEPA ≥ 85, RS ≥ 70%, leading sectors, regime-aware | ~15-25 | Free |
| **Tier 3** | LLM batch ranking (gpt-4o-mini scores 1-10 with entry/stop/target) | ~5-10 | ~$0.01 |
| **Tier 4** | TradingAgents 10-agent debate: 4 analysts + bull/bear + risk team | ~3-5 | ~$0.15/stock |

### TradingAgents Debate Structure
```
Market Analyst ──┐
Social Analyst ──┤
News Analyst ────┤──▸ Bull Researcher ◄──▸ Bear Researcher ──▸ Research Manager
Fund. Analyst ───┘         (debate rounds)                         │
                                                                    ▼
                                                                  Trader
                                                                    │
                                          Aggressive ◄──▸ Conservative ◄──▸ Neutral
                                                   (risk debate rounds)
                                                            │
                                                            ▼
                                                      Risk Manager
                                                     BUY / SELL / HOLD
```

### Output Channels
- **Telegram**: Real-time alert with signals, position sizing, thesis
- **Email**: Bloomberg-style HTML report with stock cards
- **Pipeline Dashboard**: Interactive tier-by-tier view with TradingView links
- **TradingView**: Pine Script indicator with entry/SL/T1/T2 levels + alert conditions
- **Journal**: CSV paper trade log with outcome tracking

### Cost Control
- Monthly budget: $30 (auto-scales with account size)
- Auto-throttle at 90%, hard stop at 100%
- First full run cost: $0.05
- Account scaling: $10K→$30/mo, $25K→$75/mo, $50K→$150/mo

---

## ✨ Alpha Engine Features

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
├── output/
│   ├── index.html              # 📊 Market Overview dashboard
│   ├── pipeline.html           # 🤖 AI Pipeline dashboard
│   ├── pipeline_data.json      # 📦 AI agent tier data (auto-updated)
│   └── scan_results.json       # 📦 Daily scan results
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

## 🔄 GitHub Actions Workflows

| Workflow | Trigger | Duration | What It Does |
|----------|---------|----------|-------------|
| `daily_scan.yml` | 4:30 PM ET Mon-Fri + manual | ~10-18 min | Full universe scan + dashboard deploy |
| `on_demand_scan.yml` | Manual (ticker input) | ~2 min | Single stock SEPA analysis |
| `deploy_dashboard.yml` | On push to output/ | ~20 sec | Deploy HTML to GitHub Pages |

---

## 🔗 Related Repos

| Repo | Visibility | Purpose |
|------|-----------|---------|
| **alpha-engine** (this) | Public | Market data engine + dashboards |
| **trade-bot** | Private | 6-strategy screener, position sizing, risk management |
| **ai-trading-agent** | Private | 4-tier AI pipeline with TradingAgents 10-agent debate |

---

## ⚠️ Disclaimer

This is a **personal research tool**. Not financial advice. All investment decisions are your own responsibility. Past performance does not guarantee future results. The SEPA scoring system is based on publicly documented trading methodologies and does not constitute a recommendation to buy or sell any security.

---

<div align="center">

**Built by [Vamsi Madhabattula](https://github.com/VamsiKrishna2021)** · Alpha Engine v1.1 · March 2026

MIT License

</div>
