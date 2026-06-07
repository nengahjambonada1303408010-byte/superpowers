"""
Mathematical probability engine.
Computes conditional probabilities, Markov transition matrices,
and Bayesian updates from price data.
"""
import numpy as np
import pandas as pd
from typing import List, Optional


class ProbabilityEngine:
    def __init__(self, lookahead: int = 1, rr: float = 2.0):
        self.lookahead = lookahead
        self.rr = rr

    def compute_conditional_prob(self, close: np.ndarray, condition_mask: np.ndarray,
                                  lookahead: int = None) -> float:
        """
        P(price rises | condition is True)
        Measures how often price goes up `lookahead` bars after the condition fires.
        """
        la = lookahead or self.lookahead
        if len(close) < la + 1:
            return 0.5

        # For each bar where condition is True, check if price goes up la bars later
        n = len(close)
        condition_mask = condition_mask.astype(bool)

        wins = 0
        total = 0
        for i in range(n - la):
            if condition_mask[i] and not np.isnan(close[i]) and not np.isnan(close[i + la]):
                total += 1
                if close[i + la] > close[i]:
                    wins += 1

        return wins / total if total > 0 else 0.5

    def compute_joint_probability(self, close: np.ndarray,
                                   conditions: List[np.ndarray],
                                   lookahead: int = None) -> float:
        """
        P(price rises | all conditions are True simultaneously)
        """
        if not conditions:
            return 0.5

        joint_mask = np.ones(len(close), dtype=bool)
        for cond in conditions:
            joint_mask &= cond.astype(bool)

        return self.compute_conditional_prob(close, joint_mask, lookahead)

    def compute_directional_prob(self, close: np.ndarray, high: np.ndarray,
                                  low: np.ndarray, condition_mask: np.ndarray,
                                  sl_pct: float, tp_pct: float) -> float:
        """
        P(TP hit before SL) given a long entry when condition fires.
        More realistic than simple close comparison.
        """
        n = len(close)
        condition_mask = condition_mask.astype(bool)
        wins = 0
        total = 0

        for i in range(n - 1):
            if not condition_mask[i]:
                continue
            entry = close[i]
            sl_price = entry * (1 - sl_pct)
            tp_price = entry * (1 + tp_pct)

            for j in range(i + 1, min(i + 200, n)):
                if low[j] <= sl_price:
                    total += 1
                    break
                if high[j] >= tp_price:
                    wins += 1
                    total += 1
                    break
            else:
                pass  # trade still open - don't count

        return wins / total if total > 0 else 0.0

    def markov_transition_matrix(self, close: np.ndarray,
                                  n_states: int = 3) -> np.ndarray:
        """
        Compute n_states x n_states Markov transition matrix.
        States are defined by percentile buckets of returns.
        """
        returns = np.diff(close) / close[:-1]
        returns = returns[~np.isnan(returns)]

        if len(returns) < n_states * 2:
            return np.full((n_states, n_states), 1.0 / n_states)

        # Assign states based on quantile buckets
        percentiles = np.linspace(0, 100, n_states + 1)
        thresholds = np.percentile(returns, percentiles[1:-1])

        def assign_state(r):
            for s, t in enumerate(thresholds):
                if r < t:
                    return s
            return n_states - 1

        states = np.array([assign_state(r) for r in returns])

        matrix = np.zeros((n_states, n_states))
        for i in range(len(states) - 1):
            matrix[states[i], states[i + 1]] += 1

        row_sums = matrix.sum(axis=1, keepdims=True)
        row_sums = np.where(row_sums == 0, 1, row_sums)
        return matrix / row_sums

    def bayesian_update(self, prior: float, likelihood_win: float,
                         likelihood_loss: float, observed_win: bool) -> float:
        """
        P(strategy works | observation) using Bayes theorem.
        prior: initial belief P(strategy works)
        likelihood_win: P(win | strategy works)
        likelihood_loss: P(win | strategy fails)
        observed_win: whether the last trade was a win
        """
        if observed_win:
            numerator = likelihood_win * prior
            denominator = likelihood_win * prior + likelihood_loss * (1 - prior)
        else:
            numerator = (1 - likelihood_win) * prior
            denominator = (1 - likelihood_win) * prior + (1 - likelihood_loss) * (1 - prior)

        return numerator / denominator if denominator > 0 else prior

    def expected_value(self, winrate: float, rr: float = None) -> float:
        """
        Expected value in R multiples.
        EV = winrate * rr - (1 - winrate) * 1
        EV > 0 is required for profitable strategy.
        """
        rr = rr or self.rr
        return winrate * rr - (1 - winrate) * 1.0

    def breakeven_winrate(self, rr: float = None) -> float:
        """Minimum winrate needed to break even given RR ratio."""
        rr = rr or self.rr
        return 1.0 / (1.0 + rr)

    def zscore_significance(self, winrate: float, n_trades: int,
                             expected_wr: float = 0.5) -> float:
        """
        Z-score to test if observed winrate is statistically significant.
        H0: true winrate = expected_wr (random)
        Returns z-score; |z| > 1.96 means significant at 95% CI.
        """
        if n_trades == 0:
            return 0.0
        std = np.sqrt(expected_wr * (1 - expected_wr) / n_trades)
        if std == 0:
            return 0.0
        return (winrate - expected_wr) / std

    def kelly_criterion(self, winrate: float, rr: float = None) -> float:
        """
        Kelly fraction: optimal bet size as fraction of capital.
        f = (winrate * rr - (1 - winrate)) / rr
        """
        rr = rr or self.rr
        return max(0.0, (winrate * rr - (1 - winrate)) / rr)
