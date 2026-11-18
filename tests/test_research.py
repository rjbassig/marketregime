import pandas as pd
import pytest

from scripts.run_research import features, metrics, validate


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

