from __future__ import annotations

import argparse

import matplotlib.pyplot as plt
import pandas as pd

from portfolio.data import DataConfig, get_prices, prices_to_returns, portfolio_return
from portfolio.metrics import (
    annualized_return,
    annualized_volatility,
    sharpe_ratio,
    max_drawdown,
    benchmark_summary,
)
from portfolio.plots import (
    plot_equity_curve,
    plot_drawdowns,
    plot_rolling_volatility,
    plot_rolling_sharpe,
)
from portfolio.report import (
    ensure_output_dirs,
    timestamp_tag,
    save_figure,
    save_table,
    write_text_report,
)

from portfolio.pyfolio_report import pyfolio_generate


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    p = argparse.ArgumentParser(
        description="Portfolio Analytics Tool: metrics, plots, benchmark comparison, and exports."
    )
    p.add_argument(
        "--portfolio-tickers",
        type=str,
        required=True,
        help="Comma-separated portfolio constituents used to construct the PORTFOLIO series "
            "(e.g., 'AAPL,MSFT,SPY').",
    )

    p.add_argument(
        "--portfolio-weights",
        type=str,
        default=None,
        help="Comma-separated ticker=weight pairs for the portfolio constituents "
            "(e.g., 'AAPL=0.5,MSFT=0.3,SPY=0.2'). "
            "If omitted, uses equal weights across --portfolio-tickers. "
            "Weights are normalized to sum to 1.",
    )

    p.add_argument(
        "--V0",
        type=float,
        default=1.0,
        help="Initial portfolio value (scale factor). Default: 1.0.",
    )


    p.add_argument(
        "--tickers",
        type=str,
        default="AAPL,SPY",
        help="Comma-separated tickers to analyze (e.g., 'AAPL,MSFT,SPY')",
    )
    p.add_argument(
        "--benchmark",
        type=str,
        default="SPY",
        help="Benchmark ticker symbol (e.g., 'SPY')",
    )
    p.add_argument(
        "--start", type=str, default="2022-01-01", help="Start date YYYY-MM-DD"
    )
    p.add_argument(
        "--end", type=str, default=None, help="End date YYYY-MM-DD (optional)"
    )
    p.add_argument(
        "--cache-days",
        type=int,
        default=3,
        help="Re-download data if cached file is older than N days",
    )
    p.add_argument("--outdir", type=str, default="output", help="Output directory")
    p.add_argument(
        "--show-plots",
        action="store_true",
        help="Display plots interactively (default: off)",
    )

    p.add_argument(
        "--pyfolio", action="store_true", help="Generate PyFolio report (optional)"
    )
    p.add_argument(
        "--pyfolio-target",
        type=str,
        default=None,
        help="Ticker/column to run PyFolio on (default: first non-benchmark ticker)",
    )

    p.add_argument(
        "--pyfolio-out",
        type=str,
        default=None,
        help="Path to save PyFolio HTML report (optional)",
    )
    p.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Custom run tag used in output filenames (default: timestamp)",
    )

    return p.parse_args()


def parse__portfolio(portfolio_tickers: str, portfolio_weights: str | None):
    args = parse_args()
    
    portfolio_tickers = []
    for pt in args.portfolio_tickers.split(","):
        pt = pt.strip().upper()
        portfolio_tickers.append(pt)
    
    # check for duplicates
    if len(set(portfolio_tickers)) != len(portfolio_tickers):
        raise ValueError(f"Duplicate tickers in --portfolio-tickers: {portfolio_tickers}")

    #make a dictionary with ticker and its weight
    weights_by_ticker: dict[str, float] = {}
    portfolio_weights = args.portfolio_weights
    if portfolio_weights:
        for item in portfolio_weights.split(","):
            item = item.strip()
            if not item:
                continue
            k, v = item.split("=", 1)
            k = k.strip().upper()
            w = float(v.strip())
            weights_by_ticker[k] = w
        #validate tickers set and tickers for which weights are given 
        unknown = set(weights_by_ticker) - set(portfolio_tickers)
        if unknown:
            raise ValueError(f"Weights given for unknown tickers: {sorted(unknown)}")
        
        missing = set(portfolio_tickers) - set(weights_by_ticker)
        if missing:
            raise ValueError(f"Missing weights for tickers: {sorted(missing)}")
        
        total = sum(weights_by_ticker[t] for t in portfolio_tickers)
        if abs(total - 1.0) > 1e-5:
            raise ValueError(f"Weights must sum to 1.0 (got {total})")
        
    else:
        # equal weights
        w = 1.0 / len(portfolio_tickers)
        weights_by_ticker = {t: w for t in portfolio_tickers}

    return portfolio_tickers, weights_by_ticker



