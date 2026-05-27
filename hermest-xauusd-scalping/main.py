#!/usr/bin/env python3
"""
Gold House AI — XAUUSD Scalping Bot
Base: Hermes Agent (NousResearch/hermes-agent) + Kimi AI
"""
import sys
import argparse

from PyQt5.QtWidgets import QApplication

from agent.hermes_agent import HermesTrader
from config.settings import Settings
from connectors.mt5_connector import MT5Connector
from gui.main_window import MainWindow
from risk.risk_manager import RiskManager
from utils.logger import setup_logger


def main():
    setup_logger()

    parser = argparse.ArgumentParser(description="Gold House AI — XAUUSD Scalping Bot")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run with mock MT5 data (no real trading)")
    args = parser.parse_args()

    settings = Settings.from_env()

    if args.dry_run:
        settings.MT5_LOGIN = 0
        settings.MT5_PASSWORD = "demo"
        settings.MT5_SERVER = "Mock-Demo"
        print("DRY RUN MODE — no real MT5 connection, no real trades")

    app = QApplication(sys.argv)
    app.setApplicationName("Gold House AI")

    connector = MT5Connector()
    risk_manager = RiskManager(settings)
    agent = HermesTrader(settings, connector, risk_manager)

    window = MainWindow(settings, connector, agent, risk_manager)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
