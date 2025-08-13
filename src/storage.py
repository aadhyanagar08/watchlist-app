# src/storage.py (patch load_watchlist)
from pathlib import Path
import yaml

WATCHLIST_PATH = Path("data/watchlist.yaml")

DEFAULT_CATEGORIES = [
    "US Equities",
    "International Equities",
    "Emerging Market Equities",
    "Global Factor Equities",
    "Canada Equities",
    "Long-Duration Bonds",
    "Aggregate Bonds",
    "Short-Term Credit",
    "Gold",
    "Silver",
]

def load_watchlist() -> dict:
    data = {}
    try:
        if WATCHLIST_PATH.exists():
            with WATCHLIST_PATH.open("r") as f:
                data = yaml.safe_load(f) or {}
    except Exception:
        # Corrupt or unreadable YAML -> fall back to empty (defaults below)
        data = {}

    # ensure all categories exist and normalize tickers
    for c in DEFAULT_CATEGORIES:
        data.setdefault(c, [])
        data[c] = sorted({(t or "").strip().upper() for t in data[c] if t})
    return data

def save_watchlist(data: dict) -> None:
    out = {
        c: sorted({(t or "").strip().upper() for t in data.get(c, []) if t})
        for c in DEFAULT_CATEGORIES
    }
    WATCHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with WATCHLIST_PATH.open("w") as f:
        yaml.safe_dump(out, f, sort_keys=False)
