# MarketRegime

MarketRegime is a reproducible research and paper-trading laboratory for
identifying historical market states and evaluating simple regime-aware
strategies under chronological validation. It is deliberately a research
tool, not a brokerage or investment-advice product.

## Current verified scope

The acquisition script retrieves daily OHLCV bars for SPY, QQQ, and IWM from
Yahoo Finance's public chart endpoint (`query2.finance.yahoo.com`). Each
retrieval records the endpoint, UTC retrieval time, requested range, ticker,
and response metadata. Yahoo's adjusted close is used for return calculations;
raw downloads are excluded from Git because redistribution rights are not
assumed. Run the script locally to recreate them.

The research runner computes causal return, volatility, trend, momentum, and
drawdown features; a transparent rule baseline; a training-only Gaussian
mixture comparison; and deterministic chronological backtests with explicit
fees and slippage. `src/marketregime/backtest.py` contains the reusable
long-only cash/position ledger used by paper-trading tests. Results are written
to `artifacts/summary.json` and `artifacts/market.json` only after real source
data has been acquired.

## Reproduce

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev,report]'
python scripts/acquire_data.py
python scripts/run_research.py
pytest
```

The acquisition step is network-dependent and must be rerun when creating a
new dated release. No results are claimed until the downloaded files pass the
validation checks in `scripts/run_research.py`.

## Data and licensing

The provider and endpoint are documented in `data/README.md`. This repository
does not commit the provider's raw bars. Derived aggregate research JSON is
versioned only when its provenance manifest and source hashes are present.

## Status

The current release contains the verified acquisition, feature, regime,
cost-aware backtesting, tested ledger, report, and lightweight dashboard
foundation. Additional model classes and deployment should only be added after
the artifacts are regenerated and reviewed; no profitability claim is made.

