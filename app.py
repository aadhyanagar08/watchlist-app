# app.py
import streamlit as st
import pandas as pd
import numpy as np

from src.storage import load_watchlist, save_watchlist, DEFAULT_CATEGORIES
from src.data_sources import fetch_close_many
from src.metrics import (
    compute_all_metrics, daily_returns, TRADING_DAYS, annualized_return
)
from src.fundamentals import compute_fundamentals
from src.helptext import HELP, interpret_metric
from src.input_utils import parse_ticker_list
from src.fundamentals import fetch_fundamentals_many
from src.symbols import normalize_list, normalize_ticker


st.set_page_config(page_title="Custom Watchlist", layout="wide")

# ======================
# Sidebar controls
# ======================
st.sidebar.title("Watchlist Controls")

period = st.sidebar.selectbox("Timeframe", ["1y", "3y", "5y"], index=1)
rf = st.sidebar.number_input("Risk-free rate (annual, %)", value=0.0, step=0.25) / 100.0

st.sidebar.markdown("### Benchmark")
benchmark_input = st.sidebar.text_input(
    "Benchmark (ticker or name)", value="SPY", help="Examples: SPY, VOO, ^GSPC, 'S&P 500'"
)
benchmark = normalize_ticker(benchmark_input)

st.sidebar.markdown("---")
st.sidebar.subheader("Manage Categories & Tickers (saved to YAML)")

data = load_watchlist()

with st.sidebar.form("add_form", clear_on_submit=True):
    cat = st.selectbox("Category", DEFAULT_CATEGORIES)
    new_ticker = st.text_input("Add ticker (e.g., AAPL)")
    submitted = st.form_submit_button("Add")
    if submitted and new_ticker.strip():
        nt = new_ticker.strip().upper()
        if nt not in data[cat]:
            data[cat].append(nt)
            save_watchlist(data)
            st.success(f"Added {nt} to {cat}")

with st.sidebar.expander("Remove ticker"):
    cat_r = st.selectbox("Category to edit", DEFAULT_CATEGORIES, key="remove_sel")
    if data[cat_r]:
        to_remove = st.selectbox("Ticker", data[cat_r], key="remove_ticker")
        if st.button("Remove"):
            data[cat_r] = [t for t in data[cat_r] if t != to_remove]
            save_watchlist(data)
            st.success(f"Removed {to_remove} from {cat_r}")
    else:
        st.caption("No tickers in this category.")

st.sidebar.markdown("---")
selected_cats = st.sidebar.multiselect(
    "Include categories", DEFAULT_CATEGORIES, default=DEFAULT_CATEGORIES
)

st.sidebar.markdown("---")
st.sidebar.subheader("Quick Compare (ad-hoc)")
user_tickers_text = st.sidebar.text_area(
    "Tickers (comma or newline separated)",
    value="AAPL, MSFT, VTI",
    height=80,
    help="Example: AAPL, MSFT, VTI",
)

# ======================
# Main page
# ======================
st.title("📊 Custom Watchlist")

with st.expander("📘 Metrics Glossary"):
    st.write("""
- **P/E** — Price divided by trailing 12-month earnings per share.
- **D/E** — Total debt divided by shareholders’ equity.
- **Div Yield** — Annual dividends divided by price.
- **Net Profit Margin** — Net income divided by revenue.
- **Expense Ratio** — Annual ETF fee as a % of assets.

- **Ann. Return** — Average daily return annualized (×252).
- **Sharpe** — Excess return per unit of total volatility.
- **Sortino** — Excess return per unit of downside volatility.
- **Volatility** — Annualized std dev of daily returns.
- **Max Drawdown** — Worst peak-to-trough decline.
- **Tracking Error** — Volatility of (asset − benchmark) returns (annualized).
- **Alpha** — Annualized intercept vs. benchmark (risk-adjusted outperformance).
- **Beta** — Sensitivity to the benchmark.
- **R²** — % of variance explained by the benchmark.
""")

# Build the working universe:
user_tickers = normalize_list(parse_ticker_list(user_tickers_text))
if not user_tickers:
    # Fall back to saved categories if the ad-hoc list is empty
    for c in selected_cats:
        user_tickers.extend(data.get(c, []))
    user_tickers = sorted(set(user_tickers))

if not user_tickers:
    st.info("Add some tickers (Quick Compare) or via Categories in the sidebar to get started.")
    st.stop()

# Always fetch benchmark too (if provided)
tickers_to_fetch = sorted(set(user_tickers + ([benchmark] if benchmark else [])))

# Fetch prices
with st.spinner("Fetching price history…"):
    prices = fetch_close_many(tickers_to_fetch, period=period)

if prices.empty:
    st.error("Could not fetch any data. Check tickers, benchmark, or timeframe.")
    st.stop()

# Warn if anything failed to load
missing = sorted(set(tickers_to_fetch) - set(prices.columns))
if missing:
    st.warning(
        "Could not load data for: " + ", ".join(missing) +
        ". Tip: use proper Yahoo tickers (e.g., S&P 500 → ^GSPC)."
    )

