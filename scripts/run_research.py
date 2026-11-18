from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
ARTIFACTS = ROOT / "artifacts"


def validate(frame: pd.DataFrame) -> None:
    required = {"date", "open", "high", "low", "close", "adj_close", "volume"}
    if not required <= set(frame.columns):
        raise ValueError(f"missing columns: {required - set(frame.columns)}")
    dates = pd.to_datetime(frame.date)
    if not dates.is_monotonic_increasing or dates.duplicated().any():
        raise ValueError("dates must be unique and chronological")
    if (frame[["open", "high", "low", "close", "adj_close"]] <= 0).any().any():
        raise ValueError("prices must be positive")
    if (frame.volume < 0).any() or (frame.high < frame[["open", "close"]].max(axis=1)).any() or (frame.low > frame[["open", "close"]].min(axis=1)).any():
        raise ValueError("invalid OHLCV row")


def features(frame: pd.DataFrame) -> pd.DataFrame:
    x = frame.copy()
    x["date"] = pd.to_datetime(x.date)
    x["log_return"] = np.log(x.adj_close).diff()
    x["volatility_20"] = x.log_return.rolling(20, min_periods=20).std() * np.sqrt(252)
    x["ma_ratio"] = x.adj_close.rolling(20, min_periods=20).mean() / x.adj_close.rolling(100, min_periods=100).mean()
    x["momentum_20"] = x.adj_close.pct_change(20)
    x["peak"] = x.adj_close.cummax()
    x["drawdown"] = x.adj_close / x.peak - 1
    x["rule_regime"] = np.select(
        [(x.ma_ratio >= 1.02) & (x.volatility_20 < 0.35), (x.ma_ratio <= 0.98) & (x.volatility_20 < 0.35), x.volatility_20 >= 0.35],
        ["bull", "bear", "stressed"], default="sideways")
    return x.dropna(subset=["log_return", "volatility_20", "ma_ratio", "momentum_20"])


def metrics(returns: pd.Series) -> dict:
    returns = returns.dropna()
    equity = (1 + returns).cumprod()
    drawdown = equity / equity.cummax() - 1
    vol = float(returns.std(ddof=1) * np.sqrt(252)) if len(returns) > 1 else 0.0
    return {"total_return": float(equity.iloc[-1] - 1), "annualized_volatility": vol,
            "sharpe": float(returns.mean() / returns.std(ddof=1) * np.sqrt(252)) if returns.std(ddof=1) else 0.0,
            "max_drawdown": float(drawdown.min()), "observations": int(len(returns))}


def backtest(exposure: pd.Series, next_returns: pd.Series, fee_bps: float = 5.0, slippage_bps: float = 5.0) -> tuple[pd.Series, dict]:
    """Apply next-bar returns with explicit turnover costs; no future prices are used."""
    exposure = exposure.fillna(0).astype(float)
    turnover = exposure.diff().abs().fillna(exposure.abs())
    costs = turnover * ((fee_bps + slippage_bps) / 10_000)
    realized = exposure * next_returns.fillna(0) - costs
    return realized, {"trade_count": int((turnover > 0).sum()), "turnover": float(turnover.sum()), "fee_bps": fee_bps, "slippage_bps": slippage_bps}


def run_one(ticker: str) -> tuple[dict, list[dict]]:
    frame = pd.read_csv(RAW / f"{ticker.lower()}.csv")
    validate(frame)
    x = features(frame)
    split = int(len(x) * 0.7)
    train = x.iloc[:split]
    test = x.iloc[split:].copy()
    cols = ["log_return", "volatility_20", "ma_ratio", "momentum_20"]
    model = GaussianMixture(n_components=3, covariance_type="full", random_state=7, n_init=5)
    model.fit(train[cols])
    test["gmm_state"] = model.predict(test[cols])
    test["benchmark_return"] = test.log_return.shift(-1)
    test["trend_exposure"] = (test.ma_ratio > 1).astype(float)
    test["regime_exposure"] = ((test.ma_ratio > 1) & (test.volatility_20 < 0.35)).astype(float)
    test["trend_return"], trend_meta = backtest(test.trend_exposure, test.benchmark_return)
    test["regime_return"], regime_meta = backtest(test.regime_exposure, test.benchmark_return)
    rows = test.dropna(subset=["benchmark_return"]).tail(1200)
    summary = {"ticker": ticker, "source_rows": int(len(frame)), "first_date": str(frame.date.iloc[0]), "last_date": str(frame.date.iloc[-1]),
               "chronological_split": {"train_rows": int(split), "test_rows": int(len(x) - split), "test_start": str(test.date.iloc[0])},
               "regime_counts_test": {str(k): int(v) for k, v in test.rule_regime.value_counts().to_dict().items()},
               "strategies": {"buy_and_hold": {**metrics(rows.benchmark_return), "trade_count": 1, "turnover": 1.0, "fee_bps": 5.0, "slippage_bps": 5.0}, "trend_baseline": {**metrics(rows.trend_return), **trend_meta}, "regime_aware": {**metrics(rows.regime_return), **regime_meta}}}
    records = rows[["date", "adj_close", "rule_regime", "gmm_state", "benchmark_return", "trend_return", "regime_return"]].copy()
    records["date"] = records.date.dt.strftime("%Y-%m-%d")
    return summary, records.to_dict(orient="records")


def main() -> None:
    ARTIFACTS.mkdir(exist_ok=True)
    summaries, market = [], {}
    for ticker in ("SPY", "QQQ", "IWM"):
        summary, rows = run_one(ticker)
        summaries.append(summary)
        market[ticker] = rows
    provenance = json.loads((ROOT / "data" / "provenance.json").read_text())
    manifest = {"generated_at": datetime.now(timezone.utc).isoformat(), "method": "causal rolling features; train-only 3-state Gaussian mixture; chronological 70/30 split; next-bar close proxy; 5 bps fees plus 5 bps slippage on strategy turnover", "source": provenance, "sha256_raw": {}}
    for ticker in ("SPY", "QQQ", "IWM"):
        path = RAW / f"{ticker.lower()}.csv"
        manifest["sha256_raw"][ticker] = hashlib.sha256(path.read_bytes()).hexdigest()
    (ARTIFACTS / "summary.json").write_text(json.dumps({"manifest": manifest, "assets": summaries}, indent=2) + "\n")
    (ARTIFACTS / "market.json").write_text(json.dumps(market, indent=2) + "\n")
    print(json.dumps({"assets": summaries, "manifest": manifest}, indent=2))


if __name__ == "__main__":
    main()

