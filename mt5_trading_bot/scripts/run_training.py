"""
Standalone training script - run without GUI.
Useful for overnight training on a server.

Usage:
    cd mt5_trading_bot
    python scripts/run_training.py --symbol XAUUSD
    python scripts/run_training.py --symbol EURUSD --population 50000 --generations 300
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from loguru import logger
from utils.logger import setup_logger
from core.mt5_connector import MT5Connector
from core.training_manager import TrainingManager


def main():
    parser = argparse.ArgumentParser(description="MT5 Bot Standalone Training")
    parser.add_argument("--symbol", required=True, help="Symbol to train, e.g. XAUUSD")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--population", type=int, default=None)
    parser.add_argument("--generations", type=int, default=None)
    parser.add_argument("--years", type=int, default=None)
    parser.add_argument("--continuous", action="store_true",
                        help="Retrain continuously every N days")
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f) or {}

    setup_logger(config)

    if args.population:
        config.setdefault("training", {})["population_size"] = args.population
    if args.generations:
        config.setdefault("training", {})["max_generations"] = args.generations
    if args.years:
        config.setdefault("training", {})["years_of_data"] = args.years

    connector = MT5Connector(config)
    connected = connector.initialize()
    if not connected:
        logger.warning("MT5 not connected - using mock/cached data")

    tm = TrainingManager(config, connector)

    def progress(gen, best_wr, best_formula, max_gen):
        logger.info(f"Gen {gen}/{max_gen} | WR={best_wr:.1%}")

    try:
        if args.continuous:
            interval = config.get("training", {}).get("retrain_interval_days", 7)
            symbols = [args.symbol]
            logger.info(f"Continuous training: {symbols}, retrain every {interval}d")
            tm.run_continuous_training(symbols, interval_days=interval, callback=progress)
        else:
            formula = tm.run_training(args.symbol, callback=progress)
            if formula:
                logger.info(f"Training complete! Formula saved for {args.symbol}")
            else:
                logger.error("No valid formula found")
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
    finally:
        connector.shutdown()


if __name__ == "__main__":
    main()
