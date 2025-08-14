# src/helptext.py
from __future__ import annotations
from typing import Dict, Optional
import math
import numpy as np

# --- 1) Tooltips for ALL metrics (shown as "?" help in table headers) ---
HELP: Dict[str, str] = {
    # Performance
    "Ann. Return": "Average daily return annualized (×252).",
    "Sharpe": "Excess return per unit of total volatility (higher is better).",
    "Sortino": "Excess return per unit of downside volatility (higher is better).",
    "Volatility": "Annualized standard deviation of daily returns.",
    "Max Drawdown": "Worst peak-to-trough decline in equity curve.",
    "Tracking Error": "Volatility of (asset − benchmark) returns, annualized.",
    "Alpha": "Annualized out/under-performance vs benchmark (risk-adjusted).",
    "Beta": "Sensitivity to benchmark; ~1.0 ≈ market-like.",
    "R²": "Share of return variance explained by benchmark (0–1).",

    # Fundamentals
    "P/E": "Price ÷ trailing 12-month earnings per share.",
    "D/E": "Total debt ÷ shareholders’ equity.",
    "Div Yield": "Annual dividends ÷ price.",
    "Net Profit Margin": "Net income ÷ revenue.",
    "Expense Ratio": "ETF’s annual fee as % of assets (lower is better).",
}

# --- 2) Value → short interpretation per metric ---
def _pct(x: Optional[float]) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x*100:.2f}%"

def _num(x: Optional[float], nd=2) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{nd}f}"

def interpret_r2(v: Optional[float]) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "R² unavailable—insufficient overlap with the benchmark."
    if v >= 0.8:  return "High linkage: behaves much like the benchmark; limited diversification."
    if v >= 0.5:  return "Moderate linkage: both market and asset-specific drivers."
    return "Low linkage: moves differently from the benchmark; may add diversification."

def interpret_beta(v: Optional[float]) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)): return "Beta unavailable."
    if v < 0.8:   return f"β={_num(v)}: defensive vs market (less sensitive)."
    if v <= 1.2:  return f"β={_num(v)}: market-like sensitivity."
    return f"β={_num(v)}: aggressive vs market (more sensitive)."

def interpret_alpha(v: Optional[float]) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)): return "Alpha unavailable."
    if v > 0.02:  return f"α={_pct(v)}: meaningful outperformance vs benchmark."
    if v > 0.0:   return f"α={_pct(v)}: slight outperformance."
    if v < -0.02: return f"α={_pct(v)}: meaningful underperformance."
    return f"α={_pct(v)}: roughly in line with benchmark."

def interpret_sharpe(v: Optional[float]) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)): return "Sharpe unavailable."
    if v < 0:     return f"Sharpe={_num(v)}: risk-adjusted performance below risk-free."
    if v < 0.5:   return f"Sharpe={_num(v)}: low risk-adjusted return."
    if v < 1.0:   return f"Sharpe={_num(v)}: fair."
    if v < 2.0:   return f"Sharpe={_num(v)}: good."
    return f"Sharpe={_num(v)}: excellent."

def interpret_sortino(v: Optional[float]) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)): return "Sortino unavailable."
    if v < 0:     return f"Sortino={_num(v)}: downside-adjusted return is poor."
    if v < 0.5:   return f"Sortino={_num(v)}: low."
    if v < 1.0:   return f"Sortino={_num(v)}: fair."
    if v < 2.0:   return f"Sortino={_num(v)}: good."
    return f"Sortino={_num(v)}: excellent."

def interpret_volatility(v: Optional[float]) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)): return "Volatility unavailable."
    # v is annualized decimal (e.g., 0.18 = 18%)
    if v < 0.10:  return f"Vol={_pct(v)}: low volatility."
    if v < 0.20:  return f"Vol={_pct(v)}: moderate volatility."
    return f"Vol={_pct(v)}: high volatility."

def interpret_maxdd(v: Optional[float]) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)): return "Max drawdown unavailable."
    # v is negative decimal
    if v > -0.10:  return f"MaxDD={_pct(v)}: shallow drawdowns."
    if v > -0.30:  return f"MaxDD={_pct(v)}: typical equity drawdowns."
    return f"MaxDD={_pct(v)}: deep drawdowns; higher pain risk."

def interpret_tracking_error(v: Optional[float]) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)): return "Tracking error unavailable."
    if v < 0.03:   return f"TE={_pct(v)}: closely tracks the benchmark."
    if v < 0.06:   return f"TE={_pct(v)}: moderate deviation vs benchmark."
    return f"TE={_pct(v)}: large active risk vs benchmark."

def interpret_ann_return(v: Optional[float], bench: Optional[float]=None) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)): return "Annualized return unavailable."
    if bench is None or (isinstance(bench, float) and math.isnan(bench)):
        return f"Ann. Return={_pct(v)}."
    diff = v - bench
    sign = "above" if diff >= 0 else "below"
    return f"Ann. Return={_pct(v)} ({_pct(abs(diff))} {sign} benchmark)."

def interpret_pe(v: Optional[float]) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)): return "P/E unavailable or not meaningful (e.g., negative earnings)."
    if v < 10:    return f"P/E={_num(v)}: low (may indicate value or risk)."
    if v <= 25:   return f"P/E={_num(v)}: typical range."
    return f"P/E={_num(v)}: high (priced for growth)."

def interpret_de(v: Optional[float]) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)): return "D/E unavailable."
    if v < 0.5:   return f"D/E={_num(v)}: low leverage."
    if v <= 1.0:  return f"D/E={_num(v)}: moderate leverage."
    return f"D/E={_num(v)}: high leverage."

def interpret_div_yield(v: Optional[float]) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)): return "Dividend yield unavailable."
    if v < 0.02:  return f"Yield={_pct(v)}: low income."
    if v <= 0.04: return f"Yield={_pct(v)}: moderate income."
    return f"Yield={_pct(v)}: high income (check sustainability)."

def interpret_net_margin(v: Optional[float]) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)): return "Net margin unavailable."
    if v < 0.05:  return f"Margin={_pct(v)}: thin margins."
    if v <= 0.20: return f"Margin={_pct(v)}: healthy margins."
    return f"Margin={_pct(v)}: strong margins."

def interpret_expense_ratio(v: Optional[float]) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)): return "Expense ratio unavailable (often only for ETFs)."
    if v <= 0.0015: return f"ER={_pct(v)}: very low cost."
    if v <= 0.0040: return f"ER={_pct(v)}: typical for broad ETFs."
    return f"ER={_pct(v)}: high cost; consider cheaper alternatives."

# Unified dispatcher
def interpret_metric(name: str, value: Optional[float], context: Dict[str, float] | None = None) -> str:
    ctx = context or {}
    name = name.strip()
    if name == "R²":             return interpret_r2(value)
    if name == "Beta":           return interpret_beta(value)
    if name == "Alpha":          return interpret_alpha(value)
    if name == "Sharpe":         return interpret_sharpe(value)
    if name == "Sortino":        return interpret_sortino(value)
    if name == "Volatility":     return interpret_volatility(value)
    if name == "Max Drawdown":   return interpret_maxdd(value)
    if name == "Tracking Error": return interpret_tracking_error(value)
    if name == "Ann. Return":    return interpret_ann_return(value, ctx.get("bench_ann_return"))
    if name == "P/E":            return interpret_pe(value)
    if name == "D/E":            return interpret_de(value)
    if name == "Div Yield":      return interpret_div_yield(value)
    if name == "Net Profit Margin": return interpret_net_margin(value)
    if name == "Expense Ratio":  return interpret_expense_ratio(value)
    # default
    return f"{name}: {_num(value)}"
