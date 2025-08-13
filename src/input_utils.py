# src/input_utils.py
def parse_ticker_list(text: str) -> list[str]:
    if not text:
        return []
    parts = [p.strip().upper() for p in text.replace("\n", ",").split(",")]
    return [p for p in parts if p]
