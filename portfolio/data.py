from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

CACHE_DIR = Path("portfolio/cache")


@dataclass
class DataConfig:
    """
    Configuration for market data retrieval
    Attributes:
        start: Start date (YYYY-MM-DD) or None for maximum available history
        end: End date (YYYY-MM-DD) or None
        interval: Sampling frequency supported by yfinance (eg "1d")
        cache_data: If True cache downloaded prices to disk and reuse if fresh
        cache_days: Max age (in days) for cached files before re-download
    """

    start: str | None = None
    end: str | None = None
    interval: str = "1d"
    cache_data: bool = True
    cache_days: int = 3


def _is_cache_fresh(path: Path, cache_days: int) -> bool:
    """Return True if cache file exists and is newer than 'cache_days'"""
    if not path.exists():
        return False
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return (datetime.now() - mtime) < timedelta(days=cache_days)


def get_prices(tickers: list[str], cfg: DataConfig) -> pd.DataFrame:
    """
    Download (or load from cache) adjusted close prices for 'tickers'

    Returns:
        DataFrame indexed by date, with one column per ticker

    Notes:
        Uses yfinance with auto_adjust=True (splits/dividends adjusted)
        Normalizes yfinance output so caller always receives a DataFrame
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    key = f"{'_'.join(tickers)}_{cfg.start}_{cfg.end}_{cfg.interval}".replace(":", "-")
    cache_path = CACHE_DIR / f"{key}.csv"

    if cfg.cache_data and _is_cache_fresh(cache_path, cfg.cache_days):
        return pd.read_csv(cache_path, index_col=0, parse_dates=True)

    data = yf.download(
        tickers=tickers,
        start=cfg.start,
        end=cfg.end,
        interval=cfg.interval,
        auto_adjust=True,
        progress=False,
    )

    # yfinance returns MultiIndex columns when requesting multiple tickers
    if isinstance(data.columns, pd.MultiIndex):
        prices = data["Close"].copy()
    else:
        prices = data[["Close"]].copy()
        prices.columns = tickers

    prices = prices.dropna(how="all").sort_index()

    if cfg.cache_data:
        prices.to_csv(cache_path)

    return prices


def prices_to_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Convert price series to simple arithmetic returns (pct_change)
    """
    return prices.pct_change().dropna()

def portfolio_return(prices: pd.DataFrame, weights: pd.Series | dict, V0: float = 1.0, start_date = None) -> pd.DataFrame:
    if isinstance(weights, dict):
        weights = pd.Series(weights)
    P0 = prices.iloc[0]
    shares = weights * V0 / P0
    portfolio_value = prices.mul(shares, axis=1).sum(axis=1)
    portfolio_return = portfolio_value.pct_change().drop(index=portfolio_value.index[0])
    
    return portfolio_return