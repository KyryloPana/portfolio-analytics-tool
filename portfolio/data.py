# portfolio/data.py is “data plumbing” module
# it does the next things: 1.Download market prices (from yfinance),
#                         2.Store them locally so you don’t re-download every time
#                         3.Return a clean price DataFrame (dates aligned, consistent columns)
#                         4.Convert prices into returns (because performance analytics uses returns)


from __future__ import annotations  # enables postponed evaluation of type annotations

import os  # Standard library module for interacting with the operating system (env vars, paths, etc.)
from dataclasses import (
    dataclass,
)  # dataclass is a Python feature that creates “data containers” with less boilerplate
from typing import Optional
from datetime import (
    datetime,
    timedelta,
)  # datetime represents a timestamp (date + time); timedelta represents a duration (e.g., “3 days”)

# Used in _is_cache_fresh(): Convert file modification time to a datetime; Compare “now minus mtime” to timedelta(days=cache_days)
from pathlib import (
    Path,
)  # Path is a modern, safer way to handle file paths than raw strings

import pandas as pd
import yfinance as yf

CACHE_DIR = Path("portfolio/cache")


@dataclass
class DataConfig:
    start: str | None = (
        None  # start is either: a string ("2022-01-01") or None ("no constraint"); If None, yfinance downloads “as much as available”
    )
    end: Optional[str] = None  # same logic
    interval: str = "1d"  # This defines the sampling frequency
    cache_data: bool = True  # enable/disable caching
    cache_days: int = 3  # If cached data is older than 3 days, re-download it


# Think of DataConfig as: “The contract between the user and the data engine”
#       The engine promises: “If you give me a config shaped like this, I will behave exactly as specified”


def _is_cache_fresh(
    path: Path, cache_days: int
) -> bool:  ##“Is the cached file recent enough that we can safely reuse it?”
    # _is_cache_fresh: Leading underscore = internal helper, not part of public API.
    # path:Path : the location of the cached CSV file
    # cache_days:int : how old the file is allowed to be before we consider it stale
    # -> bool : returns True or False, nothing else
    if not path.exists():
        return False  # No file → nothing cached; Therefore → not fresh
    mtime = datetime.fromtimestamp(
        path.stat().st_mtime
    )  # The exact time this cache file was last modified
    # path.stat() -> gets file metadata from the OS
    # .st_mtime -> "modification time"
    # datetime.fromtimestamp(...) → convert timestamp → datetime
    return (datetime.now() - mtime) < timedelta(days=cache_days)
    # compares how old the file is with allowed max age and returns True or False


def get_prices(
    tickers: list[str], cfg: DataConfig
) -> (
    pd.DataFrame
):  ##a pd.DataFrame of adjusted close prices, indexed by date, with one column per ticker.
    # tickers: list[str] → like ["SPY", "AAPL"]
    # cfg: DataConfig -> your config object (start/end/interval/cache_days)
    # returns a DataFrame
    CACHE_DIR.mkdir(parents=True, exist_ok=True)  # ensure cache directory exists
    # parents=True -> create parent folders if missing; exist_ok=True -> don't error if it's missing
    key = f"{'_'.join(tickers)}_{cfg.start}_{cfg.end}_{cfg.interval}".replace(":", "-")
    cache_path = CACHE_DIR / f"{key}.csv"
    # It creates a filename that encodes the request: which tickers, what start date, what end date, what interval (So different inputs generate different cache files)

    if _is_cache_fresh(
        cache_path, cfg.cache_days
    ):  # function is designed to avoid doing work unless necessary.
        prices = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        return prices
    # This is the “fast path”: Read cached CSV,
    # index_col=0 means: first column in CSV is treated as index (dates),
    # parse_dates=True converts that index column into real datetime objects

    data = yf.download(
        tickers=tickers,
        start=cfg.start,
        end=cfg.end,
        interval=cfg.interval,
        auto_adjust=True,  # yfinance adjusts the OHLC prices for splits/dividends.
        progress=False,
    )

    # yfinance behaves differently depending on how many tickers you request; it returns multi-index columns when multiple tickers are used
    if isinstance(
        data.columns, pd.MultiIndex
    ):  # If True → multiple tickers; If False → single ticker
        prices = data[
            "Close"
        ].copy()  # data["Close"] selects only the Close level from the first level of the MultiIndex
        # Pandas automatically collapses the remaining level (tickers) into columns
    else:  # if single ticker; with prices = data["Close"] You would get a Series, not a DataFrame.
        prices = data[["Close"]].copy()  # forces a 2D DataFrame, even for one ticker.
        prices.columns = tickers  # normalize naming for single ticker
    # ==> “No matter how messy or inconsistent the data source is, the internal representation is always the same”

    prices = prices.dropna(how="all")  # removes rows where all tickers are NaN
    prices.to_csv(cache_path)  # writes cache for next time
    return prices  # returns the prices DataFrame

    #!!!#FIX WHAT CAN GO WRONG LATER


def prices_to_returns(prices: pd.DataFrame) -> pd.DataFrame:
    # Convert price series to simple daily returns
    return prices.pct_change().dropna()
