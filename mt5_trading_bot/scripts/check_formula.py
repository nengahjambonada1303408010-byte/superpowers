"""
Check saved formulas and run out-of-sample validation.

Usage:
    cd mt5_trading_bot
    python scripts/check_formula.py --symbol XAUUSD
    python scripts/check_formula.py --list
"""
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from loguru import logger
from utils.logger import setup_logger
from core.mt5_connector import MT5Connector
from core.data_manager import DataManager
from core.formula_engine import FormulaEngine
from core.backtest_engine import BacktestEngine
from core.training_manager import TrainingManager, REGISTRY_FILE


def list_formulas():
    if not REGISTRY_FILE.exists():
        print("No formulas saved yet. Run training first.")
        return

    with open(REGISTRY_FILE) as f:
        registry = json.load(f)

    if not registry:
        print("Registry is empty.")
        return

    print(f"\n{'Symbol':<10} {'Val WR':>8} {'Test WR':>8} {'PF':>6} {'Trades':>7} {'Status':>10}  Date")
    print("-" * 70)
    for e in sorted(registry, key=lambda x: x["metrics"].get("val_winrate", 0), reverse=True):
        m = e["metrics"]
        vwr = m.get("val_winrate", 0)
        twr = m.get("test_winrate", 0)
        pf = m.get("val_profit_factor", 0)
        trades = m.get("val_trades", 0)
        status = "✓ VALID" if m.get("is_valid") else "✗"
        date = e["timestamp"][:8]
        print(f"{e['symbol']:<10} {vwr:>7.1%} {twr:>8.1%} {pf:>6.2f} {trades:>7} {status:>10}  {date}")


def validate_formula(symbol: str, config: dict):
    """Re-run validation on the best saved formula."""
    connector = MT5Connector(config)
    connector.initialize()

    dm = DataManager(connector)
    fe = FormulaEngine()
    be = BacktestEngine(rr_ratio=config.get("risk", {}).get("rr_ratio", 2.0))
    tm = TrainingManager(config, connector)

    formula = tm.load_best_formula(symbol)
    if formula is None:
        print(f"No formula found for {symbol}")
        return

    print(f"\nValidating formula for {symbol}...")
    print(f"Formula: {fe.describe_formula(formula)}")

    tf_entry = config.get("training", {}).get("timeframe_entry", "M15")
    tf_htf = config.get("training", {}).get("timeframe_htf", "H1")

    df = dm.fetch_and_cache(symbol, tf_entry, years=1)
    df_htf = dm.fetch_and_cache(symbol, tf_htf, years=1)

    if df is None:
        print("Failed to fetch data")
        return

    result = be.run(df, df_htf, formula, fe)

    print(f"\n=== Recent 1-Year Validation ===")
    print(f"  Winrate:       {result.winrate:.1%}")
    print(f"  Profit Factor: {result.profit_factor:.2f}")
    print(f"  Total Trades:  {result.total_trades}")
    print(f"  Max Drawdown:  {result.max_drawdown:.1%}")
    print(f"  Sharpe Ratio:  {result.sharpe_ratio:.2f}")
    print(f"  Net P&L (R):   {result.net_pnl_r:+.1f}")
    print()
    valid = result.is_valid(0.75, 20)
    print(f"  STATUS: {'✓ STILL VALID' if valid else '✗ BELOW THRESHOLD - RETRAIN RECOMMENDED'}")

    if not valid:
        print(f"  Recommendation: run 'python scripts/run_training.py --symbol {symbol}'")

    connector.shutdown()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default=None)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    config = {}
    if Path(args.config).exists():
        with open(args.config) as f:
            config = yaml.safe_load(f) or {}

    if args.list or args.symbol is None:
        list_formulas()
    if args.symbol:
        validate_formula(args.symbol, config)


if __name__ == "__main__":
    main()
