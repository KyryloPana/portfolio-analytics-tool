from __future__ import annotations
import argparse  # A standard Python library for turning terminal inputs into structured variables

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


def parse_args() -> argparse.Namespace:
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
        "--start",
        type=str,
        default="2022-01-01",
        help="Start date YYYY-MM-DD",
    )
    p.add_argument(
        "--end",
        type=str,
        default=None,
        help="End date YYYY-MM-DD (optional)",
    )
    p.add_argument(
        "--cache-days",
        type=int,
        default=3,
        help="Re-download data if cached file is older than N days",
    )
    p.add_argument(
        "--outdir",
        type=str,
        default="output",
        help="Output directory",
    )
    p.add_argument(
        "--show-plots",
        action="store_true",
        help="Display plots interactively (default: off)",
    )

    return p.parse_args()


def main() -> None:
    args = parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    benchmark_symbol = args.benchmark.strip().upper()

    # Ensure benchmark is included in tickers (useful for plotting/comparison)
    if benchmark_symbol not in tickers:
        tickers.append(benchmark_symbol)

    cfg = DataConfig(start=args.start, end=args.end, cache_days=args.cache_days)

    # 2) Fetch prices -> returns
    prices = get_prices(tickers, cfg)
    rets_df = prices_to_returns(prices)

    benchmark_prices = get_prices([benchmark_symbol], cfg)
    benchmark_rets = prices_to_returns(benchmark_prices)[benchmark_symbol]

    # 3) Core metrics table (save + print)
    core = pd.DataFrame(index=rets_df.columns)
    core["cagr"] = annualized_return(rets_df)
    core["vol"] = annualized_volatility(rets_df)
    core["sharpe"] = sharpe_ratio(rets_df)
    core["max_dd"] = max_drawdown(rets_df)

    print("Core metrics:\n", core.round(4))

    # 4) Benchmark-relative metrics (save + print)
    rel = benchmark_summary(rets_df, benchmark_rets)
    print("\nBenchmark-relative stats:\n", rel.round(4))

    # 5) Output dirs + run tag
    dirs = ensure_output_dirs(args.outdir)
    tag = timestamp_tag()

    save_table(core.round(6), dirs["tables"] / f"core_metrics_{tag}.csv")
    save_table(rel.round(6), dirs["tables"] / f"benchmark_summary_{tag}.csv")

    # 6) Save plots
    for col in rets_df.columns:
        fig1 = plot_equity_curve(rets_df[col], title=f"{col} Equity Curve")
        save_figure(fig1, dirs["figures"] / f"{col}_equity_{tag}.png")
        plt.close(fig1)

        fig2 = plot_drawdowns(rets_df[col], title=f"{col} Drawdowns")
        save_figure(fig2, dirs["figures"] / f"{col}_drawdowns_{tag}.png")
        plt.close(fig2)

        fig3 = plot_rolling_volatility(rets_df[col], title=f"{col} Rolling Volatility")
        save_figure(fig3, dirs["figures"] / f"{col}_rolling_vol_{tag}.png")
        plt.close(fig3)

        fig4 = plot_rolling_sharpe(rets_df[col], title=f"{col} Rolling Sharpe")
        save_figure(fig4, dirs["figures"] / f"{col}_rolling_sharpe_{tag}.png")
        plt.close(fig4)

    # 7) Write text report
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

    # Optional: show plots interactively (off by default for a tool)
    if args.show_plots:
        plt.show()


if __name__ == "__main__":
    main()
