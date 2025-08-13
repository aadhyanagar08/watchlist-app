import streamlit as st
import pandas as pd
from src.storage import load_watchlist, save_watchlist, DEFAULT_CATEGORIES
from src.data_sources import fetch_close_many
from src.metrics import compute_all_metrics, daily_returns, TRADING_DAYS

st.set_page_config(page_title="Custom Watchlist", layout="wide")

# ---- Sidebar controls
st.sidebar.title("Watchlist Controls")

period = st.sidebar.selectbox("Timeframe", ["1y","3y","5y"], index=1)
benchmark = st.sidebar.text_input("Benchmark ticker", value="SPY").strip().upper()
rf = st.sidebar.number_input("Risk-free rate (annual, %)", value=0.0, step=0.25) / 100.0

st.sidebar.markdown("---")
st.sidebar.subheader("Manage Categories & Tickers")

data = load_watchlist()

# Add a ticker
with st.sidebar.form("add_form", clear_on_submit=True):
    cat = st.selectbox("Category", DEFAULT_CATEGORIES)
    new_ticker = st.text_input("Add ticker (e.g., AAPL)")
    submitted = st.form_submit_button("Add")
    if submitted and new_ticker.strip():
        new_ticker = new_ticker.strip().upper()
        if new_ticker not in data[cat]:
            data[cat].append(new_ticker)
            save_watchlist(data)
            st.success(f"Added {new_ticker} to {cat}")

# Remove a ticker (optional small helper)
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
selected_cats = st.sidebar.multiselect("Include categories", DEFAULT_CATEGORIES, default=DEFAULT_CATEGORIES)

# ---- Main page
st.title("📊 Custom Watchlist")

# Glossary (one-line explanations)
with st.expander("Metrics Glossary (one-liners)"):
    st.write("""
- **Ann. Return** — Average daily return annualized (×252).
- **Sharpe** — Risk-adjusted return using total volatility (excess return / volatility).
- **Sortino** — Risk-adjusted return using downside volatility only.
- **Volatility** — Annualized standard deviation of daily returns.
- **Max Drawdown** — Worst peak-to-trough decline in the price series.
- **Tracking Error** — Volatility of (asset − benchmark) returns (annualized).
- **Alpha** — Annualized intercept from regressing excess returns vs benchmark (skill beyond beta).
- **Beta** — Sensitivity of the asset to the benchmark (slope of regression).
- **R²** — Fraction of return variance explained by the benchmark.
""")

# Build ticker universe
universe = []
for c in selected_cats:
    universe.extend(data.get(c, []))
# Ensure benchmark is fetched too
tickers_to_fetch = sorted(set(universe + ([benchmark] if benchmark else [])))

if not universe:
    st.info("Add some tickers in the sidebar to get started.")
    st.stop()

# Fetch prices
with st.spinner("Fetching price history…"):
    prices = fetch_close_many(tickers_to_fetch, period=period)

if prices.empty:
    st.error("Could not fetch any data. Check tickers/timeframe.")
    st.stop()

# Compute metrics
metrics = compute_all_metrics(prices, benchmark=benchmark, rf_annual=rf)

# Display metrics table (sortable)
st.subheader("Metrics Table")
st.caption("Tip: Click column headers to sort. Use the download below for a CSV without this guide.")
st.dataframe(metrics.style.format({
    "Ann. Return": "{:.2%}",
    "Sharpe": "{:.2f}",
    "Sortino": "{:.2f}",
    "Volatility": "{:.2%}",
    "Max Drawdown": "{:.2%}",
    "Tracking Error": "{:.2%}",
    "Alpha": "{:.2%}",
    "Beta": "{:.2f}",
    "R²": "{:.2f}",
}), use_container_width=True)

# Download CSV (data only)
csv = metrics.to_csv(index=True).encode("utf-8")
st.download_button("⬇️ Download CSV (data only)", data=csv, file_name="watchlist_metrics.csv", mime="text/csv")

# Time-series chart
st.subheader("Time-Series")
pick = st.selectbox("Choose a ticker to chart", sorted(universe))
if pick in prices:
    st.line_chart(prices[[pick, benchmark]].dropna(), height=350)
