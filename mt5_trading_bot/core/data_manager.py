"""
Data manager - fetches historical data from MT5 and caches to parquet files.
Handles multi-symbol, multi-timeframe data with efficient storage.
"""
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict

import numpy as np
import pandas as pd
from loguru import logger

from core.mt5_connector import MT5Connector

TIMEFRAME_CANDLES_PER_YEAR = {
    "M1":  525600,
    "M5":  105120,
    "M15": 35040,
    "M30": 17520,
    "H1":  8760,
    "H4":  2190,
    "D1":  252,
    "W1":  52,
}


class DataManager:
    def __init__(self, connector: MT5Connector, cache_dir: str = "data/historical"):
        self.connector = connector
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, pd.DataFrame] = {}

    def fetch_and_cache(self, symbol: str, timeframe: str,
                        years: int = 5) -> Optional[pd.DataFrame]:
        """Fetch N years of data, using parquet cache if available and fresh."""
        cache_path = self._cache_path(symbol, timeframe)
        df = self._load_from_cache(cache_path, symbol, timeframe)

        if df is not None and self._is_cache_fresh(df, timeframe):
            logger.info(f"Using cached data for {symbol} {timeframe}: {len(df)} candles")
            return df

        # Fetch from MT5
        n_candles = TIMEFRAME_CANDLES_PER_YEAR.get(timeframe, 8760) * years
        n_candles = min(n_candles, 200000)  # hard limit for memory safety

        logger.info(f"Fetching {n_candles} candles for {symbol} {timeframe} from MT5...")
        df = self.connector.fetch_rates(symbol, timeframe, n_candles)

        if df is None or len(df) == 0:
            logger.error(f"Failed to fetch {symbol} {timeframe}")
            return None

        self._save_to_cache(df, cache_path)
        self._cache[f"{symbol}_{timeframe}"] = df
        logger.info(f"Fetched and cached {len(df)} candles for {symbol} {timeframe}")
        return df

    def get(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Get cached dataframe (must call fetch_and_cache first)."""
        key = f"{symbol}_{timeframe}"
        if key in self._cache:
            return self._cache[key]
        cache_path = self._cache_path(symbol, timeframe)
        if cache_path.exists():
            return self._load_from_cache(cache_path, symbol, timeframe)
        return None

    def update(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Fetch only new candles since last cache update and append."""
        cache_path = self._cache_path(symbol, timeframe)
        existing = self._load_from_cache(cache_path, symbol, timeframe)

        if existing is None or len(existing) == 0:
            return self.fetch_and_cache(symbol, timeframe)

        last_time = existing.index[-1]
        now = datetime.now(timezone.utc)

        logger.info(f"Updating {symbol} {timeframe} from {last_time}")
        new_df = self.connector.fetch_rates_range(symbol, timeframe, last_time, now)

        if new_df is None or len(new_df) == 0:
            return existing

        combined = pd.concat([existing, new_df])
        combined = combined[~combined.index.duplicated(keep="last")]
        combined.sort_index(inplace=True)

        self._save_to_cache(combined, cache_path)
        self._cache[f"{symbol}_{timeframe}"] = combined
        logger.info(f"Updated {symbol} {timeframe}: {len(new_df)} new candles added")
        return combined

    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add commonly used derived columns to the dataframe."""
        from core.indicators import (
            ema, sma, rsi, macd, bollinger_bands, atr, adx,
            stochastic, cci, williams_r, momentum, roc
        )

        c = df["close"].values
        h = df["high"].values
        l = df["low"].values
        o = df["open"].values
        v = df.get("volume", pd.Series(np.ones(len(df)))).values

        result = df.copy()

        result["ema_9"]   = ema(c, 9)
        result["ema_21"]  = ema(c, 21)
        result["ema_50"]  = ema(c, 50)
        result["ema_200"] = ema(c, 200)
        result["sma_20"]  = sma(c, 20)
        result["sma_50"]  = sma(c, 50)

        result["rsi_14"]  = rsi(c, 14)
        result["rsi_7"]   = rsi(c, 7)

        macd_line, signal_line, hist = macd(c, 12, 26, 9)
        result["macd"]         = macd_line
        result["macd_signal"]  = signal_line
        result["macd_hist"]    = hist

        upper, mid, lower = bollinger_bands(c, 20, 2.0)
        result["bb_upper"] = upper
        result["bb_mid"]   = mid
        result["bb_lower"] = lower

        result["atr_14"]  = atr(h, l, c, 14)
        result["adx_14"]  = adx(h, l, c, 14)

        k, d = stochastic(h, l, c, 14, 3)
        result["stoch_k"] = k
        result["stoch_d"] = d

        result["cci_20"]  = cci(h, l, c, 20)
        result["willr_14"] = williams_r(h, l, c, 14)
        result["mom_10"]  = momentum(c, 10)
        result["roc_12"]  = roc(c, 12)

        # Candle body features
        result["body_size"]   = np.abs(c - o)
        result["upper_shadow"] = h - np.maximum(o, c)
        result["lower_shadow"] = np.minimum(o, c) - l
        result["is_bullish"]  = (c > o).astype(float)

        return result

    def split_data(self, df: pd.DataFrame, train: float = 0.70,
                   val: float = 0.15, test: float = 0.15):
        """Split dataframe chronologically into train/validation/test sets."""
        n = len(df)
        train_end = int(n * train)
        val_end = int(n * (train + val))
        return (
            df.iloc[:train_end].copy(),
            df.iloc[train_end:val_end].copy(),
            df.iloc[val_end:].copy(),
        )

    def _cache_path(self, symbol: str, timeframe: str) -> Path:
        return self.cache_dir / f"{symbol}_{timeframe}.parquet"

    def _load_from_cache(self, path: Path, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        key = f"{symbol}_{timeframe}"
        if key in self._cache:
            return self._cache[key]
        if not path.exists():
            return None
        try:
            df = pd.read_parquet(path)
            self._cache[key] = df
            return df
        except Exception as e:
            logger.warning(f"Failed to load cache {path}: {e}")
            return None

    def _save_to_cache(self, df: pd.DataFrame, path: Path):
        try:
            df.to_parquet(path, engine="pyarrow", compression="snappy")
        except Exception as e:
            logger.warning(f"Failed to save cache {path}: {e}")

    def _is_cache_fresh(self, df: pd.DataFrame, timeframe: str,
                        max_age_factor: float = 2.0) -> bool:
        """Cache is fresh if last candle is recent enough."""
        if df is None or len(df) == 0:
            return False
        last_time = df.index[-1]
        if last_time.tzinfo is None:
            last_time = last_time.tz_localize("UTC")
        now = pd.Timestamp.now(tz="UTC")

        tf_minutes = {
            "M1": 1, "M5": 5, "M15": 15, "M30": 30,
            "H1": 60, "H4": 240, "D1": 1440, "W1": 10080
        }
        minutes = tf_minutes.get(timeframe, 60)
        max_age = timedelta(minutes=minutes * max_age_factor)
        return (now - last_time) < max_age