def main() -> None:
    args = parse_args()
    cfg = DataConfig(start=args.start, end=args.end, cache_days=args.cache_days)
    
    
    portfolio_tickers, weights_by_ticker = parse__portfolio(args.portfolio_tickers, args.portfolio_weights)
        
    tickers = []
    for t in args.tickers.split(","):
        t = t.strip().upper()
        tickers.append(t)

    benchmark_symbol = args.benchmark.strip().upper()

    if not tickers:
        raise ValueError("No tickers provided. Use --tickers TICKER1,TICKER2,...")

    if benchmark_symbol not in tickers:
        tickers.append(benchmark_symbol)

    

    prices = get_prices(tickers, cfg)
    rets_df = prices_to_returns(prices)
    if benchmark_symbol not in rets_df.columns:
        raise ValueError(
            f"Benchmark '{benchmark_symbol}' not found in downloaded data."
        )

    benchmark_rets = rets_df[benchmark_symbol]

    portfolio_prices = get_prices(portfolio_tickers, cfg)
    portfolio_returns = portfolio_return(portfolio_prices, weights_by_ticker, args.V0)
    #rets_df = rets_df.join(portfolio_returns.rename("Portfolio"))
    rets_df.insert(0, "Portfolio", portfolio_returns)

    
    core = pd.DataFrame(index=rets_df.columns)
    core["cagr"] = annualized_return(rets_df)
    core["vol"] = annualized_volatility(rets_df)
    core["sharpe"] = sharpe_ratio(rets_df)
    core["max_dd"] = max_drawdown(rets_df)

    rel = benchmark_summary(rets_df, benchmark_rets)

    print("Core metrics:\n", core.round(4))
    print("\nBenchmark-relative stats:\n", rel.round(4))

    dirs = ensure_output_dirs(args.outdir)
    tag = timestamp_tag()

    save_table(core.round(6), dirs["tables"] / f"core_metrics_{tag}.csv")
    save_table(rel.round(6), dirs["tables"] / f"benchmark_summary_{tag}.csv")

    for col in rets_df.columns:
        fig = plot_equity_curve(rets_df[col], title=f"{col} Equity Curve")
        save_figure(fig, dirs["figures"] / f"{col}_equity_{tag}.png")
        plt.close(fig)

        fig = plot_drawdowns(rets_df[col], title=f"{col} Drawdowns")
        save_figure(fig, dirs["figures"] / f"{col}_drawdowns_{tag}.png")
        plt.close(fig)

        fig = plot_rolling_volatility(rets_df[col], title=f"{col} Rolling Volatility")
        save_figure(fig, dirs["figures"] / f"{col}_rolling_vol_{tag}.png")
        plt.close(fig)

        fig = plot_rolling_sharpe(rets_df[col], title=f"{col} Rolling Sharpe")
        save_figure(fig, dirs["figures"] / f"{col}_rolling_sharpe_{tag}.png")
        plt.close(fig)

    start = rets_df.index.min().date()
    end = rets_df.index.max().date()

    lines = [
        f"PORTFOLIO ANALYTICS REPORT  |  run={tag}",
        f"Date range: {start} -> {end}",
        f"Assets: {', '.join(rets_df.columns)}",
        "",
        "Core metrics:",
        core.round(4).to_string(),
        "",
        f"Benchmark-relative metrics (benchmark={benchmark_symbol}):",
        rel.round(4).to_string(),
    ]
    write_text_report(lines, dirs["base"] / f"report_{tag}.txt")

    if args.show_plots:
        plt.show()

    if args.pyfolio:
        candidates = []
        """
            the tool supports multi-ticker analysis (Data Frame of returns); 
            PyFolio can generate a report only for one return series at a time (a pandas Series)
            So here it is chosen a column from rets_df to be “the strategy” that PyFolio will analyze
        """
        for c in rets_df.columns:
            if c != benchmark_symbol:
                candidates.append(c)

        if len(candidates) > 0:
            if args.pyfolio_target is not None:
                target = args.pyfolio_target.strip()
                if not 'Portfolio': target.upper()
                
            elif args.portfolio_tickers is not None:
                target = 'Portfolio'
            else:
                # chooses first non-benchmark ticker from the order user typed
                target = tickers[0]
        else:
            target = benchmark_symbol

        pyfolio_html = args.pyfolio_out
        if pyfolio_html is None:
            pyfolio_html = str(dirs["base"] / f"pyfolio_{target}_{tag}.html")

        out_path = pyfolio_generate(
            returns=rets_df[target],
            benchmark_rets=benchmark_rets,
            output_html=pyfolio_html,
            title=f"PyFolio Tear Sheet — {target}",
            tag=tag,
            target=target,
        )
        print(f"PyFolio report saved: {out_path}")


if __name__ == "__main__":
    main()
