import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from portfolio.metrics import cumulative_returns, drawdown_series
from portfolio.data import get_prices, prices_to_returns, DataConfig

TRADING_DAYS = 252


def plot_equity_curve(returns: pd.Series, title: str = "Equity Curve"):
    equity = cumulative_returns(returns)

    fig, ax = plt.subplots(figsize=(10, 5))
    equity.plot(ax=ax)
    ax.set_title(title)
    ax.set_ylabel("Growth of $1")
    ax.grid(True)

    return fig


"""
if __name__ == "__main__":
    cfg = DataConfig(start="2020-01-01", interval="1d")  
    prices = get_prices("SPY", cfg=cfg)
    print("PRICES:", prices.index.min(), prices.index.max(), len(prices))

    returns = prices_to_returns(prices)
    print("RETURNS:", returns.index.min(), returns.index.max(), len(returns))

    plot_equity_curve(returns, "SPY Returns")
    plt.show()
"""


def plot_drawdowns(returns: pd.Series, title: str = "Drawdowns"):
    dd = drawdown_series(returns)
    fig, ax = plt.subplots(figsize=(10, 5))
    dd.plot(ax=ax, color="red")
    ax.set_title(title)
    ax.set_ylabel("Drawdown")
    ax.grid(True)

    return fig


"""
if __name__ == "__main__":
    cfg = DataConfig(start="2020-01-01", interval="1d")  
    prices = get_prices("SPY", cfg=cfg)
    print("PRICES:", prices.index.min(), prices.index.max(), len(prices))

    returns = prices_to_returns(prices)
    print("RETURNS:", returns.index.min(), returns.index.max(), len(returns))

    plot_drawdowns(returns, "SPY Returns")
    plt.show()
"""


def plot_rolling_volatility(
    # Why rolling? Risk is not static, Volatility clusters, Annualized rolling vol approximates “current regime”
    returns: pd.Series,
    window: int = 63,  # ~3 month of trading days, common industry convention; short enough to react, long enough to stabilize
    title: str = "Rolling Volatility",
):
    rolling_vol = returns.rolling(window).std() * np.sqrt(TRADING_DAYS)
    fig, ax = plt.subplots(figsize=(10, 5))
    rolling_vol.plot(ax=ax, color="orange")
    ax.set_title(title)
    ax.set_ylabel("Annualized Volatility")
    ax.grid(True)

    return fig


"""
if __name__ == "__main__":
    cfg = DataConfig(start="2020-01-01", interval="1d")  
    prices = get_prices("SPY", cfg=cfg)
    print("PRICES:", prices.index.min(), prices.index.max(), len(prices))

    returns = prices_to_returns(prices)
    print("RETURNS:", returns.index.min(), returns.index.max(), len(returns))

    plot_rolling_volatility(returns)
    plt.show()
"""


def plot_rolling_sharpe(
    # Average Sharpe hides regime dependence, Rolling Sharpe shows when strategy worked, Risk QA and Markets teams care about this deeply
    returns: pd.Series,
    window: int = 63,
    risk_free_rate: float = 0.0,  #!!!#connect to real-time data
    title: str = "Rolling Sharpe Ratio",
):
    excess = returns - risk_free_rate / TRADING_DAYS
    rolling_sharpe = (
        excess.rolling(window).mean() / excess.rolling(window).std()
    ) * np.sqrt(TRADING_DAYS)

    fig, ax = plt.subplots(figsize=(10, 5))
    rolling_sharpe.plot(ax=ax)
    ax.set_title(title)
    ax.set_ylabel("Sharpe")
    ax.grid(True)

    return fig


"""
if __name__ == "__main__":
    cfg = DataConfig(start="2020-01-01", interval="1d")  
    prices = get_prices("SPY", cfg=cfg)
    print("PRICES:", prices.index.min(), prices.index.max(), len(prices))

    returns = prices_to_returns(prices)
    print("RETURNS:", returns.index.min(), returns.index.max(), len(returns))

    plot_rolling_sharpe(returns, risk_free_rate=0.04)
    plt.show()
"""
