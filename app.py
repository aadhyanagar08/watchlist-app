from typing import Tuple, Dict
import numpy as np
import pandas as pd

TRADING_DAYS = 252

def daily_returns(prices: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    return prices.pct_change().dropna()

def max_drawdown(prices: pd.Series) -> float:
    cum = (1 + prices.pct_change().fillna(0)).cumprod()
    peak = cum.cummax()
    dd = cum / peak - 1.0
    return float(dd.min()) if len(dd) else np.nan

def annualized_vol(returns: pd.Series) -> float:
    return float(returns.std(ddof=0) * np.sqrt(TRADING_DAYS)) if len(returns) else np.nan

def annualized_return(returns: pd.Series) -> float:
    return float(returns.mean() * TRADING_DAYS) if len(returns) else np.nan

def sharpe_ratio(returns: pd.Series, rf_annual: float = 0.0) -> float:
    if not len(returns):
        return np.nan
    rf_daily = rf_annual / TRADING_DAYS
    ex = returns - rf_daily
    denom = ex.std(ddof=0) * np.sqrt(TRADING_DAYS)
    return float(ex.mean() * TRADING_DAYS / denom) if denom and not np.isnan(denom) else np.nan

def sortino_ratio(returns: pd.Series, rf_annual: float = 0.0) -> float:
    if not len(returns):
        return np.nan
    rf_daily = rf_annual / TRADING_DAYS
    ex = returns - rf_daily
    downside = ex[ex < 0]
    dd = downside.std(ddof=0) * np.sqrt(TRADING_DAYS) if len(downside) else np.nan
    num = ex.mean() * TRADING_DAYS
    return float(num / dd) if dd and not np.isnan(dd) else np.nan

def tracking_error(returns: pd.Series, bench: pd.Series) -> float:
    aligned = pd.concat([returns, bench], axis=1).dropna()
    if aligned.empty:
        return np.nan
    active = aligned.iloc[:,0] - aligned.iloc[:,1]
    return float(active.std(ddof=0) * np.sqrt(TRADING_DAYS))

def beta_alpha_r2(returns: pd.Series, bench: pd.Series, rf_annual: float = 0.0) -> Tuple[float, float, float]:
    aligned = pd.concat([returns, bench], axis=1).dropna()
    if aligned.empty:
        return (np.nan, np.nan, np.nan)
    rf_daily = rf_annual / TRADING_DAYS
    y = aligned.iloc[:,0] - rf_daily
    x = aligned.iloc[:,1] - rf_daily
    if len(x) < 2:
        return (np.nan, np.nan, np.nan)
    cov = np.cov(x, y, ddof=0)[0,1]
    var = np.var(x, ddof=0)
    beta = cov / var if var else np.nan
    # intercept (alpha per day), via means
    alpha_daily = y.mean() - beta * x.mean() if beta is not np.nan else np.nan
    # annualize alpha
    alpha_annual = float(alpha_daily * TRADING_DAYS) if alpha_daily is not np.nan else np.nan
    # R^2 via correlation^2
    r = np.corrcoef(x, y)[0,1] if len(x) > 1 else np.nan
    r2 = float(r**2) if not np.isnan(r) else np.nan
    return (float(beta), alpha_annual, r2)

def compute_all_metrics(prices: pd.DataFrame, benchmark: str, rf_annual: float = 0.0) -> pd.DataFrame:
    if prices.empty:
        return pd.DataFrame()
    rets = prices.pct_change().dropna()
    cols = []
    rows = []
    for col in prices.columns:
        if col == benchmark:
            continue
        r = rets[col]
        rb = rets[benchmark] if benchmark in rets.columns else pd.Series(dtype=float)
        beta, alpha, r2 = beta_alpha_r2(r, rb, rf_annual=rf_annual) if not rb.empty else (np.nan, np.nan, np.nan)
        rows.append({
            "Ticker": col,
            "Sharpe": sharpe_ratio(r, rf_annual),
            "Sortino": sortino_ratio(r, rf_annual),
            "Volatility": annualized_vol(r),
            "Max Drawdown": max_drawdown(prices[col]),
            "Tracking Error": tracking_error(r, rb) if not rb.empty else np.nan,
            "Alpha": alpha,
            "Beta": beta,
            "R²": r2,
            "Ann. Return": annualized_return(r),
        })
    df = pd.DataFrame(rows).set_index("Ticker")
    # nicer order
    order = ["Ann. Return","Sharpe","Sortino","Volatility","Max Drawdown","Tracking Error","Alpha","Beta","R²"]
    return df[order]
