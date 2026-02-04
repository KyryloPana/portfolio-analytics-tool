import pandas as pd
from portfolio.data import DataConfig, get_prices, prices_to_returns, portfolio_return
# example
df = pd.DataFrame(
    {
        "AAPL": [100, 101, 102],
        "MSFT": [200, 198, 202],
        "GOOG": [300, 305, 310],
    },
    index=pd.to_datetime(["2024-01-03", "2024-01-02", "2024-01-01"])
)
df = df.sort_index()
weights = {
    "AAPL": 0.4,
    "MSFT": 0.3,
    "GOOG": 0.3,
}
portfolio_returns = portfolio_return(df, weights, V0=1.0)
print(portfolio_returns)