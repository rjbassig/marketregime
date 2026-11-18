# Data provenance

MarketRegime uses Yahoo Finance's public chart API at
`https://query2.finance.yahoo.com/v8/finance/chart/{TICKER}` for daily bars.
The endpoint returned real OHLCV records for SPY, QQQ, and IWM during the
initial availability check on 2026-11-17. Requests include `events=div,splits`
and `includeAdjustedClose=true`.

The pipeline stores raw JSON/CSV files locally under `data/raw/` and excludes
them from Git. Yahoo Finance terms and redistribution rights can change, so
raw provider data is not republished here. Reproducers should run
`python scripts/acquire_data.py` and retain the generated provenance metadata.

Adjustment policy: adjusted close is used for returns and backtests to account
for splits and distributions; OHLC and volume remain provider-reported fields
for chart display. The validator checks chronological ordering, duplicate
dates, finite prices, positive prices, `high >= max(open, close)`,
`low <= min(open, close)`, and nonnegative volume.