# Compute performance metrics (returns-based)
metrics = compute_all_metrics(prices, benchmark=benchmark, rf_annual=rf)

# Fundamentals for the same tickers shown in the metrics table (metrics excludes the benchmark)
fund_tickers = metrics.index.tolist()
funds = fetch_fundamentals_many(fund_tickers)
combined = metrics.join(funds, how="left")

# Column config with help tooltips and formatting
col_config = {
    "Ann. Return":       st.column_config.NumberColumn("Ann. Return", help=HELP["Ann. Return"], format="%.2f%%"),
    "Sharpe":            st.column_config.NumberColumn("Sharpe", help=HELP["Sharpe"], format="%.2f"),
    "Sortino":           st.column_config.NumberColumn("Sortino", help=HELP["Sortino"], format="%.2f"),
    "Volatility":        st.column_config.NumberColumn("Volatility", help=HELP["Volatility"], format="%.2f%%"),
    "Max Drawdown":      st.column_config.NumberColumn("Max Drawdown", help=HELP["Max Drawdown"], format="%.2f%%"),
    "Tracking Error":    st.column_config.NumberColumn("Tracking Error", help=HELP["Tracking Error"], format="%.2f%%"),
    "Alpha":             st.column_config.NumberColumn("Alpha", help=HELP["Alpha"], format="%.2f%%"),
    "Beta":              st.column_config.NumberColumn("Beta", help=HELP["Beta"], format="%.2f"),
    "R²":                st.column_config.NumberColumn("R²", help=HELP["R²"], format="%.2f"),
    "P/E":               st.column_config.NumberColumn("P/E", help=HELP["P/E"], format="%.2f"),
    "D/E":               st.column_config.NumberColumn("D/E", help=HELP["D/E"], format="%.2f"),
    "Div Yield":         st.column_config.NumberColumn("Div Yield", help=HELP["Div Yield"], format="%.2f%%"),
    "Net Profit Margin": st.column_config.NumberColumn("Net Profit Margin", help=HELP["Net Profit Margin"], format="%.2f%%"),
    "Expense Ratio":     st.column_config.NumberColumn("Expense Ratio", help=HELP["Expense Ratio"], format="%.2f%%"),
}

# Convert decimal % columns to human % for display
display_df = combined.copy()
for pct_col in [
    "Ann. Return", "Volatility", "Max Drawdown", "Tracking Error",
    "Alpha", "Div Yield", "Net Profit Margin", "Expense Ratio"
]:
    if pct_col in display_df.columns:
        display_df[pct_col] = display_df[pct_col] * 100.0

st.subheader("All Metrics (Performance + Fundamentals)")
st.caption("Tip: Click column headers to sort. Download below for a clean CSV.")
st.dataframe(display_df, use_container_width=True, column_config=col_config)

# Downloads
st.download_button(
    "⬇️ Download Combined CSV",
    data=combined.to_csv(index=True).encode("utf-8"),
    file_name="watchlist_metrics_fundamentals.csv",
    mime="text/csv",
)

# Time-series chart (resilient to missing benchmark)
st.subheader("Time-Series")
valid_choices = sorted([t for t in user_tickers if t in prices.columns])
if not valid_choices:
    st.info("No valid tickers loaded to chart.")
else:
    pick = st.selectbox("Choose a ticker to chart", valid_choices)
    series_to_plot = []
    if pick in prices.columns:
        series_to_plot.append(pick)
    if benchmark and (benchmark in prices.columns) and (benchmark != pick):
        series_to_plot.append(benchmark)
    else:
        st.caption(f"Benchmark '{benchmark_input}' not available; charting {pick} only.")
    if series_to_plot:
        st.line_chart(prices[series_to_plot].dropna(), height=350)

# Per-ticker Insights (explain *all* metrics in plain English)
st.subheader("📘 Insights (per ticker)")
if not combined.empty:
    ex_ticker = st.selectbox("Pick a ticker", list(combined.index))
    # Benchmark annualized return for context in Ann. Return interpretation
    bench_ann_ret = None
    if benchmark in prices.columns:
        bench_ann_ret = annualized_return(prices[benchmark].pct_change().dropna())
    context = {"bench_ann_return": bench_ann_ret}

    explain_order = [
        "Ann. Return", "Sharpe", "Sortino", "Volatility", "Max Drawdown",
        "Tracking Error", "Alpha", "Beta", "R²",
        "P/E", "D/E", "Div Yield", "Net Profit Margin", "Expense Ratio"
    ]
    explain_order = [c for c in explain_order if c in combined.columns]
    row = combined.loc[ex_ticker, explain_order]

    for col in explain_order:
        val = row[col]
        # pass the raw decimal values (not the 100x display copies)
        vfloat = float(val) if pd.notna(val) else np.nan
        st.markdown(f"- **{col}** — {interpret_metric(col, vfloat, context)}")
