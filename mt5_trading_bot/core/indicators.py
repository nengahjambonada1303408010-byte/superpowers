"""
Technical indicators implemented in pure numpy/pandas.
All functions accept numpy arrays and return numpy arrays.
"""
import numpy as np
import pandas as pd
from typing import Tuple, Dict


def sma(close: np.ndarray, period: int) -> np.ndarray:
    result = np.full_like(close, np.nan, dtype=float)
    for i in range(period - 1, len(close)):
        result[i] = np.mean(close[i - period + 1:i + 1])
    return result


def ema(close: np.ndarray, period: int) -> np.ndarray:
    result = np.full_like(close, np.nan, dtype=float)
    k = 2.0 / (period + 1)
    # find first valid index
    start = period - 1
    if start >= len(close):
        return result
    result[start] = np.mean(close[:period])
    for i in range(start + 1, len(close)):
        result[i] = close[i] * k + result[i - 1] * (1 - k)
    return result


def wma(close: np.ndarray, period: int) -> np.ndarray:
    weights = np.arange(1, period + 1, dtype=float)
    denom = weights.sum()
    result = np.full_like(close, np.nan, dtype=float)
    for i in range(period - 1, len(close)):
        result[i] = np.dot(close[i - period + 1:i + 1], weights) / denom
    return result


def rsi(close: np.ndarray, period: int = 14) -> np.ndarray:
    delta = np.diff(close.astype(float))
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)

    result = np.full(len(close), np.nan)
    if len(gain) < period:
        return result

    avg_gain = np.mean(gain[:period])
    avg_loss = np.mean(loss[:period])

    for i in range(period, len(delta)):
        avg_gain = (avg_gain * (period - 1) + gain[i]) / period
        avg_loss = (avg_loss * (period - 1) + loss[i]) / period
        if avg_loss == 0:
            result[i + 1] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[i + 1] = 100.0 - (100.0 / (1.0 + rs))

    # fill first complete RSI value
    if avg_loss == 0 and period < len(delta):
        result[period] = 100.0
    elif period < len(delta):
        ag0 = np.mean(gain[:period])
        al0 = np.mean(loss[:period])
        if al0 == 0:
            result[period] = 100.0
        else:
            result[period] = 100.0 - 100.0 / (1.0 + ag0 / al0)

    return result


