from __future__ import annotations

import argparse

import matplotlib.pyplot as plt
import pandas as pd

from portfolio.data import DataConfig, get_prices, prices_to_returns
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


def main() -> None:
    args = parse_args()

    tickers = []
    for t in args.tickers.split(","):
        t = t.strip().upper()
        tickers.append(t)

    benchmark_symbol = args.benchmark.strip().upper()

    if not tickers:
        raise ValueError("No tickers provided. Use --tickers TICKER1,TICKER2,...")

    if benchmark_symbol not in tickers:
        tickers.append(benchmark_symbol)

    cfg = DataConfig(start=args.start, end=args.end, cache_days=args.cache_days)

    prices = get_prices(tickers, cfg)
    rets_df = prices_to_returns(prices)
    if benchmark_symbol not in rets_df.columns:
        raise ValueError(
            f"Benchmark '{benchmark_symbol}' not found in downloaded data."
        )

    benchmark_rets = rets_df[benchmark_symbol]

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
                target = args.pyfolio_target.strip().upper()
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
