"""
Formula Engine - builds, encodes, and evaluates trading signal formulas.
Each formula is a dictionary of conditions evaluated on indicator data.
"""
import uuid
import random
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple

from core.indicators import (
    ema, sma, rsi, macd, bollinger_bands, atr, adx,
    stochastic, cci, williams_r, momentum, roc,
    crosses_above, crosses_below,
)
from core.patterns import compute_all_patterns

# ------- Parameter Space Definition -------

CONDITION_TYPES = [
    "RSI_OVERSOLD",       # RSI < threshold → buy signal
    "RSI_OVERBOUGHT",     # RSI > threshold → sell signal
    "RSI_CROSS_UP",       # RSI crosses above threshold
    "RSI_CROSS_DOWN",     # RSI crosses below threshold
    "EMA_CROSS_UP",       # Fast EMA crosses above slow EMA
    "EMA_CROSS_DOWN",     # Fast EMA crosses below slow EMA
    "MACD_CROSS_UP",      # MACD crosses above signal
    "MACD_CROSS_DOWN",    # MACD crosses below signal
    "BB_BELOW_LOWER",     # Price below lower BB
    "BB_ABOVE_UPPER",     # Price above upper BB
    "BB_SQUEEZE",         # BB width narrow (consolidation)
    "ADX_STRONG",         # ADX > threshold (strong trend)
    "STOCH_OVERSOLD",     # Stochastic K < threshold
    "STOCH_OVERBOUGHT",   # Stochastic K > threshold
    "STOCH_CROSS_UP",     # K crosses above D
    "STOCH_CROSS_DOWN",   # K crosses below D
    "CCI_OVERSOLD",       # CCI < threshold
    "CCI_OVERBOUGHT",     # CCI > threshold
    "WILLIAMS_R_OVERSOLD",
    "WILLIAMS_R_OVERBOUGHT",
    "MOMENTUM_POSITIVE",
    "MOMENTUM_NEGATIVE",
    "PATTERN_ENGULFING_BULL",
    "PATTERN_ENGULFING_BEAR",
    "PATTERN_HAMMER",
    "PATTERN_SHOOTING_STAR",
    "PATTERN_INSIDE_BAR",
    "TREND_UPTREND",      # HH-HL structure
    "TREND_DOWNTREND",    # LH-LL structure
    "PRICE_ABOVE_EMA200", # Price above long-term EMA
    "PRICE_BELOW_EMA200",
]

PARAM_RANGES = {
    "rsi_period":       (5, 30),
    "rsi_threshold":    (20, 80),
    "ema_fast":         (5, 30),
    "ema_slow":         (20, 200),
    "macd_fast":        (8, 20),
    "macd_slow":        (16, 40),
    "macd_signal":      (5, 15),
    "bb_period":        (10, 30),
    "bb_std":           (1.5, 3.0),
    "adx_period":       (7, 21),
    "adx_threshold":    (20, 45),
    "stoch_k":          (5, 21),
    "stoch_d":          (3, 9),
    "stoch_threshold":  (15, 40),
    "cci_period":       (10, 30),
    "cci_threshold":    (80, 200),
    "willr_period":     (7, 21),
    "willr_threshold":  (15, 40),
    "mom_period":       (5, 20),
    "ema200_period":    (150, 250),
    "atr_period":       (7, 21),
    "sl_atr_mult":      (0.8, 3.0),
    "n_conditions":     (1, 4),    # how many conditions must be met
}

DIRECTION_TYPES = ["buy", "sell"]


