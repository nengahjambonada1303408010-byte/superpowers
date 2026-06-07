"""
Tests for probability engine.
"""
import numpy as np
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.probability import ProbabilityEngine


@pytest.fixture
def pe():
    return ProbabilityEngine(lookahead=1, rr=2.0)


@pytest.fixture
def trending_up():
    np.random.seed(1)
    return np.cumsum(np.abs(np.random.randn(300)) * 0.1) + 1.0


@pytest.fixture
def random_walk():
    np.random.seed(99)
    return 1.0 + np.cumsum(np.random.randn(300) * 0.01)


def test_conditional_prob_range(pe, random_walk):
    mask = np.ones(len(random_walk), dtype=bool)
    p = pe.compute_conditional_prob(random_walk, mask)
    assert 0.0 <= p <= 1.0


def test_uptrend_prob_high(pe, trending_up):
    """For a pure uptrend, P(up) should be > 0.5."""
    mask = np.ones(len(trending_up), dtype=bool)
    p = pe.compute_conditional_prob(trending_up, mask)
    assert p > 0.5, f"Expected p > 0.5 for uptrend, got {p}"


def test_joint_probability_range(pe, random_walk):
    mask1 = random_walk > np.median(random_walk)
    mask2 = np.roll(mask1, 1)
    p = pe.compute_joint_probability(random_walk, [mask1, mask2])
    assert 0.0 <= p <= 1.0


def test_markov_matrix_rows_sum_one(pe, random_walk):
    matrix = pe.markov_transition_matrix(random_walk, n_states=3)
    row_sums = matrix.sum(axis=1)
    assert np.allclose(row_sums, 1.0, atol=1e-9)


def test_expected_value(pe):
    ev = pe.expected_value(0.75, rr=2.0)
    assert ev == pytest.approx(0.75 * 2.0 - 0.25 * 1.0)
    assert ev > 0


def test_expected_value_breakeven(pe):
    wr_be = pe.breakeven_winrate(rr=2.0)
    ev_at_breakeven = pe.expected_value(wr_be, rr=2.0)
    assert abs(ev_at_breakeven) < 1e-9


def test_kelly_criterion_positive(pe):
    k = pe.kelly_criterion(0.75, rr=2.0)
    assert k > 0


def test_kelly_criterion_zero_below_breakeven(pe):
    k = pe.kelly_criterion(0.2, rr=2.0)
    assert k == 0.0


def test_bayesian_update(pe):
    prior = 0.5
    post_win = pe.bayesian_update(prior, 0.75, 0.25, observed_win=True)
    post_loss = pe.bayesian_update(prior, 0.75, 0.25, observed_win=False)
    assert post_win > prior, "Win should increase belief"
    assert post_loss < prior, "Loss should decrease belief"


def test_zscore_significance(pe):
    z = pe.zscore_significance(0.75, n_trades=100)
    assert abs(z) > 1.96, f"WR=75% with 100 trades should be significant, z={z}"
