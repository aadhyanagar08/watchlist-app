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
        threads=False,  # avoids some flaky multi-threading behavior
    )

    if df is None or df.empty:
        raise ValueError(f"No data for {ticker}")

    # Handle both Series and DataFrame cases for "Close"
    if "Close" not in df.columns:
        # Sometimes yfinance returns MultiIndex columns; try to flatten/access
        # If it's a MultiIndex, columns like ('Close', <something>) may exist
        close_cols = [c for c in df.columns if isinstance(c, tuple) and c[0] == "Close"]
        if close_cols:
            # take the first close column
            s = df[close_cols[0]].dropna()
        else:
            raise ValueError(f"No 'Close' column for {ticker}")
    else:
        close_obj = df["Close"]
        if isinstance(close_obj, pd.DataFrame):
            # If it's a DataFrame (e.g., MultiIndex columns), take first column
            s = close_obj.iloc[:, 0].dropna()
        else:
            s = close_obj.dropna()

    # Ensure we return a Series and set its name to the ticker
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
            # keep going if one ticker fails (delisted/typo/rate-limit)
            continue

    if not frames:
        return pd.DataFrame()

    prices = pd.concat(frames, axis=1).sort_index().dropna(how="all")
    return prices
