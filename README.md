# Portfolio Analytics Dashboard

A live-data financial analytics dashboard that automates computation of portfolio risk KPIs — Sharpe ratio, Beta, Max Drawdown, Alpha, Sortino, Tracking Error, and R² — across configurable asset universes and timeframes. Benchmarked to deliver **40%+ efficiency gains** over equivalent manual Excel workflows.

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Module Reference](#module-reference)
4. [KPI Definitions](#kpi-definitions)
5. [Data Pipeline Design](#data-pipeline-design)
6. [Benchmarking Methodology](#benchmarking-methodology)
7. [Configuration](#configuration)
8. [Running Locally](#running-locally)
9. [Testing](#testing)
10. [Known Limitations](#known-limitations)

---

## Overview

| | |
|---|---|
| **Stack** | Python 3.10+, Streamlit, yfinance, pandas, NumPy, PyYAML |
| **Data source** | Yahoo Finance via `yfinance` (live, no API key required) |
| **Persistence** | YAML watchlist (`data/watchlist.yaml`) |
| **Deployment** | Local (`streamlit run app.py`) or Streamlit Cloud |

The dashboard replaces a multi-step manual Excel workflow (price download → formula entry → chart creation → fundamental lookup) with a single automated pipeline that runs end-to-end in seconds.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        app.py (UI layer)                    │
│  Streamlit sidebar controls → ticker universe → chart/table │
└────────────────────┬────────────────────────────────────────┘
                     │ orchestrates
        ┌────────────┼────────────────────┐
        ▼            ▼                    ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│ data_sources │ │   metrics    │ │   fundamentals   │
│              │ │              │ │                  │
│ fetch_close_ │ │ Sharpe       │ │ P/E, D/E         │
│ many()       │ │ Sortino      │ │ Div Yield        │
│              │ │ Alpha/Beta   │ │ Net Margin       │
│ yfinance API │ │ Max Drawdown │ │ Expense Ratio    │
│ → pd.DataFrame│ │ Tracking Err│ │                  │
└──────────────┘ └──────────────┘ └──────────────────┘
        │                │                    │
        └────────────────┴────────────────────┘
                         │ combined DataFrame
                         ▼
              ┌──────────────────────┐
              │   helptext.py        │
              │   interpret_metric() │
              │   Plain-English      │
              │   KPI explanations   │
              └──────────────────────┘
                         │
              ┌──────────────────────┐
              │   benchmarking.py    │
              │   AnalysisBenchmark  │
              │   Efficiency logging │
              └──────────────────────┘

Supporting modules:
  storage.py     → YAML watchlist read/write
  symbols.py     → Ticker alias normalization (S&P 500 → ^GSPC)
  input_utils.py → Raw text parsing for ad-hoc ticker entry
```

---

## Module Reference

### `src/data_sources.py`
| Function | Description |
|---|---|
| `fetch_close_series(ticker, period)` | Downloads adjusted close prices for a single ticker via yfinance. Handles MultiIndex column edge cases. |
| `fetch_close_many(tickers, period)` | Batch fetches multiple tickers, concatenates into a single aligned DataFrame, silently skips failed tickers. |

**Design decision:** `threads=False` in yfinance download call reduces race conditions on repeated calls in Streamlit's execution model.

---

### `src/metrics.py`
All metrics operate on daily return series (`pd.Series`). Annualization uses `TRADING_DAYS = 252`.

| Function | Formula / Notes |
|---|---|
| `annualized_return(r)` | `mean(r) × 252` |
| `annualized_vol(r)` | `std(r, ddof=0) × √252` |
| `sharpe_ratio(r, rf)` | `(mean(r) - rf_daily) × 252 / (std(excess) × √252)` |
| `sortino_ratio(r, rf)` | Sharpe but denominator uses downside std only |
| `max_drawdown(prices)` | `min(cumulative / running_peak - 1)` |
| `tracking_error(r, rb)` | `std(r - rb, ddof=0) × √252` |
| `beta_alpha_r2(r, rb, rf)` | OLS of excess returns; alpha annualized from daily intercept; R² via `corr²` |
| `compute_all_metrics(prices, benchmark, rf)` | Orchestrator: iterates tickers, excludes benchmark, returns tidy DataFrame |

**Risk-free rate:** Applied as daily equivalent (`rf_annual / 252`) in Sharpe/Sortino/Alpha calculations.

---

### `src/fundamentals.py`
Fetches fundamental data from Yahoo Finance `info` dict.

| Output Column | Source Keys | Notes |
|---|---|---|
| P/E | `trailingPE` | Raw float |
| Forward P/E | `forwardPE` | Raw float |
| D/E | `debtToEquity` | Raw float |
| Div Yield | `dividendYield`, `trailingAnnualDividendYield` | Normalized to decimal via `_safe_dividend_yield()` |
| Net Profit Margin | `profitMargins`, `netMargins` | Normalized to decimal |
| Expense Ratio | `annualReportExpenseRatio`, `expenseRatio` | ETF-only; normalized to decimal |

**Dividend yield normalization (`_safe_dividend_yield`):** Yahoo returns inconsistent formats (e.g., `0.015` vs `1.5` for 1.5%). The function applies range-based heuristics: values ≥ 1.0 are divided by 100; values 0.2–1.0 are also divided by 100; values 0–0.2 are treated as already decimal. Falls back to `sum(last 12m dividends) / price` if all fields are missing.

---

### `src/helptext.py`
| Function | Purpose |
|---|---|
| `HELP` dict | Short tooltip strings for all 14 metrics (used in `st.column_config`) |
| `interpret_metric(name, value, context)` | Dispatcher: routes to per-metric interpreter, returns plain-English verdict |
| `interpret_*` functions | Threshold-based text for each KPI (e.g., Sharpe < 0.5 = "low", 1–2 = "good") |

---

### `src/benchmarking.py`
Measures automated pipeline runtime and computes efficiency gain vs. a calibrated manual baseline.

**Manual baseline (per ticker):**
| Task | Time |
|---|---|
| Price download + Excel paste | 45s |
| Metric calculation (formulas) | 90s |
| Fundamentals lookup + entry | 60s |
| Chart creation | 45s |
| **Total** | **240s (~4 min)** |

`AnalysisBenchmark` is a context manager wrapping the fetch + compute block. On exit it computes:

```
efficiency_gain = (manual_time - automated_time) / manual_time × 100
```

Results are displayed as an `st.info` banner and expanded performance log in the UI.

---

### `src/storage.py`
| Function | Description |
|---|---|
| `load_watchlist()` | Reads `data/watchlist.yaml`; initializes missing categories; normalizes tickers to uppercase |
| `save_watchlist(data)` | Writes back to YAML; deduplicates and sorts tickers; creates parent directory if absent |

`DEFAULT_CATEGORIES` defines the canonical asset class taxonomy (US Equities, Bonds, Gold, etc.).

---

### `src/symbols.py`
Maps common index names and aliases to Yahoo Finance ticker symbols.

```python
normalize_ticker("S&P 500")  # → "^GSPC"
normalize_ticker("Nasdaq 100")  # → "^NDX"
normalize_ticker("TSX")  # → "^GSPTSE"
```

---

## KPI Definitions

| KPI | Formula | Interpretation |
|---|---|---|
| Ann. Return | `mean(daily_r) × 252` | Total return if held for one year at this average rate |
| Sharpe Ratio | `(Ann. Return - rf) / Ann. Vol` | Risk-adjusted return per unit of total risk |
| Sortino Ratio | `(Ann. Return - rf) / Downside Vol` | Like Sharpe but only penalizes downside volatility |
| Volatility | `std(daily_r) × √252` | Annualized dispersion of daily returns |
| Max Drawdown | `min(equity / peak - 1)` | Worst loss from peak to trough over the period |
| Tracking Error | `std(r - r_bench) × √252` | Active risk vs benchmark |
| Alpha | `(daily_intercept) × 252` | Risk-adjusted outperformance vs benchmark |
| Beta | `cov(r, r_b) / var(r_b)` | Market sensitivity; 1.0 = market-like |
| R² | `corr(r, r_b)²` | % of return variance explained by benchmark |

---

## Data Pipeline Design

```
User input (tickers + period)
        │
        ▼
normalize_ticker() / normalize_list()       [symbols.py]
        │
        ▼
fetch_close_many(tickers, period)           [data_sources.py]
        │  → pd.DataFrame: dates × tickers (adjusted close)
        ▼
compute_all_metrics(prices, benchmark, rf)  [metrics.py]
        │  → pd.DataFrame: tickers × KPIs
        ▼
fetch_fundamentals_many(tickers)            [fundamentals.py]
        │  → pd.DataFrame: tickers × fundamentals
        ▼
metrics.join(fundamentals)                  [app.py]
        │  → combined pd.DataFrame
        ▼
Display (st.dataframe + column_config)      [app.py]
        │
        ▼
interpret_metric() per ticker               [helptext.py]
```

---

## Benchmarking Methodology

On each run, `AnalysisBenchmark` records wall-clock time for the full fetch + compute cycle and displays:

```
⚡ Analyzed 10 ticker(s) in 8.3s — est. 39.7 min saved vs manual Excel workflow (96% faster)
```

The performance log expander shows the breakdown:

| Field | Value |
|---|---|
| Tickers analyzed | N |
| Automated time | X seconds |
| Manual baseline | N × 240 seconds |
| Efficiency gain | (manual - auto) / manual × 100% |

This provides a concrete, auditable basis for the efficiency claim in documentation and stakeholder reporting.

---

## Configuration

### `data/watchlist.yaml`
Stores the persistent watchlist. Edit directly or use the sidebar UI.

```yaml
US Equities:
  - AAPL
  - MSFT
Canada Equities:
  - ENB
Gold:
  - GLD
```

### Sidebar options
| Control | Effect |
|---|---|
| Timeframe | 1y / 3y / 5y lookback period |
| Risk-free rate | Annual % used in Sharpe/Sortino/Alpha |
| Benchmark | Any valid Yahoo ticker or alias |
| Quick Compare | Ad-hoc tickers override category selection |

---

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run
streamlit run app.py
```

**requirements.txt:**
```
streamlit
yfinance
pandas
numpy
pyyaml
```

---

## Testing

```bash
# Run all tests (from project root)
pytest tests/

# Individual test files
pytest tests/test_fundamentals.py -v
pytest tests/test_symbols.py -v
```

`test_fundamentals.py` uses `monkeypatch` to mock `yfinance.Ticker`, validating:
- Dividend yield normalization (percent vs decimal format)
- Expense ratio handling for ETF vs equity
- Graceful NaN handling for missing/unknown tickers

`test_symbols.py` validates alias normalization for common index names.

---

## Known Limitations

| Limitation | Detail |
|---|---|
| Data dependency | All data from Yahoo Finance; subject to their availability and accuracy |
| Dividend yield normalization | Heuristic-based; may misclassify very high-yield instruments |
| Fundamentals coverage | ETF expense ratios often unavailable; forward P/E inconsistently populated |
| No caching | Each page load re-fetches data; add `@st.cache_data` for production use |
| Single-currency | No FX adjustment for international tickers |
| Manual baseline | Conservative estimate; actual savings vary by analyst experience and tooling |
