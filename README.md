# Portfolio Analytics Tool — v0.1.1

A Python-based command-line tool for analyzing portfolio and strategy performance using historical market data.  
It computes core risk/return metrics, benchmark-relative statistics, rolling diagnostics, and exports reproducible reports.

This project is designed as a foundational analytics engine for quantitative research, risk analysis, and systematic strategy evaluation.

---

## 1. Key Features (v0.1.1)

- **Deterministic market data ingestion**
  - Downloads historical prices from Yahoo Finance
  - Uses local caching to avoid unnecessary re-downloads

- **Portfolio and asset-level return construction**
  - Converts adjusted close prices into daily returns
  - Supports multiple tickers simultaneously

- **Core performance metrics**
  - CAGR (compound annual growth rate)
  - Annualized volatility
  - Sharpe ratio
  - Maximum drawdown

- **Benchmark-relative analytics**
  - Beta
  - Annualized alpha
  - Tracking error
  - Information ratio
  - Correlation

- **Rolling diagnostics**
  - Rolling volatility
  - Rolling Sharpe ratio

- **Automated exports**
  - Figures (PNG)
  - Tables (CSV)
  - Text-based summary reports

- **Optional PyFolio tear sheet export (v0.1.1)**
  - Generates a PyFolio tear sheet for one selected return series
  - Captures PyFolio Matplotlib figures and embeds them into an HTML report
  - Output includes an HTML file + a companion folder with PNG figures

- **CLI interface**
  - Flexible configuration for tickers, benchmark, dates, cache settings, and output paths
  - Optional PyFolio flags (`--pyfolio`, `--pyfolio-out`)

---

## 2. Project Structure
```bash
portfolio-analytics-tool/
├── portfolio/
│ ├── __init__.py
│ ├── data.py                # Market data ingestion & caching
│ ├── metrics.py             # Performance & risk analytics
│ ├── plots.py               # Visualization utilities
│ ├── report.py              # Export & reporting utilities
│ └── pyfolio_report.py      # OPTIONAL: PyFolio tear sheet export
├── data/
│ ├── sample_strategy.csv
│ └── sample_benchmark.csv
├── analyze.py               # CLI entry point / orchestration layer
├── README.md
├── CHANGELOG.md
├── requirements.txt
└── .gitignore
```

**Design principles**

- Clear separation of concerns 
- Each module has a single responsibility  
- No hidden side effects  
- Deterministic outputs given identical inputs  

---

## 3. Installation

### Prerequisites

- Python 3.10 or newer
- `pip` package manager
- Internet connection (for initial data download)

### Steps

1. Clone the repository:

```bash
git clone https://github.com/your-username/portfolio-analytics-tool.git
cd portfolio-analytics-tool
```
2. (Optional but recommended) Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. (Optional) Install PyFolio add-on (v0.1.1):
```bash
pip install pyfolio-reloaded
```
---

## 4. Quick Start

Run a basic analysis on AAPL vs SPY using default settings:
```bash
python analyze.py
```
Default configuration
Tickers: AAPL,SPY
Benchmark: SPY
Start date: 2022-01-01
End date: latest available
Cache validity: 3 days
Output directory: output/

---

## 5. CLI Usage
**Example**
```bash
python analyze.py \
  --tickers 'AAPL,MSFT,SPY' \
  --benchmark 'SPY' \
  --start '2018-01-01' \
  --cache-days 5 \
  --outdir 'output' \
  --show-plots
```

**PyFolio tear sheet (v0.1.1)**
```bash
python analyze.py \
  --tickers 'MSTR,NVDA,AAPL' \
  --benchmark 'SPY' \
  --start '2018-01-01' \
  --pyfolio \
  --pyfolio-target 'NVDA' \
  --pyfolio-out 'output/pyfolio.html'



**Available Arguments**
| Argument           | Description                                    |
|--------------------|------------------------------------------------|
| `--tickers`        | Comma-separated list of tickers to analyze     |
| `--benchmark`      | Benchmark ticker symbol                        |
| `--start`          | Start date (YYYY-MM-DD)                        |
| `--end`            | End date (optional)                            |
| `--cache-days`     | Re-download data if cache is older than N days |
| `--outdir`         | Output directory                               |
| `--show-plots`     | Display plots interactively                    |
| `--pyfolio`        | Generate PyFolio tear sheet (optional add-on)  |
| `--pyfolio-target` | Asset that is going to be analized by PyFolio  |
| `--pyfolio-out`    | Output path for PyFolio HTML (file or folder)  |
| `--tag`            | Custom tag for export file                     |

```bash
analyze.py [-h]  [--tickers TICKERS]  [--benchmark BENCHMARK]  [--start START]  [--end END]  [--cache-days CACHE_DAYS]  [--outdir OUTDIR]  [--show-plots]  [--pyfolio]  [--pyfolio-target PYFOLIO_TARGET]  [--pyfolio-out PYFOLIO_OUT] [--tag TAG]
```
---

## 6. Outputs
Each run generates a timestamped set of outputs.

### Figures (`output/figures/`)
- Equity curve  
- Drawdowns  
- Rolling volatility  
- Rolling Sharpe ratio  

### Tables (`output/tables/`)
- Core performance metrics  
- Benchmark-relative statistics  

### Text Report (`output/`)
A concise, human-readable summary including:
- Date range  
- Assets analyzed  
- Core metrics  
- Benchmark-relative metrics  

### PyFolio Report (optional, v0.1.1)
If --pyfolio is enabled:
- An HTML tear sheet (path defined by --pyfolio-out)
- A companion folder of PNGs next to the HTML (captured PyFolio figures)

All outputs are deterministic and reproducible given the same inputs.

## 7. Methodology Notes

- Prices are sourced from Yahoo Finance and adjusted for splits/dividends.  
- Returns are computed as simple percentage returns.  
- Annualization assumes 252 trading days per year.  
- Alpha and beta use a realized CAPM-style formulation.  
- Information ratio is undefined when tracking error is zero (e.g., benchmark compared with itself).  
- Rolling metrics use a default 63-day (~3-month) window.

### PyFolio notes (v0.1.1)
- PyFolio generates a tear sheet for a single returns series (pd.Series).
- When multi-ticker returns are provided, the tool selects one target series for PyFolio.
- PyFolio is treated as an optional reporting utility; the core analytics pipeline remains independent.

This tool prioritizes clarity, correctness, and reproducibility over predictive claims.

---

## 8. Roadmap

### v0.2.0 — Portfolio & Strategy Abstraction
- Explicit portfolio weights  
- Multi-strategy comparison  
- Support for user-provided return series
- Strategy-level PyFolio integration

### v0.3.0 — Risk Scaling & Regime Awareness
- Regime-conditioned analytics
- Regime segmentation
- Volatility targeting and risk scaling  
- Expanded internal metrics (progressive removal of external dependencies such as PyFolio)  
- Expanded benchmark universe 

### v0.4.0 — Factor & Attribution Analysis
- Factor regression framework
- Performance attribution
- Rolling factor exposure analysis
- Attribution tables and charts

> **Note:** PyFolio support is transitional and will be fully deprecated in future releases in favor of native, transparent analytics
---

## Disclaimer

This project is for research and educational purposes only.  
It does not constitute financial advice.

---

## Why This Project Exists

Most beginner finance projects stop at plotting prices.

This project focuses on how performance is evaluated in professional settings:  
risk-adjusted returns, benchmark context, drawdowns, and regime sensitivity.

It is intentionally built as a clean, extensible analytics core suitable as a base  
for more advanced quantitative research.
