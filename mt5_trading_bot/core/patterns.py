"""
Candlestick pattern detection and price action analysis.
All functions return numpy boolean arrays or integer arrays (-1, 0, 1).
"""
import numpy as np
import pandas as pd
from typing import Dict, List


def _body(open_: np.ndarray, close: np.ndarray) -> np.ndarray:
    return np.abs(close - open_)


def _upper_shadow(open_: np.ndarray, high: np.ndarray, close: np.ndarray) -> np.ndarray:
    return high - np.maximum(open_, close)


def _lower_shadow(open_: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    return np.minimum(open_, close) - low


def _candle_range(high: np.ndarray, low: np.ndarray) -> np.ndarray:
    return high - low


def detect_doji(open_: np.ndarray, high: np.ndarray, low: np.ndarray,
                close: np.ndarray, threshold: float = 0.1) -> np.ndarray:
    body = _body(open_, close)
    rng = _candle_range(high, low)
    rng = np.where(rng == 0, 1e-10, rng)
    return (body / rng) < threshold


def detect_engulfing(open_: np.ndarray, high: np.ndarray, low: np.ndarray,
                     close: np.ndarray) -> np.ndarray:
    result = np.zeros(len(close), dtype=int)
    for i in range(1, len(close)):
        prev_bull = close[i - 1] > open_[i - 1]
        prev_bear = close[i - 1] < open_[i - 1]
        curr_bull = close[i] > open_[i]
        curr_bear = close[i] < open_[i]

        # Bullish engulfing: prev candle is bearish, current is bullish and engulfs
        if prev_bear and curr_bull and open_[i] <= close[i - 1] and close[i] >= open_[i - 1]:
            result[i] = 1
        # Bearish engulfing: prev candle is bullish, current is bearish and engulfs
        elif prev_bull and curr_bear and open_[i] >= close[i - 1] and close[i] <= open_[i - 1]:
            result[i] = -1
    return result


def detect_hammer(open_: np.ndarray, high: np.ndarray, low: np.ndarray,
                  close: np.ndarray) -> np.ndarray:
    body = _body(open_, close)
    lower = _lower_shadow(open_, low, close)
    upper = _upper_shadow(open_, high, close)
    rng = _candle_range(high, low)
    rng = np.where(rng == 0, 1e-10, rng)
    return (lower >= 2 * body) & (upper <= body * 0.3) & (body / rng > 0.1)


def detect_shooting_star(open_: np.ndarray, high: np.ndarray, low: np.ndarray,
                         close: np.ndarray) -> np.ndarray:
    body = _body(open_, close)
    lower = _lower_shadow(open_, low, close)
    upper = _upper_shadow(open_, high, close)
    rng = _candle_range(high, low)
    rng = np.where(rng == 0, 1e-10, rng)
    return (upper >= 2 * body) & (lower <= body * 0.3) & (body / rng > 0.1)


def detect_morning_star(open_: np.ndarray, high: np.ndarray, low: np.ndarray,
                        close: np.ndarray) -> np.ndarray:
    result = np.zeros(len(close), dtype=bool)
    for i in range(2, len(close)):
        # Day 1: large bearish candle
        day1_bear = close[i - 2] < open_[i - 2] and _body(open_[i - 2:i - 1], close[i - 2:i - 1])[0] > 0
        # Day 2: small body (doji-like), gaps down
        day2_small = _body(open_[i - 1:i], close[i - 1:i])[0] < _body(open_[i - 2:i - 1], close[i - 2:i - 1])[0] * 0.3
        # Day 3: large bullish candle closing above day 1 midpoint
        mid1 = (open_[i - 2] + close[i - 2]) / 2
        day3_bull = close[i] > mid1 and close[i] > open_[i]
        result[i] = day1_bear and day2_small and day3_bull
    return result


def detect_evening_star(open_: np.ndarray, high: np.ndarray, low: np.ndarray,
                        close: np.ndarray) -> np.ndarray:
    result = np.zeros(len(close), dtype=bool)
    for i in range(2, len(close)):
        day1_bull = close[i - 2] > open_[i - 2]
        day2_small = _body(open_[i - 1:i], close[i - 1:i])[0] < _body(open_[i - 2:i - 1], close[i - 2:i - 1])[0] * 0.3
        mid1 = (open_[i - 2] + close[i - 2]) / 2
        day3_bear = close[i] < mid1 and close[i] < open_[i]
        result[i] = day1_bull and day2_small and day3_bear
    return result


def detect_three_white_soldiers(open_: np.ndarray, high: np.ndarray, low: np.ndarray,
                                 close: np.ndarray) -> np.ndarray:
    result = np.zeros(len(close), dtype=bool)
    for i in range(2, len(close)):
        all_bull = (close[i] > open_[i]) and (close[i - 1] > open_[i - 1]) and (close[i - 2] > open_[i - 2])
        each_higher = close[i] > close[i - 1] > close[i - 2]
        result[i] = all_bull and each_higher
    return result


def detect_three_black_crows(open_: np.ndarray, high: np.ndarray, low: np.ndarray,
                              close: np.ndarray) -> np.ndarray:
    result = np.zeros(len(close), dtype=bool)
    for i in range(2, len(close)):
        all_bear = (close[i] < open_[i]) and (close[i - 1] < open_[i - 1]) and (close[i - 2] < open_[i - 2])
        each_lower = close[i] < close[i - 1] < close[i - 2]
        result[i] = all_bear and each_lower
    return result


def detect_inside_bar(open_: np.ndarray, high: np.ndarray, low: np.ndarray,
                      close: np.ndarray) -> np.ndarray:
    result = np.zeros(len(close), dtype=bool)
    result[1:] = (high[1:] <= high[:-1]) & (low[1:] >= low[:-1])
    return result


def detect_pin_bar(open_: np.ndarray, high: np.ndarray, low: np.ndarray,
                   close: np.ndarray) -> np.ndarray:
    """Bullish pin bars (hammer-like) return 1, bearish (shooting star-like) return -1."""
    result = np.zeros(len(close), dtype=int)
    result[detect_hammer(open_, high, low, close)] = 1
    result[detect_shooting_star(open_, high, low, close)] = -1
    return result


def support_resistance_levels(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                               lookback: int = 50) -> np.ndarray:
    """Returns array of support/resistance price levels at each bar."""
    n = len(close)
    levels = np.full(n, np.nan)
    for i in range(lookback, n):
        slice_high = high[i - lookback:i]
        slice_low = low[i - lookback:i]
        # Simple approach: pivot highs and lows
        pivot_highs = []
        pivot_lows = []
        for j in range(2, len(slice_high) - 2):
            if slice_high[j] > slice_high[j - 1] and slice_high[j] > slice_high[j + 1]:
                pivot_highs.append(slice_high[j])
            if slice_low[j] < slice_low[j - 1] and slice_low[j] < slice_low[j + 1]:
                pivot_lows.append(slice_low[j])
        all_levels = pivot_highs + pivot_lows
        if all_levels:
            # Find nearest level to current close
            diffs = [abs(l - close[i]) for l in all_levels]
            levels[i] = all_levels[np.argmin(diffs)]
    return levels


def near_support_resistance(close: np.ndarray, sr_levels: np.ndarray,
                             tolerance_pct: float = 0.001) -> np.ndarray:
    """Returns True where close is within tolerance% of a support/resistance level."""
    result = np.zeros(len(close), dtype=bool)
    valid = ~np.isnan(sr_levels)
    diff = np.where(valid, np.abs(close - sr_levels) / np.where(close == 0, 1, close), np.inf)
    result = diff < tolerance_pct
    return result


def higher_high_higher_low(high: np.ndarray, low: np.ndarray, n: int = 5) -> np.ndarray:
    """Returns True where the last n bars show HH-HL structure (uptrend)."""
    result = np.zeros(len(high), dtype=bool)
    for i in range(n, len(high)):
        h_slice = high[i - n:i + 1]
        l_slice = low[i - n:i + 1]
        hh = all(h_slice[j] > h_slice[j - 1] for j in range(1, len(h_slice)))
        hl = all(l_slice[j] > l_slice[j - 1] for j in range(1, len(l_slice)))
        result[i] = hh and hl
    return result


def lower_high_lower_low(high: np.ndarray, low: np.ndarray, n: int = 5) -> np.ndarray:
    """Returns True where the last n bars show LH-LL structure (downtrend)."""
    result = np.zeros(len(high), dtype=bool)
    for i in range(n, len(high)):
        h_slice = high[i - n:i + 1]
        l_slice = low[i - n:i + 1]
        lh = all(h_slice[j] < h_slice[j - 1] for j in range(1, len(h_slice)))
        ll = all(l_slice[j] < l_slice[j - 1] for j in range(1, len(l_slice)))
        result[i] = lh and ll
    return result


def compute_all_patterns(df: pd.DataFrame) -> Dict[str, np.ndarray]:
    o = df["open"].values
    h = df["high"].values
    l = df["low"].values
    c = df["close"].values
    return {
        "doji":              detect_doji(o, h, l, c),
        "engulfing":         detect_engulfing(o, h, l, c),
        "hammer":            detect_hammer(o, h, l, c),
        "shooting_star":     detect_shooting_star(o, h, l, c),
        "morning_star":      detect_morning_star(o, h, l, c),
        "evening_star":      detect_evening_star(o, h, l, c),
        "three_soldiers":    detect_three_white_soldiers(o, h, l, c),
        "three_crows":       detect_three_black_crows(o, h, l, c),
        "inside_bar":        detect_inside_bar(o, h, l, c),
        "pin_bar":           detect_pin_bar(o, h, l, c),
        "hh_hl":             higher_high_higher_low(h, l, n=3),
        "lh_ll":             lower_high_lower_low(h, l, n=3),
    }
