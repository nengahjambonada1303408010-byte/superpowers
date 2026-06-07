"""
MT5 Mathematical Trading Bot - Main Entry Point.

Usage:
    python main.py                          # Launch GUI
    python main.py --mode train             # Train with GUI
    python main.py --mode live              # Live trade with GUI
    python main.py --mode backtest          # Show backtest results
"""
import sys
import argparse
from pathlib import Path

import yaml
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger
from core.mt5_connector import MT5Connector
from core.training_manager import TrainingManager
from trading.live_trader import LiveTrader


def load_config(config_path: str = "config.yaml") -> dict:
    p = Path(config_path)
    if not p.exists():
        logger.warning(f"Config not found at {config_path}, using defaults")
        return {}
    with open(p) as f:
        return yaml.safe_load(f) or {}


def launch_gui(config: dict, connector: MT5Connector,
               training_manager: TrainingManager, live_trader: LiveTrader,
               initial_tab: int = 0):
    """Launch the PyQt5 GUI application."""
    from PyQt5.QtWidgets import QApplication
    from gui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("MT5 Trading Bot")

    window = MainWindow(config, connector, training_manager, live_trader)

    if initial_tab > 0:
        window.tabs.setCurrentIndex(initial_tab)

    window.show()
    return app.exec_()


def main():
    parser = argparse.ArgumentParser(description="MT5 Mathematical Trading Bot")
    parser.add_argument("--mode", choices=["train", "live", "backtest", "gui"],
                        default="gui", help="Startup mode")
    parser.add_argument("--symbol", default=None, help="Symbol to train/trade")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    args = parser.parse_args()

    # Load config
    config = load_config(args.config)
    setup_logger(config)

    logger.info("MT5 Mathematical Trading Bot starting...")
    logger.info(f"Mode: {args.mode}")

    # Initialize core components
    connector = MT5Connector(config)
    connected = connector.initialize()
    if not connected:
        logger.warning("MT5 not connected - running in demo/mock mode")

    training_manager = TrainingManager(config, connector)
    live_trader = LiveTrader(config, connector)

    # Tab mapping
    TAB_MAP = {"gui": 0, "train": 0, "live": 1, "backtest": 2}
    initial_tab = TAB_MAP.get(args.mode, 0)

    # Override symbol in config if provided
    if args.symbol:
        config.setdefault("training", {})
        config["training"].setdefault("symbols", [args.symbol])

    try:
        exit_code = launch_gui(config, connector, training_manager, live_trader, initial_tab)
    finally:
        live_trader.stop()
        training_manager.stop()
        connector.shutdown()
        logger.info("Bot shutdown complete")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
