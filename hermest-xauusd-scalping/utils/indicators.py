import numpy as np
import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def latest_atr(df: pd.DataFrame, period: int = 14) -> float:
    series = atr(df, period)
    return float(series.iloc[-1]) if not series.empty else 0.0


def latest_ema(df: pd.DataFrame, period: int = 20) -> float:
    series = ema(df["close"], period)
    return float(series.iloc[-1]) if not series.empty else 0.0


def latest_rsi(df: pd.DataFrame, period: int = 14) -> float:
    series = rsi(df["close"], period)
    return float(series.iloc[-1]) if not series.empty else 50.0
