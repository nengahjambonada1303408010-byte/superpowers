"""
Tests for backtest engine - uses synthetic data, no MT5 needed.
"""
import numpy as np
import pandas as pd
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.formula_engine import FormulaEngine
from core.backtest_engine import BacktestEngine


@pytest.fixture
def synthetic_df():
    """5 years of synthetic H1 data."""
    np.random.seed(123)
    n = 3000
    close = 1.1 + np.cumsum(np.random.randn(n) * 0.001)
    close = np.abs(close) + 0.8
    high = close + np.abs(np.random.randn(n) * 0.0005)
    low = close - np.abs(np.random.randn(n) * 0.0005)
    open_ = close + np.random.randn(n) * 0.0002
    volume = np.random.randint(100, 10000, n).astype(float)
    idx = pd.date_range("2019-01-01", periods=n, freq="h", tz="UTC")
    return pd.DataFrame({
        "open": open_, "high": high, "low": low,
        "close": close, "volume": volume
    }, index=idx)


def test_backtest_returns_result(synthetic_df):
    fe = FormulaEngine()
    be = BacktestEngine(rr_ratio=2.0)
    formula = fe.random_formula()
    result = be.run(synthetic_df, None, formula, fe)
    assert result is not None
    assert 0.0 <= result.winrate <= 1.0
    assert result.total_trades >= 0


def test_backtest_rr_ratio(synthetic_df):
    """Verify all trades have exactly 2.0 R win or -1.0 R loss."""
    fe = FormulaEngine()
    be = BacktestEngine(rr_ratio=2.0)
    formula = fe.random_formula()
    result = be.run(synthetic_df, None, formula, fe)
    for trade in result.trades:
        assert trade.pnl_r in (2.0, -1.0), f"Unexpected pnl_r: {trade.pnl_r}"


def test_fitness_score_range(synthetic_df):
    fe = FormulaEngine()
    be = BacktestEngine(rr_ratio=2.0)
    for _ in range(5):
        formula = fe.random_formula()
        result = be.run(synthetic_df, None, formula, fe)
        score = result.fitness_score()
        assert score >= 0.0


def test_walk_forward_returns_n_folds(synthetic_df):
    fe = FormulaEngine()
    be = BacktestEngine(rr_ratio=2.0)
    formula = fe.random_formula()
    results = be.walk_forward_test(synthetic_df, None, formula, fe, n_folds=5)
    assert len(results) == 5


def test_backtest_result_is_valid_criteria(synthetic_df):
    """A formula with 0 trades should not be valid."""
    fe = FormulaEngine()
    be = BacktestEngine(rr_ratio=2.0)
    formula = fe.random_formula()
    formula["conditions"] = []  # force no signals
    result = be.run(synthetic_df, None, formula, fe)
    assert result.total_trades == 0
    assert not result.is_valid()


def test_formula_roundtrip():
    """Formula encode/decode should preserve structure."""
    fe = FormulaEngine()
    original = fe.random_formula()
    vec = fe.formula_to_vector(original)
    decoded = fe.vector_to_formula(vec)
    assert decoded["direction"] == original["direction"]
    assert len(decoded["conditions"]) > 0
    assert "rsi_period" in decoded["params"]


def test_population_generation():
    fe = FormulaEngine()
    pop = fe.generate_population(50)
    assert len(pop) == 50
    for f in pop:
        assert "direction" in f
        assert "conditions" in f
        assert "params" in f
        assert isinstance(f["params"]["rsi_period"], int)
