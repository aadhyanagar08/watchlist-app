# src/benchmarking.py
"""
Benchmarking utility: measures automated dashboard computation time
and compares against a calibrated manual-analysis baseline.

Manual baseline assumptions (conservative, documented):
- Per-ticker price download + paste into Excel:     ~45 seconds
- Per-ticker metric calculation (Sharpe, Beta etc): ~90 seconds
- Per-ticker fundamental lookup + entry:            ~60 seconds
- Per-ticker chart creation:                        ~45 seconds
- Total manual time per ticker:                     ~240 seconds (4 minutes)

These estimates are based on standard financial analyst Excel workflows
for computing risk-adjusted return metrics from raw price data.
"""
from __future__ import annotations
import time
from typing import Optional

# Manual baseline: seconds per ticker for equivalent Excel analysis
MANUAL_SECONDS_PER_TICKER = 240.0  # 4 minutes per ticker (conservative)


class AnalysisBenchmark:
    """
    Context manager that times a block of code and reports
    efficiency gain vs the manual baseline.

    Usage:
        with AnalysisBenchmark(n_tickers=10) as bm:
            ... run analysis ...
        print(bm.summary())
    """

    def __init__(self, n_tickers: int):
        self.n_tickers = max(1, n_tickers)
        self.elapsed: float = 0.0
        self._start: Optional[float] = None

    def __enter__(self) -> "AnalysisBenchmark":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_) -> None:
        self.elapsed = time.perf_counter() - (self._start or 0.0)

    @property
    def manual_time(self) -> float:
        """Estimated manual time in seconds for the same analysis."""
        return self.n_tickers * MANUAL_SECONDS_PER_TICKER

    @property
    def time_saved(self) -> float:
        """Seconds saved vs manual baseline."""
        return max(0.0, self.manual_time - self.elapsed)

    @property
    def efficiency_gain_pct(self) -> float:
        """
        Percentage reduction in analysis time vs manual baseline.
        Formula: (manual - automated) / manual * 100
        """
        if self.manual_time <= 0:
            return 0.0
        return (self.time_saved / self.manual_time) * 100.0

    def summary(self) -> dict:
        return {
            "tickers_analyzed": self.n_tickers,
            "automated_seconds": round(self.elapsed, 2),
            "manual_baseline_seconds": round(self.manual_time, 2),
            "time_saved_seconds": round(self.time_saved, 2),
            "efficiency_gain_pct": round(self.efficiency_gain_pct, 1),
        }

    def caption(self) -> str:
        """Short human-readable caption for display in the dashboard."""
        mins_saved = self.time_saved / 60
        return (
            f"⚡ Analyzed {self.n_tickers} ticker(s) in "
            f"{self.elapsed:.1f}s — "
            f"est. {mins_saved:.1f} min saved vs manual Excel workflow "
            f"({self.efficiency_gain_pct:.0f}% faster)"
        )


__all__ = ["AnalysisBenchmark", "MANUAL_SECONDS_PER_TICKER"]