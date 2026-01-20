import numpy as np  # use NumPy for mathematical operations
import pandas as pd  # use pandas because your data is a pd.Series (time series of returns).

TRADING_DAYS = 252  # assumed number of trading days


def cumulative_returns(
    returns: pd.Series,
) -> (
    pd.Series
):  # a time series showing how $1 grows over time if you keep compounding returns.
    return (1 + returns).cumprod()
    # “Cumulative product” multiplies growth factors over time


def annualized_return(returns: pd.Series, periods=TRADING_DAYS) -> float:
    # Convert the total compounded growth over the whole sample into a compounded annual growth rate (CAGR)
    total_return = (1 + returns).prod()  # final value of the equity curve
    years = len(returns) / periods
    return total_return ** (1 / years) - 1


def annualized_volatility(returns: pd.Series, periods=TRADING_DAYS) -> float:
    # Convert daily volatility into annual volatility
    return returns.std() * np.sqrt(periods)
    # returns.std() is the standard deviation of returns per period (daily)
    """Example:
    daily std = 1% = 0.01
    annual vol = 0.01 * sqrt(252) ≈ 0.158 → 15.8%  """


def sharpe_ratio(
    returns: pd.Series, risk_free_rate: float = 0.0, periods=TRADING_DAYS
) -> float:
    excess = (
        returns - risk_free_rate / periods
    )  # Excess returns (this subtracts the per-period risk-free rate from each return)
    return (excess.mean() / excess.std()) * np.sqrt(periods)


#!!!#If excess.std() is zero or extremely small, Sharpe can blow up or become infinite. In production you should handle that (later)


def drawdown_series(
    returns: pd.Series,
) -> pd.Series:  # Compute drawdown at every point in time
    # Drawdown = how far you are below the previous highest point (“peak”)
    cum = cumulative_returns(returns)
    peak = cum.cummax()
    return (cum - peak) / peak


def max_drawdown(returns: pd.Series) -> float:
    return drawdown_series(returns).min()
    """Example:
    peak = 1.20, current cum = 1.08
    drawdown = (1.08 - 1.20) / 1.20 = -0.10 → -10% """


# Add benchmark functions


def _to_dataframe(x: pd.Series | pd.DataFrame) -> pd.DataFrame:
    if isinstance(x, pd.Series):
        return x.to_frame(name=x.name or "Strategy")
    return x


def align_returns(
    strategy: pd.Series | pd.DataFrame,
    benchmark: pd.Series,
) -> tuple[pd.DataFrame, pd.Series]:
    # “Give me strategy returns (one or many) + benchmark returns; I will return both aligned on the exact same dates, with no missing values.”
    s = _to_dataframe(strategy).copy()
    b = benchmark.copy()

    # align on common dates; drop any missing points
    joined = s.join(b.rename("benchmark"), how="inner").dropna()
    b_aligned = joined["benchmark"]
    s_aligned = joined.drop(columns=["benchmark"])
    #!!!# .dropna() drops rows if any strategy column is missing. If you have multiple strategy columns and one of them has NaNs, you might lose a lot of data.
    return s_aligned, b_aligned


def beta(strategy: pd.Series | pd.DataFrame, benchmark: pd.Series) -> pd.Series:
    s, b = align_returns(strategy, benchmark)
    b_var = b.var()
    if b_var == 0:
        return pd.Series(
            index=s.columns, data=np.nan
        )  #!!!# also treat “almost zero” variance, or NaN variance:
    betas = {}
    for col in s.columns:
        cov = s[col].cov(b)
        betas[col] = cov / b_var
    return pd.Series(betas, name="beta")


def alpha_annualized(
    # This function computes CAPM-style alpha, annualized, for: one strategy (pd.Series) or multiple strategies (pd.DataFrame) against one benchmark (pd.Series).
    strategy: pd.Series | pd.DataFrame,
    benchmark: pd.Series,
    periods: int = TRADING_DAYS,
) -> pd.Series:
    # After accounting for market exposure (beta), how much extra return did the strategy produce?
    # Alpha is the average return you get after removing what the market already explains.
    """
    CAPM-style alpha using realized returns:
    alpha_daily = mean(strategy - beta * benchmark)
    alpha_annual = alpha_daily * periods
    """
    s, b = align_returns(strategy, benchmark)
    betas = beta(s, b)
    alphas = {}
    for col in s.columns:
        alpha_daily = (s[col] - betas[col] * b).mean()
        alphas[col] = alpha_daily * periods
    return pd.Series(alphas, name="alpha_annual")
    #!!!# No risk-free rate; This is excess-return CAPM without Rf.


def tracking_error_annualized(
    strategy: pd.Series | pd.DataFrame,
    benchmark: pd.Series,
    periods: int = TRADING_DAYS,
) -> pd.Series:
    # “How much does my strategy deviate from the benchmark?”; Not volatility of the strategy itself — volatility of the difference between strategy and benchmark.
    s, b = align_returns(strategy, benchmark)
    te = {}
    for col in s.columns:
        active = s[col] - b
        te[col] = active.std() * np.sqrt(periods)
    return pd.Series(te, name="tracking_error")


# measures how tightly the strategy tracks the benchmark.


def information_ratio(
    strategy: pd.Series | pd.DataFrame,
    benchmark: pd.Series,
    periods: int = TRADING_DAYS,
) -> pd.Series:
    # Information Ratio (IR) answers: “How much consistent outperformance do I get per unit of active risk?”
    # It’s Sharpe ratio, but relative to a benchmark instead of cash.
    s, b = align_returns(strategy, benchmark)
    ir = {}
    for col in s.columns:
        active = s[col] - b
        active_mean_annual = active.mean() * periods  # average outperformance per year
        te = active.std() * np.sqrt(periods)
        ir[col] = (active_mean_annual / te) if te != 0 else np.nan
        # numerator: “how much I beat the benchmark”; denominator: “how much I deviated from it”
    return pd.Series(ir, name="information_ratio")


def correlation(
    strategy: pd.Series | pd.DataFrame,
    benchmark: pd.Series,
) -> pd.Series:
    s, b = align_returns(strategy, benchmark)
    cors = {col: s[col].corr(b) for col in s.columns}
    # For each col in the strategy DataFrame: compute s[col].corr(b)
    # pandas.Series.corr(...) computes Pearson correlation by default (linear correlation).
    return pd.Series(cors, name="correlation")


def benchmark_summary(
    strategy: pd.Series | pd.DataFrame,
    benchmark: pd.Series,
) -> pd.DataFrame:
    """
    Collect benchmark-relative stats into a single table.
    """
    s, b = align_returns(strategy, benchmark)
    out = pd.DataFrame(index=s.columns)
    out["beta"] = beta(s, b)
    out["alphas_annual"] = alpha_annualized(s, b)
    out["tracking_error"] = tracking_error_annualized(s, b)
    out["information_ratio"] = information_ratio(s, b)
    out["correlation"] = correlation(s, b)
    return out
