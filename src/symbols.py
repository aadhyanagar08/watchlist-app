# src/symbols.py
from typing import List

# Common aliases → Yahoo Finance tickers
ALIASES = {
    # S&P 500
    "S&P": "^GSPC",
    "S&P 500": "^GSPC",
    "SP500": "^GSPC",
    "SPX": "^GSPC",
    "GSPC": "^GSPC",
    "^SPX": "^GSPC",

    # US indices
    "NASDAQ": "^IXIC",
    "NASDAQ 100": "^NDX",
    "NDX": "^NDX",
    "DOW": "^DJI",
    "DJIA": "^DJI",
    "RUSSELL 2000": "^RUT",
    "RUT": "^RUT",

    # Canada
    "TSX": "^GSPTSE",
    "TSX COMPOSITE": "^GSPTSE",

    # India (examples)
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
}

def normalize_ticker(sym: str) -> str:
    s = (sym or "").strip()
    if not s:
        return ""
    u = s.upper().replace("’", "'")
    return ALIASES.get(u, u)

def normalize_list(items: List[str]) -> List[str]:
    out: List[str] = []
    for x in items:
        x = (x or "").strip()
        if not x:
            continue
        out.append(normalize_ticker(x))
    return out
