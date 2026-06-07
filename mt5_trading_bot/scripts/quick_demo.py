"""
Quick Demo - test the full training pipeline with small dataset.
Runs without MT5 connection using synthetic data.

Usage:
    cd mt5_trading_bot
    python scripts/quick_demo.py
    python scripts/quick_demo.py --population 200 --generations 5
"""
import sys
import time
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.formula_engine import FormulaEngine
from core.backtest_engine import BacktestEngine
from core.evolution_engine import EvolutionEngine
from core.indicator_cache import IndicatorCache
from utils.metrics import expected_value


def make_demo_data(n: int = 3000, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic OHLCV data for testing."""
    np.random.seed(seed)
    close = 1.1 + np.cumsum(np.random.randn(n) * 0.001)
    close = np.abs(close) + 0.8
    high = close + np.abs(np.random.randn(n) * 0.0005)
    low = close - np.abs(np.random.randn(n) * 0.0005)
    open_ = close + np.random.randn(n) * 0.0002
    vol = np.random.randint(100, 10000, n).astype(float)
    idx = pd.date_range("2019-01-01", periods=n, freq="h", tz="UTC")
    return pd.DataFrame({"open": open_, "high": high, "low": low,
                          "close": close, "volume": vol}, index=idx)


def benchmark_cache_speedup(df: pd.DataFrame, n_formulas: int = 50):
    """Compare speed with and without indicator cache."""
    fe = FormulaEngine()
    be = BacktestEngine(rr_ratio=2.0)
    population = fe.generate_population(n_formulas)
    htf_trend = np.zeros(len(df), dtype=int)

    print(f"\n--- Speed Benchmark ({n_formulas} formulas) ---")

    # Without cache
    t0 = time.perf_counter()
    for formula in population[:10]:  # only 10 for non-cached (slow)
        be.run(df, None, formula, fe)
    t_no_cache = (time.perf_counter() - t0) / 10 * n_formulas
    print(f"Without cache (estimated): {t_no_cache:.1f}s for {n_formulas} formulas")

    # With cache
    cache = IndicatorCache(df)
    t1 = time.perf_counter()
    cache.build()
    build_time = time.perf_counter() - t1
    print(f"Cache build time: {build_time:.2f}s")

    t2 = time.perf_counter()
    for formula in population:
        signals = fe.compute_signals_cached(cache, htf_trend, formula)
        be._simulate_trades(df, signals, formula)
    t_cache = time.perf_counter() - t2
    print(f"With cache: {t_cache:.2f}s for {n_formulas} formulas")
    print(f"Speedup: {t_no_cache / (build_time + t_cache):.1f}x")


def run_demo_evolution(df: pd.DataFrame, population: int = 100,
                        generations: int = 5):
    """Run a small evolution cycle and show the best formula found."""
    fe = FormulaEngine()
    be = BacktestEngine(rr_ratio=2.0)
    ee = EvolutionEngine({
        "population_size": population,
        "max_generations": generations,
        "target_winrate": 0.75,
        "min_trades": 10,
        "n_cpu_cores": 1,  # single-threaded for demo stability
    })

    print(f"\n--- Evolution Demo ({population} formulas, {generations} generations) ---")

    def progress(gen, wr, formula, max_gen):
        print(f"  Gen {gen:>3}/{max_gen} | WR={wr:.1%} | {fe.describe_formula(formula)[:70]}")

    t0 = time.perf_counter()
    result = ee.evolve(df, None, fe, be, callback=progress)
    elapsed = time.perf_counter() - t0

    if result["best_formula"]:
        m = result["best_metrics"]
        bf = result["best_formula"]
        ev = expected_value(m["winrate"], rr=2.0)
        print(f"\n=== BEST FORMULA FOUND ===")
        print(f"  Direction: {bf['direction'].upper()}")
        print(f"  Conditions: {', '.join(bf['conditions'])}")
        print(f"  WinRate: {m['winrate']:.1%}")
        print(f"  Profit Factor: {m['profit_factor']:.2f}")
        print(f"  Total Trades: {m['total_trades']}")
        print(f"  Max Drawdown: {m['max_drawdown']:.1%}")
        print(f"  Expected Value: {ev:+.3f} R per trade")
        print(f"  Evolution time: {elapsed:.1f}s")
        print()

        if m["winrate"] >= 0.75 and m["total_trades"] >= 10:
            print("  STATUS: ✓ MEETS TARGET (75% WR)")
        else:
            print(f"  STATUS: ✗ Below target (need {0.75:.0%} WR)")
    else:
        print("No formula found.")

    return result


def show_probability_analysis(df: pd.DataFrame):
    """Show probability analysis on the dataset."""
    from core.probability import ProbabilityEngine
    from core.indicators import rsi, ema

    pe = ProbabilityEngine(rr=2.0)
    c = df["close"].values
    rsi_arr = rsi(c, 14)
    ema50 = ema(c, 50)

    print("\n--- Probability Analysis ---")

    # P(up next bar | RSI < 30)
    mask_oversold = (~np.isnan(rsi_arr)) & (rsi_arr < 30)
    p_oversold = pe.compute_conditional_prob(c, mask_oversold, lookahead=3)
    print(f"  P(up in 3 bars | RSI<30):          {p_oversold:.1%}")

    # P(up next bar | RSI > 70)
    mask_overbought = (~np.isnan(rsi_arr)) & (rsi_arr > 70)
    p_overbought = pe.compute_conditional_prob(c, mask_overbought, lookahead=3)
    print(f"  P(up in 3 bars | RSI>70):          {p_overbought:.1%}")

    # P(up | price above EMA50)
    mask_above_ema = (~np.isnan(ema50)) & (c > ema50)
    p_above_ema = pe.compute_conditional_prob(c, mask_above_ema, lookahead=1)
    print(f"  P(up next bar | price > EMA50):    {p_above_ema:.1%}")

    be_wr = pe.breakeven_winrate(rr=2.0)
    kelly = pe.kelly_criterion(0.75, rr=2.0)
    ev = pe.expected_value(0.75, rr=2.0)
    print(f"\n  Breakeven winrate (RR 1:2):        {be_wr:.1%}")
    print(f"  Kelly fraction (75% WR):           {kelly:.1%}")
    print(f"  Expected Value (75% WR):           {ev:+.3f} R")

    # Markov transition matrix
    matrix = pe.markov_transition_matrix(c, n_states=3)
    print(f"\n  Markov Transition Matrix (3 states: down/neutral/up):")
    for row in matrix:
        print(f"    {[f'{v:.2f}' for v in row]}")


def main():
    parser = argparse.ArgumentParser(description="MT5 Bot Quick Demo")
    parser.add_argument("--population", type=int, default=100)
    parser.add_argument("--generations", type=int, default=5)
    parser.add_argument("--bars", type=int, default=3000)
    parser.add_argument("--no-benchmark", action="store_true")
    args = parser.parse_args()

    print("MT5 Mathematical Trading Bot - Quick Demo")
    print("=" * 50)
    print(f"Dataset: {args.bars} synthetic bars")

    df = make_demo_data(n=args.bars)
    print(f"Date range: {df.index[0].date()} → {df.index[-1].date()}")

    show_probability_analysis(df)

    if not args.no_benchmark:
        benchmark_cache_speedup(df, n_formulas=args.population)

    run_demo_evolution(df, population=args.population, generations=args.generations)


if __name__ == "__main__":
    main()
