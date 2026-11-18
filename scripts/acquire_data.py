from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
TICKERS = ("SPY", "QQQ", "IWM")


def _epoch(value: str) -> int:
    return int(pd.Timestamp(value, tz="UTC").timestamp())


def fetch(ticker: str, start: str, end: str) -> dict:
    host = os.getenv("YAHOO_CHART_HOST", "query2.finance.yahoo.com")
    url = (f"https://{host}/v8/finance/chart/{ticker}?period1={_epoch(start)}"
           f"&period2={_epoch(end)}&interval=1d&events=div%2Csplits&includeAdjustedClose=true")
    request = Request(url, headers={"User-Agent": "MarketRegime/0.1 research client"})
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    result = (payload.get("chart", {}).get("result") or [None])[0]
    if not result or not result.get("timestamp"):
        raise RuntimeError(f"No chart data returned for {ticker}")
    q = result["indicators"]["quote"][0]
    adj = result["indicators"].get("adjclose", [{"adjclose": []}])[0]["adjclose"]
    rows = []
    for i, ts in enumerate(result["timestamp"]):
        rows.append({"date": pd.to_datetime(ts, unit="s", utc=True).date().isoformat(),
                     "open": q["open"][i], "high": q["high"][i], "low": q["low"][i],
                     "close": q["close"][i], "adj_close": adj[i] if i < len(adj) else q["close"][i],
                     "volume": q["volume"][i]})
    frame = pd.DataFrame(rows).dropna(subset=["open", "high", "low", "close", "adj_close"])
    frame.to_csv(RAW / f"{ticker.lower()}.csv", index=False)
    return {"ticker": ticker, "url": url, "rows": len(frame), "first_date": frame.date.min(),
            "last_date": frame.date.max(), "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "currency": result.get("meta", {}).get("currency"), "exchange": result.get("meta", {}).get("fullExchangeName")}


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    start = os.getenv("MARKETREGIME_START", "2010-01-01")
    end = os.getenv("MARKETREGIME_END", datetime.now(timezone.utc).date().isoformat())
    manifest = {"provider": "Yahoo Finance", "retrieval_started_at": datetime.now(timezone.utc).isoformat(),
                "adjustment_policy": "adjusted close for returns; provider OHLCV retained for display",
                "tickers": [fetch(t, start, end) for t in TICKERS]}
    (ROOT / "data" / "provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

