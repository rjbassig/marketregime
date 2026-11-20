import pandas as pd
import pytest

from scripts.run_research import features, metrics, validate
from marketregime.backtest import PortfolioLedger


def sample():
    return pd.DataFrame({"date": ["2024-01-02", "2024-01-03", "2024-01-04"], "open": [10, 11, 12], "high": [11, 12, 13], "low": [9, 10, 11], "close": [10.5, 11.5, 12.5], "adj_close": [10.5, 11.5, 12.5], "volume": [100, 110, 120]})


def test_ohlcv_validation_and_features():
    frame = sample()
    validate(frame)
    assert "log_return" in features(frame).columns


def test_invalid_order_rejected():
    frame = sample()
    frame.loc[1, "high"] = 1
    with pytest.raises(ValueError):
        validate(frame)


def test_metrics_are_reproducible():
    result = metrics(pd.Series([0.01, -0.005, 0.02]))
    assert result["observations"] == 3
    assert result["total_return"] == pytest.approx((1.01 * .995 * 1.02) - 1)
    assert "cagr" in result and "sortino" in result and "profit_factor" in result


def test_ledger_reconciles_cash_and_pnl():
    ledger = PortfolioLedger(initial_cash=1_000, fee_bps=0, slippage_bps=0)
    ledger.execute("2024-01-02", "buy", 10, 50)
    assert ledger.mark(55)["equity"] == pytest.approx(1_050)
    ledger.execute("2024-01-03", "sell", 4, 55)
    marked = ledger.mark(55)
    assert marked["cash"] == pytest.approx(720)
    assert marked["quantity"] == pytest.approx(6)
    assert marked["realized_pnl"] == pytest.approx(20)


def test_ledger_rejects_overspending_and_short_sales():
    ledger = PortfolioLedger(initial_cash=100)
    with pytest.raises(ValueError):
        ledger.execute("2024-01-02", "buy", 3, 50)
    with pytest.raises(ValueError):
        ledger.execute("2024-01-02", "sell", 1, 10)

