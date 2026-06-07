"""
Indicator Cache - pre-computes all indicator variants once before evolution.
This gives 5-20x speedup when evaluating thousands of formulas on the same dataset.

Instead of recomputing RSI(14), RSI(7), EMA(21), EMA(50)... for EVERY formula,
we compute them ONCE and store in a dict. Each formula evaluation then just
reads from this cache.
"""
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Any
from loguru import logger

from core.indicators import (
    sma, ema, rsi, macd, bollinger_bands, atr, adx,
    stochastic, cci, williams_r, momentum, crosses_above, crosses_below,
)
from core.patterns import compute_all_patterns

# All parameter values we pre-compute (covers PARAM_RANGES)
RSI_PERIODS    = list(range(5, 31))            # 26 variants
EMA_PERIODS    = list(range(5, 201, 3))        # ~66 variants
ATR_PERIODS    = list(range(7, 22))            # 15 variants
ADX_PERIODS    = list(range(7, 22))            # 15 variants
STOCH_K        = list(range(5, 22))            # 17 variants
BB_PERIODS     = list(range(10, 31))           # 21 variants
CCI_PERIODS    = list(range(10, 31))           # 21 variants
WILLR_PERIODS  = list(range(7, 22))            # 15 variants


class IndicatorCache:
    """
    Pre-computes every indicator variant on a DataFrame.

    Usage:
        cache = IndicatorCache(df)
        cache.build()   # one-time cost (a few seconds)
        # Now pass cache to FormulaEngine.compute_signals_cached(df, df_htf, formula, cache)
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.c  = df["close"].values.astype(float)
        self.h  = df["high"].values.astype(float)
        self.l  = df["low"].values.astype(float)
        self.o  = df["open"].values.astype(float)
        self._data: Dict[Tuple, np.ndarray] = {}
        self.patterns: Dict[str, np.ndarray] = {}
        self._built = False

    def build(self) -> None:
        if self._built:
            return
        logger.info("Building indicator cache...")

        # RSI
        for p in RSI_PERIODS:
            self._data[("rsi", p)] = rsi(self.c, p)

        # EMA
        for p in EMA_PERIODS:
            self._data[("ema", p)] = ema(self.c, p)

        # ATR
        for p in ATR_PERIODS:
            self._data[("atr", p)] = atr(self.h, self.l, self.c, p)

        # ADX
        for p in ADX_PERIODS:
            self._data[("adx", p)] = adx(self.h, self.l, self.c, p)

        # Stochastic K (we fix d=3 for cache)
        for k in STOCH_K:
            k_arr, d_arr = stochastic(self.h, self.l, self.c, k, 3)
            self._data[("stoch_k", k)] = k_arr
            self._data[("stoch_d", k)] = d_arr

        # Bollinger Bands (std=2.0 fixed)
        for p in BB_PERIODS:
            u, m, lo = bollinger_bands(self.c, p, 2.0)
            self._data[("bb_upper", p)] = u
            self._data[("bb_mid",   p)] = m
            self._data[("bb_lower", p)] = lo

        # MACD (pre-compute common variants)
        for fast, slow, sig in [(8,16,5),(10,21,7),(12,26,9),(16,34,9)]:
            ml, sl, hist = macd(self.c, fast, slow, sig)
            self._data[("macd_line",   fast, slow, sig)] = ml
            self._data[("macd_signal", fast, slow, sig)] = sl
            self._data[("macd_hist",   fast, slow, sig)] = hist

        # CCI
        for p in CCI_PERIODS:
            self._data[("cci", p)] = cci(self.h, self.l, self.c, p)

        # Williams %R
        for p in WILLR_PERIODS:
            self._data[("willr", p)] = williams_r(self.h, self.l, self.c, p)

        # Patterns (computed once)
        self.patterns = compute_all_patterns(self.df)

        self._built = True
        logger.info(f"Indicator cache built: {len(self._data)} arrays")

    def get_rsi(self, period: int) -> np.ndarray:
        p = self._nearest(period, RSI_PERIODS)
        return self._data[("rsi", p)]

    def get_ema(self, period: int) -> np.ndarray:
        p = self._nearest(period, EMA_PERIODS)
        return self._data[("ema", p)]

    def get_atr(self, period: int) -> np.ndarray:
        p = self._nearest(period, ATR_PERIODS)
        return self._data[("atr", p)]

    def get_adx(self, period: int) -> np.ndarray:
        p = self._nearest(period, ADX_PERIODS)
        return self._data[("adx", p)]

    def get_stoch_k(self, k_period: int) -> np.ndarray:
        p = self._nearest(k_period, STOCH_K)
        return self._data[("stoch_k", p)]

    def get_stoch_d(self, k_period: int) -> np.ndarray:
        p = self._nearest(k_period, STOCH_K)
        return self._data[("stoch_d", p)]

    def get_bb(self, period: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        p = self._nearest(period, BB_PERIODS)
        return (self._data[("bb_upper", p)],
                self._data[("bb_mid",   p)],
                self._data[("bb_lower", p)])

    def get_macd(self, fast: int, slow: int, sig: int):
        # Find nearest pre-computed variant
        candidates = [(8,16,5),(10,21,7),(12,26,9),(16,34,9)]
        best = min(candidates, key=lambda t: abs(t[0]-fast)+abs(t[1]-slow)+abs(t[2]-sig))
        f, s, sg = best
        return (self._data[("macd_line",   f, s, sg)],
                self._data[("macd_signal", f, s, sg)],
                self._data[("macd_hist",   f, s, sg)])

    def get_cci(self, period: int) -> np.ndarray:
        p = self._nearest(period, CCI_PERIODS)
        return self._data[("cci", p)]

    def get_willr(self, period: int) -> np.ndarray:
        p = self._nearest(period, WILLR_PERIODS)
        return self._data[("willr", p)]

    @staticmethod
    def _nearest(val: int, choices: list) -> int:
        return min(choices, key=lambda x: abs(x - val))
