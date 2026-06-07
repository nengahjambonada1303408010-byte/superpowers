"""
Training Manager - orchestrates the full training pipeline.
Fetches data, runs evolution, validates formulas, and saves results.
"""
import json
import pickle
import os
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Callable

import numpy as np
import pandas as pd
from loguru import logger

from core.mt5_connector import MT5Connector
from core.data_manager import DataManager
from core.formula_engine import FormulaEngine
from core.backtest_engine import BacktestEngine
from core.evolution_engine import EvolutionEngine


FORMULA_DIR = Path("data/formulas")
REGISTRY_FILE = FORMULA_DIR / "registry.json"


class TrainingManager:
    def __init__(self, config: dict, connector: MT5Connector):
        self.config = config
        self.connector = connector
        self.train_cfg = config.get("training", {})
        self.data_manager = DataManager(connector)
        self.formula_engine = FormulaEngine(config)
        self.backtest_engine = BacktestEngine(rr_ratio=config.get("risk", {}).get("rr_ratio", 2.0))
        self.evolution_engine = EvolutionEngine(self.train_cfg)
        FORMULA_DIR.mkdir(parents=True, exist_ok=True)
        self._stop_flag = threading.Event()
        self._running = False

    def stop(self):
        """Signal training to stop after current generation."""
        self._stop_flag.set()
        logger.info("Stop signal sent to training manager")

    def is_running(self) -> bool:
        return self._running

    def run_training(self, symbol: str, callback: Callable = None,
                     checkpoint_callback: Callable = None) -> Optional[Dict]:
        """
        Full training pipeline for a single symbol.
        Returns the best formula dict or None if no valid formula found.
        """
        self._stop_flag.clear()
        self._running = True
        logger.info(f"=== Starting training for {symbol} ===")

        try:
            years = self.train_cfg.get("years_of_data", 5)
            tf_entry = self.train_cfg.get("timeframe_entry", "M15")
            tf_htf = self.train_cfg.get("timeframe_htf", "H1")
            split = self.train_cfg.get("data_split", {"train": 0.70, "validation": 0.15, "test": 0.15})

            # Fetch data
            logger.info(f"Fetching {years} years of {symbol} data...")
            df_entry = self.data_manager.fetch_and_cache(symbol, tf_entry, years)
            df_htf = self.data_manager.fetch_and_cache(symbol, tf_htf, years)

            if df_entry is None or len(df_entry) < 200:
                logger.error(f"Insufficient data for {symbol}")
                return None

            # Align HTF data
            df_entry = self.data_manager.compute_features(df_entry)

            # Split chronologically
            n = len(df_entry)
            train_end = int(n * split["train"])
            val_end = int(n * (split["train"] + split["validation"]))

            df_train = df_entry.iloc[:train_end].copy()
            df_val = df_entry.iloc[train_end:val_end].copy()
            df_test = df_entry.iloc[val_end:].copy()

            if df_htf is not None:
                htf_train = df_htf[df_htf.index <= df_train.index[-1]].copy()
                htf_val = df_htf[(df_htf.index >= df_val.index[0]) & (df_htf.index <= df_val.index[-1])].copy()
                htf_test = df_htf[df_htf.index >= df_test.index[0]].copy()
            else:
                htf_train = htf_val = htf_test = None

            logger.info(f"Data split: train={len(df_train)}, val={len(df_val)}, test={len(df_test)} bars")

            # Wrap callback to check stop flag
            def evolution_callback(gen, best_wr, best_formula, max_gen):
                if self._stop_flag.is_set():
                    raise InterruptedError("Training stopped by user")
                if callback:
                    callback(gen, best_wr, best_formula, max_gen)

            # Run evolution on training data
            logger.info("Running genetic evolution on training data...")
            try:
                result = self.evolution_engine.evolve(
                    df_entry=df_train,
                    df_htf=htf_train,
                    formula_engine=self.formula_engine,
                    backtest_engine=self.backtest_engine,
                    callback=evolution_callback,
                    checkpoint_callback=checkpoint_callback,
                )
            except InterruptedError:
                logger.info("Training interrupted by user")
                return None

            if result["best_formula"] is None:
                logger.warning("No valid formula found during evolution")
                return None

            best = result["best_formula"]
            logger.info(f"Best formula from evolution: {self.formula_engine.describe_formula(best)}")

            # Validate on out-of-sample validation set
            logger.info("Validating on out-of-sample validation set...")
            val_result = self.backtest_engine.run(df_val, htf_val, best, self.formula_engine)
            logger.info(f"Validation: winrate={val_result.winrate:.1%}, "
                        f"trades={val_result.total_trades}, PF={val_result.profit_factor:.2f}")

            # Final test on held-out test set
            logger.info("Testing on held-out test set...")
            test_result = self.backtest_engine.run(df_test, htf_test, best, self.formula_engine)
            logger.info(f"Test: winrate={test_result.winrate:.1%}, "
                        f"trades={test_result.total_trades}, PF={test_result.profit_factor:.2f}")

            metrics = {
                "symbol": symbol,
                "train_winrate": result["best_metrics"]["winrate"] if result["best_metrics"] else 0,
                "val_winrate": val_result.winrate,
                "test_winrate": test_result.winrate,
                "val_profit_factor": val_result.profit_factor,
                "test_profit_factor": test_result.profit_factor,
                "val_trades": val_result.total_trades,
                "test_trades": test_result.total_trades,
                "val_max_drawdown": val_result.max_drawdown,
                "generations": len(result["history"]),
                "trained_at": datetime.now(timezone.utc).isoformat(),
                "timeframe_entry": tf_entry,
                "timeframe_htf": tf_htf,
                "is_valid": val_result.is_valid(
                    self.train_cfg.get("target_winrate", 0.75),
                    self.train_cfg.get("min_trades", 30),
                )
            }

            self.save_formula(symbol, best, metrics)
            return best

        finally:
            self._running = False

    def save_formula(self, symbol: str, formula: Dict, metrics: Dict):
        """Save best formula to disk with metadata."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        pkl_path = FORMULA_DIR / f"{symbol}_{ts}.pkl"
        json_path = FORMULA_DIR / f"{symbol}_{ts}.json"

        # Atomic write for pkl
        with open(pkl_path, "wb") as f:
            pickle.dump({"formula": formula, "metrics": metrics}, f)

        entry = {
            "symbol": symbol,
            "timestamp": ts,
            "pkl_path": str(pkl_path),
            "formula": formula,
            "metrics": metrics,
        }

        # Save human-readable JSON
        with open(json_path, "w") as f:
            json.dump(entry, f, indent=2, default=str)

        # Update registry
        self._update_registry(entry)
        logger.info(f"Formula saved: {pkl_path}")

    def load_best_formula(self, symbol: str) -> Optional[Dict]:
        """Load the best valid formula for a symbol from registry."""
        registry = self._load_registry()
        entries = [e for e in registry if e["symbol"] == symbol]

        if not entries:
            logger.warning(f"No formula found for {symbol}")
            return None

        # Sort by validation winrate, prefer valid ones
        entries.sort(
            key=lambda e: (
                e["metrics"].get("is_valid", False),
                e["metrics"].get("val_winrate", 0),
            ),
            reverse=True,
        )

        best_entry = entries[0]
        pkl_path = Path(best_entry["pkl_path"])

        if pkl_path.exists():
            try:
                with open(pkl_path, "rb") as f:
                    data = pickle.load(f)
                logger.info(f"Loaded formula for {symbol}: "
                            f"val_wr={best_entry['metrics'].get('val_winrate', 0):.1%}")
                return data["formula"]
            except Exception as e:
                logger.error(f"Failed to load formula: {e}")

        # Fallback: use the formula dict directly from registry
        return best_entry.get("formula")

    def list_formulas(self) -> List[Dict]:
        """Return all formula entries from registry."""
        return self._load_registry()

    def run_continuous_training(self, symbols: List[str],
                                 interval_days: int = 7,
                                 callback: Callable = None):
        """Run training in a loop, retraining every interval_days."""
        logger.info(f"Starting continuous training: symbols={symbols}, interval={interval_days}d")
        while not self._stop_flag.is_set():
            for symbol in symbols:
                if self._stop_flag.is_set():
                    break
                self.run_training(symbol, callback=callback)

            if not self._stop_flag.is_set():
                sleep_secs = interval_days * 24 * 3600
                logger.info(f"Next training in {interval_days} days")
                self._stop_flag.wait(sleep_secs)

    def _update_registry(self, entry: Dict):
        registry = self._load_registry()
        registry.append({
            "symbol": entry["symbol"],
            "timestamp": entry["timestamp"],
            "pkl_path": entry["pkl_path"],
            "metrics": entry["metrics"],
            "formula": entry["formula"],
        })

        tmp = REGISTRY_FILE.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(registry, f, indent=2, default=str)
        os.replace(tmp, REGISTRY_FILE)

    def _load_registry(self) -> List[Dict]:
        if not REGISTRY_FILE.exists():
            return []
        try:
            with open(REGISTRY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
