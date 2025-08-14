# src/data_sources.py
from typing import List
import pandas as pd
import yfinance as yf

def fetch_close_series(ticker: str, period: str = "3y") -> pd.Series:
    df = yf.download(
        ticker,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=False,  # reduces flaky behavior
    )
    if df is None or df.empty:
        raise ValueError(f"No data for {ticker}")

    # Handle cases where "Close" may be a DataFrame or MultiIndex
    if "Close" not in df.columns:
        close_cols = [c for c in df.columns if isinstance(c, tuple) and c[0] == "Close"]
        if close_cols:
            s = df[close_cols[0]].dropna()
        else:
            raise ValueError(f"No 'Close' column for {ticker}")
    else:
        close_obj = df["Close"]
        s = close_obj.iloc[:, 0].dropna() if isinstance(close_obj, pd.DataFrame) else close_obj.dropna()

    if not isinstance(s, pd.Series):
        s = pd.Series(s, name=ticker)
    s.name = ticker
    return s

def fetch_close_many(tickers: List[str], period: str = "3y") -> pd.DataFrame:
    frames = []
    for t in tickers:
        t = (t or "").strip().upper()
        if not t:
            continue
        try:
            frames.append(fetch_close_series(t, period=period))
        except Exception:
            continue
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, axis=1).sort_index().dropna(how="all")

__all__ = ["fetch_close_series", "fetch_close_many"]
