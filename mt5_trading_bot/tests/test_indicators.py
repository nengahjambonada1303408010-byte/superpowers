"""
Unit tests for technical indicators - no MT5 connection required.
"""
import numpy as np
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.indicators import (
    sma, ema, wma, rsi, macd, bollinger_bands, atr, adx,
    stochastic, cci, williams_r, momentum, roc, crosses_above, crosses_below
)


@pytest.fixture
def sample_close():
    np.random.seed(42)
    prices = 100.0 + np.cumsum(np.random.randn(500) * 0.5)
    return np.abs(prices)


@pytest.fixture
def sample_ohlc():
    np.random.seed(42)
    n = 500
    close = 100.0 + np.cumsum(np.random.randn(n) * 0.5)
    close = np.abs(close) + 50
    high = close + np.abs(np.random.randn(n) * 0.3)
    low = close - np.abs(np.random.randn(n) * 0.3)
    open_ = close + np.random.randn(n) * 0.1
    return open_, high, low, close


def test_sma_length(sample_close):
    result = sma(sample_close, 14)
    assert len(result) == len(sample_close)


def test_sma_nan_prefix(sample_close):
    period = 20
    result = sma(sample_close, period)
    assert np.all(np.isnan(result[:period - 1]))
    assert not np.isnan(result[period - 1])


def test_ema_length(sample_close):
    result = ema(sample_close, 14)
    assert len(result) == len(sample_close)


def test_ema_nan_prefix(sample_close):
    period = 14
    result = ema(sample_close, period)
    assert np.all(np.isnan(result[:period - 1]))
    assert not np.isnan(result[period - 1])


def test_rsi_range(sample_close):
    result = rsi(sample_close, 14)
    valid = result[~np.isnan(result)]
    assert np.all(valid >= 0)
    assert np.all(valid <= 100)


def test_macd_shape(sample_close):
    ml, sl, hist = macd(sample_close, 12, 26, 9)
    assert len(ml) == len(sample_close)
    assert len(sl) == len(sample_close)
    assert len(hist) == len(sample_close)


def test_bollinger_bands_ordering(sample_close):
    upper, mid, lower = bollinger_bands(sample_close, 20, 2.0)
    valid = ~(np.isnan(upper) | np.isnan(mid) | np.isnan(lower))
    assert np.all(upper[valid] >= mid[valid])
    assert np.all(mid[valid] >= lower[valid])


def test_atr_positive(sample_ohlc):
    _, high, low, close = sample_ohlc
    result = atr(high, low, close, 14)
    valid = result[~np.isnan(result)]
    assert np.all(valid > 0)


def test_stochastic_range(sample_ohlc):
    _, high, low, close = sample_ohlc
    k, d = stochastic(high, low, close, 14, 3)
    valid_k = k[~np.isnan(k)]
    assert np.all(valid_k >= 0)
    assert np.all(valid_k <= 100)


def test_rsi_length_matches(sample_close):
    for period in [7, 14, 21]:
        result = rsi(sample_close, period)
        assert len(result) == len(sample_close)


def test_momentum_length(sample_close):
    result = momentum(sample_close, 10)
    assert len(result) == len(sample_close)


def test_roc_length(sample_close):
    result = roc(sample_close, 12)
    assert len(result) == len(sample_close)


def test_crosses_above():
    a = np.array([1.0, 2.0, 3.0, 2.0, 1.0])
    b = np.array([2.0, 2.0, 2.0, 2.0, 2.0])
    result = crosses_above(a, b)
    assert result[2] == True  # 2 -> 3 crosses above 2
    assert result[0] == False


def test_crosses_below():
    a = np.array([3.0, 2.0, 1.0, 2.0, 3.0])
    b = np.array([2.0, 2.0, 2.0, 2.0, 2.0])
    result = crosses_below(a, b)
    assert result[2] == True  # 2 -> 1 crosses below 2