class FormulaEngine:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def random_formula(self) -> Dict:
        """Generate a random formula configuration."""
        direction = random.choice(DIRECTION_TYPES)
        buy_conditions = [c for c in CONDITION_TYPES if
                          any(k in c for k in ["OVERSOLD", "UP", "BULL", "UPTREND",
                                               "POSITIVE", "ABOVE", "SQUEEZE"])]
        sell_conditions = [c for c in CONDITION_TYPES if
                           any(k in c for k in ["OVERBOUGHT", "DOWN", "BEAR", "DOWNTREND",
                                                "NEGATIVE", "BELOW"])]
        neutral_conditions = [c for c in CONDITION_TYPES if c not in buy_conditions and c not in sell_conditions]

        pool = (buy_conditions if direction == "buy" else sell_conditions) + neutral_conditions
        n_conds = random.randint(1, 3)
        selected = random.sample(pool, min(n_conds, len(pool)))

        params = {
            "rsi_period":      random.randint(*PARAM_RANGES["rsi_period"]),
            "rsi_threshold":   random.randint(20, 40) if direction == "buy" else random.randint(60, 80),
            "ema_fast":        random.randint(*PARAM_RANGES["ema_fast"]),
            "ema_slow":        random.randint(21, 100),
            "macd_fast":       random.randint(*PARAM_RANGES["macd_fast"]),
            "macd_slow":       random.randint(*PARAM_RANGES["macd_slow"]),
            "macd_signal":     random.randint(*PARAM_RANGES["macd_signal"]),
            "bb_period":       random.randint(*PARAM_RANGES["bb_period"]),
            "bb_std":          round(random.uniform(*PARAM_RANGES["bb_std"]), 1),
            "adx_period":      random.randint(*PARAM_RANGES["adx_period"]),
            "adx_threshold":   random.randint(*PARAM_RANGES["adx_threshold"]),
            "stoch_k":         random.randint(*PARAM_RANGES["stoch_k"]),
            "stoch_d":         random.randint(*PARAM_RANGES["stoch_d"]),
            "stoch_threshold": random.randint(*PARAM_RANGES["stoch_threshold"]),
            "cci_period":      random.randint(*PARAM_RANGES["cci_period"]),
            "cci_threshold":   random.randint(*PARAM_RANGES["cci_threshold"]),
            "willr_period":    random.randint(*PARAM_RANGES["willr_period"]),
            "willr_threshold": random.randint(*PARAM_RANGES["willr_threshold"]),
            "mom_period":      random.randint(*PARAM_RANGES["mom_period"]),
            "ema200_period":   random.randint(*PARAM_RANGES["ema200_period"]),
            "atr_period":      random.randint(*PARAM_RANGES["atr_period"]),
            "sl_atr_mult":     round(random.uniform(*PARAM_RANGES["sl_atr_mult"]), 2),
        }

        # Ensure ema_fast < ema_slow
        if params["ema_fast"] >= params["ema_slow"]:
            params["ema_slow"] = params["ema_fast"] + random.randint(5, 50)
        if params["macd_fast"] >= params["macd_slow"]:
            params["macd_slow"] = params["macd_fast"] + random.randint(4, 20)

        return {
            "id": str(uuid.uuid4())[:8],
            "direction": direction,
            "conditions": selected,
            "params": params,
        }

    def generate_population(self, size: int) -> List[Dict]:
        return [self.random_formula() for _ in range(size)]

    def formula_to_vector(self, formula: Dict) -> np.ndarray:
        """Encode formula as float vector for genetic operations."""
        cond_encoded = np.zeros(len(CONDITION_TYPES))
        for c in formula["conditions"]:
            if c in CONDITION_TYPES:
                cond_encoded[CONDITION_TYPES.index(c)] = 1.0

        direction_bit = 1.0 if formula["direction"] == "buy" else 0.0
        p = formula["params"]
        param_vec = np.array([
            p["rsi_period"],
            p["rsi_threshold"],
            p["ema_fast"],
            p["ema_slow"],
            p["macd_fast"],
            p["macd_slow"],
            p["macd_signal"],
            p["bb_period"],
            p["bb_std"],
            p["adx_period"],
            p["adx_threshold"],
            p["stoch_k"],
            p["stoch_d"],
            p["stoch_threshold"],
            p["cci_period"],
            p["cci_threshold"],
            p["willr_period"],
            p["willr_threshold"],
            p["mom_period"],
            p["ema200_period"],
            p["atr_period"],
            p["sl_atr_mult"],
            direction_bit,
        ], dtype=float)

        return np.concatenate([cond_encoded, param_vec])

    def vector_to_formula(self, vec: np.ndarray) -> Dict:
        """Decode float vector back to formula dictionary."""
        n_cond = len(CONDITION_TYPES)
        cond_vec = vec[:n_cond]
        param_vec = vec[n_cond:]

        conditions = [CONDITION_TYPES[i] for i in range(n_cond) if cond_vec[i] > 0.5]
        if not conditions:
            conditions = [random.choice(CONDITION_TYPES)]

        direction = "buy" if param_vec[22] > 0.5 else "sell"

        def clip(val, lo, hi, as_int=True):
            v = int(round(np.clip(val, lo, hi))) if as_int else float(np.clip(val, lo, hi))
            return v

        params = {
            "rsi_period":      clip(param_vec[0], 5, 30),
            "rsi_threshold":   clip(param_vec[1], 20, 80),
            "ema_fast":        clip(param_vec[2], 5, 30),
            "ema_slow":        clip(param_vec[3], 21, 200),
            "macd_fast":       clip(param_vec[4], 8, 20),
            "macd_slow":       clip(param_vec[5], 16, 40),
            "macd_signal":     clip(param_vec[6], 5, 15),
            "bb_period":       clip(param_vec[7], 10, 30),
            "bb_std":          clip(param_vec[8], 1.5, 3.0, as_int=False),
            "adx_period":      clip(param_vec[9], 7, 21),
            "adx_threshold":   clip(param_vec[10], 20, 45),
            "stoch_k":         clip(param_vec[11], 5, 21),
            "stoch_d":         clip(param_vec[12], 3, 9),
            "stoch_threshold": clip(param_vec[13], 15, 40),
            "cci_period":      clip(param_vec[14], 10, 30),
            "cci_threshold":   clip(param_vec[15], 80, 200),
            "willr_period":    clip(param_vec[16], 7, 21),
            "willr_threshold": clip(param_vec[17], 15, 40),
            "mom_period":      clip(param_vec[18], 5, 20),
            "ema200_period":   clip(param_vec[19], 150, 250),
            "atr_period":      clip(param_vec[20], 7, 21),
            "sl_atr_mult":     clip(param_vec[21], 0.8, 3.0, as_int=False),
        }

        if params["ema_fast"] >= params["ema_slow"]:
            params["ema_slow"] = params["ema_fast"] + 10
        if params["macd_fast"] >= params["macd_slow"]:
            params["macd_slow"] = params["macd_fast"] + 8

        return {
            "id": str(uuid.uuid4())[:8],
            "direction": direction,
            "conditions": conditions,
            "params": params,
        }

    def compute_signals(self, df_entry: pd.DataFrame, df_htf: pd.DataFrame,
                        formula: Dict) -> np.ndarray:
        """
        Evaluate formula conditions on entry + HTF dataframes.
        Returns array: 1=buy, -1=sell, 0=no signal.
        """
        n = len(df_entry)
        p = formula["params"]
        direction = formula["direction"]
        conditions = formula["conditions"]

        c  = df_entry["close"].values
        h  = df_entry["high"].values
        l  = df_entry["low"].values
        o  = df_entry["open"].values

        # Compute all indicators
        rsi_arr   = rsi(c, p["rsi_period"])
        ema_f     = ema(c, p["ema_fast"])
        ema_s     = ema(c, p["ema_slow"])
        ema200    = ema(c, p["ema200_period"])
        macd_l, macd_sig, macd_h = macd(c, p["macd_fast"], p["macd_slow"], p["macd_signal"])
        bb_u, bb_m, bb_l = bollinger_bands(c, p["bb_period"], p["bb_std"])
        adx_arr   = adx(h, l, c, p["adx_period"])
        atr_arr   = atr(h, l, c, p["atr_period"])
        stoch_k, stoch_d = stochastic(h, l, c, p["stoch_k"], p["stoch_d"])
        cci_arr   = cci(h, l, c, p["cci_period"])
        willr_arr = williams_r(h, l, c, p["willr_period"])
        mom_arr   = momentum(c, p["mom_period"])

        patterns  = compute_all_patterns(df_entry)

        # Evaluate HTF trend
        htf_trend = self._compute_htf_trend(df_htf, df_entry.index)

        # Build condition mask
        condition_masks = []
        for cond in conditions:
            mask = self._evaluate_condition(
                cond, c, h, l, rsi_arr, ema_f, ema_s, ema200, macd_l, macd_sig,
                bb_u, bb_m, bb_l, adx_arr, stoch_k, stoch_d, cci_arr,
                willr_arr, mom_arr, patterns, htf_trend, p
            )
            condition_masks.append(mask)

        # All conditions must be True simultaneously
        if condition_masks:
            combined = np.ones(n, dtype=bool)
            for m in condition_masks:
                combined &= m
        else:
            combined = np.zeros(n, dtype=bool)

        signal = np.zeros(n, dtype=int)
        if direction == "buy":
            signal[combined] = 1
        else:
            signal[combined] = -1

        return signal

    def _evaluate_condition(self, cond: str, c, h, l, rsi_arr, ema_f, ema_s,
                             ema200, macd_l, macd_sig, bb_u, bb_m, bb_l,
                             adx_arr, stoch_k, stoch_d, cci_arr, willr_arr,
                             mom_arr, patterns, htf_trend, p) -> np.ndarray:
        n = len(c)
        bb_width = bb_u - bb_l
        bb_width_mean = np.nanmean(bb_width[~np.isnan(bb_width)]) if np.any(~np.isnan(bb_width)) else 1

        cond_map = {
            "RSI_OVERSOLD":            lambda: (~np.isnan(rsi_arr)) & (rsi_arr < p["rsi_threshold"]),
            "RSI_OVERBOUGHT":          lambda: (~np.isnan(rsi_arr)) & (rsi_arr > (100 - p["rsi_threshold"])),
            "RSI_CROSS_UP":            lambda: crosses_above(rsi_arr, np.full(n, p["rsi_threshold"])),
            "RSI_CROSS_DOWN":          lambda: crosses_below(rsi_arr, np.full(n, 100 - p["rsi_threshold"])),
            "EMA_CROSS_UP":            lambda: crosses_above(ema_f, ema_s),
            "EMA_CROSS_DOWN":          lambda: crosses_below(ema_f, ema_s),
            "MACD_CROSS_UP":           lambda: crosses_above(macd_l, macd_sig),
            "MACD_CROSS_DOWN":         lambda: crosses_below(macd_l, macd_sig),
            "BB_BELOW_LOWER":          lambda: (~np.isnan(bb_l)) & (c < bb_l),
            "BB_ABOVE_UPPER":          lambda: (~np.isnan(bb_u)) & (c > bb_u),
            "BB_SQUEEZE":              lambda: (~np.isnan(bb_width)) & (bb_width < bb_width_mean * 0.7),
            "ADX_STRONG":              lambda: (~np.isnan(adx_arr)) & (adx_arr > p["adx_threshold"]),
            "STOCH_OVERSOLD":          lambda: (~np.isnan(stoch_k)) & (stoch_k < p["stoch_threshold"]),
            "STOCH_OVERBOUGHT":        lambda: (~np.isnan(stoch_k)) & (stoch_k > (100 - p["stoch_threshold"])),
            "STOCH_CROSS_UP":          lambda: crosses_above(stoch_k, stoch_d),
            "STOCH_CROSS_DOWN":        lambda: crosses_below(stoch_k, stoch_d),
            "CCI_OVERSOLD":            lambda: (~np.isnan(cci_arr)) & (cci_arr < -p["cci_threshold"]),
            "CCI_OVERBOUGHT":          lambda: (~np.isnan(cci_arr)) & (cci_arr > p["cci_threshold"]),
            "WILLIAMS_R_OVERSOLD":     lambda: (~np.isnan(willr_arr)) & (willr_arr < -100 + p["willr_threshold"]),
            "WILLIAMS_R_OVERBOUGHT":   lambda: (~np.isnan(willr_arr)) & (willr_arr > -p["willr_threshold"]),
            "MOMENTUM_POSITIVE":       lambda: (~np.isnan(mom_arr)) & (mom_arr > 0),
            "MOMENTUM_NEGATIVE":       lambda: (~np.isnan(mom_arr)) & (mom_arr < 0),
            "PATTERN_ENGULFING_BULL":  lambda: patterns["engulfing"] == 1,
            "PATTERN_ENGULFING_BEAR":  lambda: patterns["engulfing"] == -1,
            "PATTERN_HAMMER":          lambda: patterns["hammer"].astype(bool),
            "PATTERN_SHOOTING_STAR":   lambda: patterns["shooting_star"].astype(bool),
            "PATTERN_INSIDE_BAR":      lambda: patterns["inside_bar"].astype(bool),
            "TREND_UPTREND":           lambda: patterns["hh_hl"].astype(bool),
            "TREND_DOWNTREND":         lambda: patterns["lh_ll"].astype(bool),
            "PRICE_ABOVE_EMA200":      lambda: (~np.isnan(ema200)) & (c > ema200),
            "PRICE_BELOW_EMA200":      lambda: (~np.isnan(ema200)) & (c < ema200),
        }

        fn = cond_map.get(cond)
        if fn is None:
            return np.zeros(n, dtype=bool)
        try:
            return fn().astype(bool)
        except Exception:
            return np.zeros(n, dtype=bool)

    def _compute_htf_trend(self, df_htf: pd.DataFrame,
                            entry_index: pd.DatetimeIndex) -> np.ndarray:
        """Map HTF trend (1=up, -1=down, 0=neutral) to entry timeframe bars."""
        n = len(entry_index)
        trend = np.zeros(n, dtype=int)

        if df_htf is None or len(df_htf) == 0:
            return trend

        htf_c = df_htf["close"].values
        htf_ema50 = ema(htf_c, min(50, len(htf_c) // 2))
        htf_trend_arr = np.zeros(len(htf_c), dtype=int)
        valid = ~np.isnan(htf_ema50)
        htf_trend_arr[valid] = np.where(htf_c[valid] > htf_ema50[valid], 1, -1)

        # Reindex to entry TF using forward-fill
        htf_series = pd.Series(htf_trend_arr, index=df_htf.index)
        entry_series = htf_series.reindex(entry_index, method="ffill").fillna(0)
        return entry_series.values.astype(int)

    def describe_formula(self, formula: Dict) -> str:
        p = formula["params"]
        conds_str = " + ".join(formula["conditions"])
        return (f"[{formula['direction'].upper()}] {conds_str} | "
                f"RSI({p['rsi_period']}) EMA({p['ema_fast']}/{p['ema_slow']}) "
                f"SL={p['sl_atr_mult']}×ATR")
