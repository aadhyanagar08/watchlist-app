# Watchlist App

A **Streamlit-powered** financial dashboard for tracking and analyzing your own watchlist of stocks and ETFs.  
This tool allows users to input custom tickers, select a benchmark, fetch historical price data from **Yahoo Finance**, and compare performance metrics over a selected time horizon.

---

## Features

### 1. Custom Watchlist
- Add any Yahoo Finance-supported ticker symbol (e.g., `AAPL`, `MSFT`, `VTI`, `^GSPC`)
- Organize your own investment universe — no preloaded lists

### 2. Benchmark Comparison
- Compare your picks to market benchmarks like:
  - **S&P 500** → `^GSPC`
  - **NASDAQ 100** → `^NDX`
  - **Dow Jones** → `^DJI`
  - **TSX Composite** → `^GSPTSE`
  - **Russell 2000** → `^RUT`

### 3. Performance Metrics
- **Daily Returns**
- **Annualized Volatility**
- **Sharpe Ratio**
- **Sortino Ratio**
- **Maximum Drawdown**
- **Tracking Error** vs benchmark
- **Alpha** & **Beta** vs benchmark
- **R²** (coefficient of determination)

### 4. Visual Insights
- Interactive **line chart** for price history
- Clean data tables with calculated metrics

---

## Tech Stack

- **Python 3.9+**
- **Streamlit** – web app framework
- **pandas** / **numpy** – data analysis
- **yfinance** – market data retrieval
- **matplotlib** / **Altair** – visualization

---

### Installation & Setup

### 1️Clone the repository
```bash
git clone https://github.com/your-username/watchlist-app.git
cd watchlist-app