def macd(close: np.ndarray, fast: int = 12, slow: int = 26,
         signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    fast_ema = ema(close, fast)
    slow_ema = ema(close, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(np.where(np.isnan(macd_line), 0, macd_line), signal)
    signal_line = np.where(np.isnan(macd_line), np.nan, signal_line)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(close: np.ndarray, period: int = 20,
                    num_std: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    mid = sma(close, period)
    result_std = np.full_like(close, np.nan, dtype=float)
    for i in range(period - 1, len(close)):
        result_std[i] = np.std(close[i - period + 1:i + 1], ddof=0)
    upper = mid + num_std * result_std
    lower = mid - num_std * result_std
    return upper, mid, lower


def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray,
        period: int = 14) -> np.ndarray:
    high = high.astype(float)
    low = low.astype(float)
    close = close.astype(float)

    tr = np.maximum(high[1:] - low[1:],
          np.maximum(np.abs(high[1:] - close[:-1]),
                     np.abs(low[1:] - close[:-1])))
    tr = np.concatenate([[high[0] - low[0]], tr])

    result = np.full_like(close, np.nan)
    result[period - 1] = np.mean(tr[:period])
    for i in range(period, len(close)):
        result[i] = (result[i - 1] * (period - 1) + tr[i]) / period
    return result


def adx(high: np.ndarray, low: np.ndarray, close: np.ndarray,
        period: int = 14) -> np.ndarray:
    high = high.astype(float)
    low = low.astype(float)
    close = close.astype(float)
    n = len(close)

    plus_dm = np.zeros(n)
    minus_dm = np.zeros(n)
    for i in range(1, n):
        up = high[i] - high[i - 1]
        down = low[i - 1] - low[i]
        plus_dm[i] = up if up > down and up > 0 else 0
        minus_dm[i] = down if down > up and down > 0 else 0

    tr_arr = atr(high, low, close, 1)
    tr_arr = np.where(np.isnan(tr_arr), 0, tr_arr)

    smooth_plus = np.full(n, np.nan)
    smooth_minus = np.full(n, np.nan)
    smooth_tr = np.full(n, np.nan)

    smooth_plus[period] = np.sum(plus_dm[1:period + 1])
    smooth_minus[period] = np.sum(minus_dm[1:period + 1])
    smooth_tr[period] = np.sum(tr_arr[1:period + 1])

    for i in range(period + 1, n):
        smooth_plus[i] = smooth_plus[i - 1] - smooth_plus[i - 1] / period + plus_dm[i]
        smooth_minus[i] = smooth_minus[i - 1] - smooth_minus[i - 1] / period + minus_dm[i]
        smooth_tr[i] = smooth_tr[i - 1] - smooth_tr[i - 1] / period + tr_arr[i]

    pdi = np.where(smooth_tr > 0, 100 * smooth_plus / smooth_tr, 0)
    mdi = np.where(smooth_tr > 0, 100 * smooth_minus / smooth_tr, 0)
    dx = np.where((pdi + mdi) > 0, 100 * np.abs(pdi - mdi) / (pdi + mdi), 0)

    adx_arr = np.full(n, np.nan)
    start = 2 * period
    if start < n:
        adx_arr[start] = np.mean(dx[period:start + 1])
        for i in range(start + 1, n):
            adx_arr[i] = (adx_arr[i - 1] * (period - 1) + dx[i]) / period

    return adx_arr


def stochastic(high: np.ndarray, low: np.ndarray, close: np.ndarray,
               k_period: int = 14, d_period: int = 3) -> Tuple[np.ndarray, np.ndarray]:
    n = len(close)
    k_line = np.full(n, np.nan)

    for i in range(k_period - 1, n):
        highest = np.max(high[i - k_period + 1:i + 1])
        lowest = np.min(low[i - k_period + 1:i + 1])
        if highest != lowest:
            k_line[i] = 100 * (close[i] - lowest) / (highest - lowest)
        else:
            k_line[i] = 50.0

    d_line = sma(np.where(np.isnan(k_line), 0, k_line), d_period)
    d_line = np.where(np.isnan(k_line), np.nan, d_line)
    return k_line, d_line


def cci(high: np.ndarray, low: np.ndarray, close: np.ndarray,
        period: int = 20) -> np.ndarray:
    typical = (high + low + close) / 3.0
    result = np.full(len(close), np.nan)
    for i in range(period - 1, len(close)):
        tp_slice = typical[i - period + 1:i + 1]
        tp_mean = np.mean(tp_slice)
        mad = np.mean(np.abs(tp_slice - tp_mean))
        if mad != 0:
            result[i] = (typical[i] - tp_mean) / (0.015 * mad)
    return result


def williams_r(high: np.ndarray, low: np.ndarray, close: np.ndarray,
               period: int = 14) -> np.ndarray:
    result = np.full(len(close), np.nan)
    for i in range(period - 1, len(close)):
        highest = np.max(high[i - period + 1:i + 1])
        lowest = np.min(low[i - period + 1:i + 1])
        if highest != lowest:
            result[i] = -100 * (highest - close[i]) / (highest - lowest)
        else:
            result[i] = -50.0
    return result


def momentum(close: np.ndarray, period: int = 10) -> np.ndarray:
    result = np.full_like(close, np.nan, dtype=float)
    result[period:] = close[period:] - close[:-period]
    return result


def roc(close: np.ndarray, period: int = 12) -> np.ndarray:
    result = np.full_like(close, np.nan, dtype=float)
    prev = close[:-period].astype(float)
    nonzero = prev != 0
    result[period:] = np.where(nonzero, (close[period:] - prev) / prev * 100, 0)
    return result


def vwap(high: np.ndarray, low: np.ndarray, close: np.ndarray,
         volume: np.ndarray) -> np.ndarray:
    typical = (high + low + close) / 3.0
    vol = volume.astype(float)
    cum_tp_vol = np.cumsum(typical * vol)
    cum_vol = np.cumsum(vol)
    return np.where(cum_vol > 0, cum_tp_vol / cum_vol, np.nan)


def pivot_points(high: float, low: float, close: float) -> Dict[str, float]:
    pp = (high + low + close) / 3.0
    return {
        "pp": pp,
        "r1": 2 * pp - low,
        "r2": pp + (high - low),
        "r3": high + 2 * (pp - low),
        "s1": 2 * pp - high,
        "s2": pp - (high - low),
        "s3": low - 2 * (high - pp),
    }


def crosses_above(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Returns True where a crosses above b (was below, now above)."""
    result = np.zeros(len(a), dtype=bool)
    result[1:] = (a[:-1] <= b[:-1]) & (a[1:] > b[1:])
    return result


def crosses_below(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Returns True where a crosses below b (was above, now below)."""
    result = np.zeros(len(a), dtype=bool)
    result[1:] = (a[:-1] >= b[:-1]) & (a[1:] < b[1:])
    return result
