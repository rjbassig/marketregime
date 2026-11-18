# MarketRegime: Chronological Market-Regime and Strategy Evaluation

**Research release 0.1 · Randall Bassig · 2026-11-18**

## Abstract

This release asks whether simple market-state labels add information beyond
trend and buy-and-hold baselines. It uses daily SPY, QQQ, and IWM bars retrieved
from Yahoo Finance's chart endpoint. Adjusted close is used for returns. A
70/30 chronological split reserves the final 30% for evaluation. A transparent
trailing-feature rule classifier is compared with a three-state Gaussian
mixture fit on the training window only. Backtests use next-bar close returns;
the current baseline is explicitly zero-cost and is not a live-trading claim.

## Data and reproducibility

Each asset contains 4,245 validated daily observations from 2010-01-04 through
2026-11-17. The exact request URLs, UTC retrieval times, response metadata, and
raw-file SHA-256 hashes are in `data/provenance.json` and
`artifacts/summary.json`. Raw provider files are ignored by Git because this
project does not assume redistribution rights under Yahoo Finance terms.

Validation checks enforce chronological unique dates, positive prices,
consistent OHLC bounds, finite adjusted close, and nonnegative volume.

## Methods

Features are trailing log return, 20-session annualized volatility, a 20/100
moving-average ratio, 20-session momentum, and running drawdown. The rule
baseline labels bull, bear, stressed, or sideways using trailing trend and
volatility thresholds. The statistical comparison is a seeded three-component
Gaussian mixture fit only on the first 70% of each asset's feature history;
state identifiers are descriptive and are not presented as causal forecasts.

The trend baseline holds when the trailing moving-average ratio exceeds one.
The regime-aware strategy additionally requires volatility below 35%. Results
below are calculated on the latest 1,200 rows of the chronological holdout
window. They are historical descriptive results, not expected returns.

## Verified held-out results

| Asset | Buy/hold return | Buy/hold Sharpe | Buy/hold max DD | Trend return | Regime-aware return | Regime-aware Sharpe |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SPY | 61.96% | 0.67 | -23.45% | 36.03% | 36.03% | 0.62 |
| QQQ | 66.02% | 0.57 | -32.25% | 55.43% | 58.07% | 0.69 |
| IWM | 27.78% | 0.34 | -28.23% | -16.01% | -16.01% | -0.16 |

The QQQ regime-aware rule returned 58.07% with Sharpe 0.69 and maximum drawdown
-14.56%, compared with 55.43% for its cost-aware trend baseline. SPY and IWM
did not improve. That mixed result is the appropriate conclusion:
the release does not support a universal regime premium. Transaction-cost
sensitivity, a full trade ledger, and a formal walk-forward refit schedule are
still required before stronger claims.

## Limitations

Daily bars cannot establish intraday execution precision. The current baseline
uses a next-bar close proxy and zero fees/slippage, so it is optimistic. Public
provider revisions and adjustment conventions can change a rerun. Gaussian
mixture labels are not stable identities across refits without an explicit
alignment procedure. No result is financial advice or a probability of future
profit.

## Reproduce

```bash
python scripts/acquire_data.py
python scripts/run_research.py
pytest
cd web && npm install && npm run build
```

