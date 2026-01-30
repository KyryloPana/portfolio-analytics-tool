# Changelog

## v0.1.1
- Added **optional PyFolio integration** via `pyfolio-reloaded`
  - Generates a PyFolio tear sheet for a selected return series
  - Exports a standalone HTML report with embedded performance tables
  - Captures PyFolio Matplotlib figures and saves them as PNG files alongside the HTML
- Introduced CLI flags for PyFolio reporting:
  - `--pyfolio` to enable tear sheet generation
  - `--pyfolio-out` to control output file or directory
- Ensured PyFolio remains a **non-core, optional add-on**
  - Core analytics pipeline is unaffected if PyFolio is not installed
- Improved output handling and robustness for report generation paths
- Internal cleanup and refactoring to support future extensibility (v0.2.0)

## v0.1.0
- Deterministic market data ingestion with caching (yfinance)
- Portfolio return construction and core risk/return metrics (CAGR, vol, Sharpe, max drawdown)
- Benchmark-relative analytics (beta, alpha, tracking error, information ratio, correlation)
- Rolling diagnostics (rolling volatility and rolling Sharpe)
- Export of figures, tables, and text reports
- CLI interface for tickers, benchmark, date range, cache-days, and output directory
