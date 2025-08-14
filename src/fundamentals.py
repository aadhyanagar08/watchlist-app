# src/fundamentals.py
from __future__ import annotations
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import yfinance as yf

# Map our column names -> likely yfinance keys
FUND_KEYS_MAP: Dict[str, List[str]] = {
    "P/E": ["trailingPE"],
    "Forward P/E": ["forwardPE"],
    "D/E": ["debtToEquity"],
    "Div Yield": ["dividendYield", "trailingAnnualDividendYield"],  # decimals, e.g., 0.018
    "Net Profit Margin": ["profitMargins", "netMargins"],           # decimals
    # Expense ratio handled specially below (ETF-aware)
}

COLUMNS = ["P/E", "Forward P/E", "D/E", "Div Yield", "Net Profit Margin", "Expense Ratio"]

def _to_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return np.nan
        return float(x)
    except Exception:
        return np.nan

def _safe_pick(info: Dict[str, Any], keys: List[str]) -> Optional[float]:
    for k in keys:
        v = info.get(k)
        if v is not None:
            return _to_float(v)
    return np.nan

def _normalize_decimal(v: Optional[float]) -> Optional[float]:
    """
    Keep percent-like values as decimals for internal use.
    If v in [0,1] -> keep.
    If 1 < v <= 100 -> assume percent, convert to decimal.
    Else -> return as-is (NaN or other).
    """
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return np.nan
    if 0.0 <= v <= 1.0:
        return float(v)
    if 1.0 < v <= 100.0:
        return float(v) / 100.0
    return float(v)


def fetch_fundamentals_one(ticker: str) -> Dict[str, Any]:
    t = (ticker or "").strip().upper()
    if not t:
        return {}

    # Pull info (yfinance has both .info and .get_info across versions)
    try:
        tk = yf.Ticker(t)
        info = tk.get_info() if hasattr(tk, "get_info") else getattr(tk, "info", {}) or {}
    except Exception:
        info = {}

    row: Dict[str, Any] = {"Ticker": t}

    # Basic fields from info
    for label, keys in FUND_KEYS_MAP.items():
        row[label] = _safe_pick(info, keys)

    # Expense Ratio (ETF-aware): try common keys
    er = _to_float(
        info.get("annualReportExpenseRatio")
        or info.get("expenseRatio")
        or info.get("fundExpenseRatio")
    )
    quote_type = (info.get("quoteType") or "").upper()
    if quote_type == "ETF":
        row["Expense Ratio"] = _normalize_decimal(er)
    else:
        # Hide ER for non-ETFs unless a valid number exists
        row["Expense Ratio"] = _normalize_decimal(er) if er is not None and not np.isnan(er) else np.nan

    # Normalize percent-like fields to decimals
    for pct_label in ["Div Yield", "Net Profit Margin"]:
        row[pct_label] = _normalize_decimal(row.get(pct_label))

    # Numeric ratios as floats
    for num_label in ["P/E", "Forward P/E", "D/E"]:
        row[num_label] = _to_float(row.get(num_label))

    return row

def fetch_fundamentals_many(tickers: List[str]) -> pd.DataFrame:
    records: List[Dict[str, Any]] = []
    for t in tickers:
        try:
            rec = fetch_fundamentals_one(t)
            if rec:
                records.append(rec)
        except Exception:
            continue

    if not records:
        return pd.DataFrame(columns=["Ticker"] + COLUMNS).set_index("Ticker")

    df = pd.DataFrame(records).set_index("Ticker")

    # Ensure all expected columns exist in a consistent order
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = np.nan
    df = df[COLUMNS]
    return df

# Alias for existing app code using the old name
def compute_fundamentals(tickers: List[str]) -> pd.DataFrame:
    return fetch_fundamentals_many(tickers)

__all__ = ["fetch_fundamentals_one", "fetch_fundamentals_many", "compute_fundamentals"]
