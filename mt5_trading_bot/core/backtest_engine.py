"""
Backtest Engine - simulates trades on historical data.
Supports walk-forward validation to prevent overfitting.
Fixed 1:2 Risk-Reward ratio throughout.
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

from core.formula_engine import FormulaEngine
from core.indicators import atr
from utils.metrics import compute_all_metrics


@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: Optional[pd.Timestamp]
    direction: str           # "buy" or "sell"
    entry_price: float
    sl_price: float
    tp_price: float
    exit_price: float
    result: str              # "win", "loss", "open"
    pnl_r: float             # profit in R multiples (+2.0 win, -1.0 loss)
    duration_bars: int


@dataclass
class BacktestResult:
    winrate: float
    profit_factor: float
    total_trades: int
    max_drawdown: float
    sharpe_ratio: float
    avg_trade_duration: float
    net_pnl_r: float
    equity_curve: np.ndarray = field(default_factory=lambda: np.array([]))
    trades: List[Trade] = field(default_factory=list)

    def is_valid(self, min_winrate: float = 0.75, min_trades: int = 100) -> bool:
        return (self.winrate >= min_winrate and
                self.total_trades >= min_trades and
                self.profit_factor >= 2.0)

    def fitness_score(self) -> float:
        if self.total_trades < 10:
            return 0.0
        trade_weight = min(1.0, self.total_trades / 100)
        return self.winrate * self.profit_factor * trade_weight


class BacktestEngine:
    def __init__(self, rr_ratio: float = 2.0):
        self.rr_ratio = rr_ratio
        self._formula_engine = None

    def run(self, df_entry: pd.DataFrame, df_htf: pd.DataFrame,
            formula: Dict, formula_engine: FormulaEngine) -> BacktestResult:
        """Run backtest of a single formula on full dataset."""
        signals = formula_engine.compute_signals(df_entry, df_htf, formula)
        trades = self._simulate_trades(df_entry, signals, formula)
        return self._build_result(trades)

    def walk_forward_test(self, df_entry: pd.DataFrame, df_htf: pd.DataFrame,
                           formula: Dict, formula_engine: FormulaEngine,
                           n_folds: int = 5) -> List[BacktestResult]:
        """
        Walk-forward validation: split data into n_folds windows,
        test each window sequentially. Reduces overfitting.
        """
        n = len(df_entry)
        fold_size = n // n_folds
        results = []

        for i in range(n_folds):
            start = i * fold_size
            end = start + fold_size if i < n_folds - 1 else n
            fold_df = df_entry.iloc[start:end].copy()

            # Get matching HTF data
            if df_htf is not None and len(df_htf) > 0:
                fold_htf = df_htf[
                    (df_htf.index >= fold_df.index[0]) &
                    (df_htf.index <= fold_df.index[-1])
                ].copy()
            else:
                fold_htf = df_htf

            result = self.run(fold_df, fold_htf, formula, formula_engine)
            results.append(result)

        return results

    def aggregate_walk_forward(self, results: List[BacktestResult]) -> BacktestResult:
        """Aggregate walk-forward fold results into one summary."""
        all_trades = []
        for r in results:
            all_trades.extend(r.trades)
        return self._build_result(all_trades)

    def _simulate_trades(self, df: pd.DataFrame, signals: np.ndarray,
                          formula: Dict) -> List[Trade]:
        """
        Simulate trade execution bar-by-bar with fixed RR.
        SL = ATR * sl_multiplier
        TP = SL * rr_ratio (always 2.0)
        """
        p = formula["params"]
        rr = self.rr_ratio

        h = df["high"].values
        l = df["low"].values
        c = df["close"].values
        n = len(c)

        atr_arr = atr(h, l, c, p["atr_period"])

        trades = []
        in_trade = False
        trade_entry_i = -1
        trade_dir = None
        trade_entry = 0.0
        trade_sl = 0.0
        trade_tp = 0.0

        for i in range(n):
            if in_trade:
                if trade_dir == "buy":
                    if l[i] <= trade_sl:
                        # SL hit
                        trades.append(Trade(
                            entry_time=df.index[trade_entry_i],
                            exit_time=df.index[i],
                            direction="buy",
                            entry_price=trade_entry,
                            sl_price=trade_sl,
                            tp_price=trade_tp,
                            exit_price=trade_sl,
                            result="loss",
                            pnl_r=-1.0,
                            duration_bars=i - trade_entry_i,
                        ))
                        in_trade = False
                    elif h[i] >= trade_tp:
                        # TP hit
                        trades.append(Trade(
                            entry_time=df.index[trade_entry_i],
                            exit_time=df.index[i],
                            direction="buy",
                            entry_price=trade_entry,
                            sl_price=trade_sl,
                            tp_price=trade_tp,
                            exit_price=trade_tp,
                            result="win",
                            pnl_r=rr,
                            duration_bars=i - trade_entry_i,
                        ))
                        in_trade = False
                else:  # sell
                    if h[i] >= trade_sl:
                        trades.append(Trade(
                            entry_time=df.index[trade_entry_i],
                            exit_time=df.index[i],
                            direction="sell",
                            entry_price=trade_entry,
                            sl_price=trade_sl,
                            tp_price=trade_tp,
                            exit_price=trade_sl,
                            result="loss",
                            pnl_r=-1.0,
                            duration_bars=i - trade_entry_i,
                        ))
                        in_trade = False
                    elif l[i] <= trade_tp:
                        trades.append(Trade(
                            entry_time=df.index[trade_entry_i],
                            exit_time=df.index[i],
                            direction="sell",
                            entry_price=trade_entry,
                            sl_price=trade_sl,
                            tp_price=trade_tp,
                            exit_price=trade_tp,
                            result="win",
                            pnl_r=rr,
                            duration_bars=i - trade_entry_i,
                        ))
                        in_trade = False

            if not in_trade and signals[i] != 0 and not np.isnan(atr_arr[i]) and atr_arr[i] > 0:
                sl_dist = atr_arr[i] * p["sl_atr_mult"]

                if signals[i] == 1:  # buy
                    sl_price = c[i] - sl_dist
                    tp_price = c[i] + sl_dist * rr
                    trade_dir = "buy"
                else:  # sell
                    sl_price = c[i] + sl_dist
                    tp_price = c[i] - sl_dist * rr
                    trade_dir = "sell"

                in_trade = True
                trade_entry_i = i
                trade_entry = c[i]
                trade_sl = sl_price
                trade_tp = tp_price

        return trades

    def _build_result(self, trades: List[Trade]) -> BacktestResult:
        if not trades:
            return BacktestResult(
                winrate=0.0, profit_factor=0.0, total_trades=0,
                max_drawdown=0.0, sharpe_ratio=0.0,
                avg_trade_duration=0.0, net_pnl_r=0.0,
                equity_curve=np.array([1.0]), trades=[],
            )

        trade_dicts = [
            {"result": t.result, "pnl_r": t.pnl_r, "duration_bars": t.duration_bars}
            for t in trades
        ]
        metrics = compute_all_metrics(trade_dicts)

        return BacktestResult(
            winrate=metrics["winrate"],
            profit_factor=metrics["profit_factor"],
            total_trades=metrics["total_trades"],
            max_drawdown=metrics["max_drawdown"],
            sharpe_ratio=metrics["sharpe_ratio"],
            avg_trade_duration=metrics["avg_trade_duration"],
            net_pnl_r=metrics["net_pnl_r"],
            equity_curve=self._build_equity_curve(trades),
            trades=trades,
        )

    @staticmethod
    def _build_equity_curve(trades: List[Trade]) -> np.ndarray:
        equity = [1.0]
        for t in trades:
            equity.append(equity[-1] + t.pnl_r * 0.01)  # 1% per R
        return np.array(equity)
