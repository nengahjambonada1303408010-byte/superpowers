from __future__ import annotations

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QSplitter, QLabel, QMessageBox)
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QFont

from core.bot import ScalpingBot
from gui.widgets.account_panel import AccountPanel
from gui.widgets.agent_log_panel import AgentLogPanel
from gui.widgets.chart_widget import ChartWidget
from gui.widgets.control_panel import ControlPanel
from gui.widgets.positions_table import PositionsTable
from gui.widgets.price_panel import PricePanel
from gui.widgets.risk_config_panel import RiskConfigPanel
from gui.widgets.skill_manager_panel import SkillManagerPanel
from utils.logger import logger


class MainWindow(QMainWindow):
    def __init__(self, settings, connector, agent, risk_manager):
        super().__init__()
        self._settings = settings
        self._connector = connector
        self._agent = agent
        self._risk_manager = risk_manager
        self._bot: ScalpingBot | None = None
        self._bot_thread: QThread | None = None

        self._setup_ui()
        self._apply_dark_style()
        self.setWindowTitle("Gold House AI — XAUUSD Scalping Bot")
        self.resize(1400, 900)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(6, 6, 6, 6)
        root_layout.setSpacing(4)

        # ── Header ──────────────────────────────────────────────────────────
        header = QLabel("🏆 Gold House AI — XAUUSD Scalping Desk | Powered by Hermes Agent + Kimi AI")
        header.setFont(QFont("Consolas", 12, QFont.Bold))
        header.setStyleSheet("color: #ffd700; padding: 4px;")
        root_layout.addWidget(header)

        # ── Top row: Account + Chart + Price ────────────────────────────────
        self._account_panel = AccountPanel()
        self._chart = ChartWidget()
        self._price_panel = PricePanel()

        top_splitter = QSplitter(Qt.Horizontal)
        top_splitter.addWidget(self._account_panel)
        top_splitter.addWidget(self._chart)
        top_splitter.addWidget(self._price_panel)
        top_splitter.setSizes([180, 800, 200])
        root_layout.addWidget(top_splitter, stretch=4)

        # ── Positions table ──────────────────────────────────────────────────
        self._positions = PositionsTable()
        root_layout.addWidget(self._positions, stretch=2)

        # ── Bottom row: Agent log + Skill manager + Risk config ───────────────
        self._agent_log = AgentLogPanel()
        self._skill_mgr = SkillManagerPanel()
        self._risk_config = RiskConfigPanel(self._settings)
        self._risk_config.settings_applied.connect(self._apply_settings)

        bottom_splitter = QSplitter(Qt.Horizontal)
        bottom_splitter.addWidget(self._agent_log)
        bottom_splitter.addWidget(self._skill_mgr)
        bottom_splitter.addWidget(self._risk_config)
        bottom_splitter.setSizes([500, 250, 300])
        root_layout.addWidget(bottom_splitter, stretch=3)

        # ── Control panel ────────────────────────────────────────────────────
        self._controls = ControlPanel()
        self._controls.start_clicked.connect(self._start_bot)
        self._controls.stop_clicked.connect(self._stop_bot)
        self._controls.close_all_clicked.connect(self._close_all_positions)
        self._controls.timeframe_changed.connect(self._chart.set_timeframe)
        root_layout.addWidget(self._controls)

    def _start_bot(self):
        if self._bot_thread and self._bot_thread.isRunning():
            return

        try:
            connected = self._connector.connect(
                self._settings.MT5_LOGIN,
                self._settings.MT5_PASSWORD,
                self._settings.MT5_SERVER,
            )
        except Exception as e:
            QMessageBox.critical(self, "MT5 Connection Error", str(e))
            return

        self._bot = ScalpingBot(self._settings, self._connector, self._agent, self._risk_manager)
        self._bot_thread = QThread()
        self._bot.moveToThread(self._bot_thread)

        self._bot_thread.started.connect(self._bot.run)
        self._bot.price_updated.connect(self._on_price_updated)
        self._bot.candles_updated.connect(self._chart.update_candles)
        self._bot.agent_decision.connect(self._on_agent_decision)
        self._bot.positions_updated.connect(self._positions.update_positions)
        self._bot.account_updated.connect(self._on_account_updated)
        self._bot.error_occurred.connect(self._on_error)
        self._bot.status_changed.connect(self._controls.update_status_text)

        self._bot_thread.start()
        self._controls.set_running(True)
        self._agent_log.add_status("Bot started — Hermes Agent active")
        logger.info("Bot started from GUI")

    def _stop_bot(self):
        if self._bot:
            self._bot.stop()
        if self._bot_thread:
            self._bot_thread.quit()
            self._bot_thread.wait(5000)
        self._controls.set_running(False)
        self._agent_log.add_status("Bot stopped")
        logger.info("Bot stopped from GUI")

    def _close_all_positions(self):
        try:
            count = self._connector.close_all_positions()
            self._agent_log.add_status(f"Closed {count} positions manually")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _on_price_updated(self, bid: float, ask: float, spread: float):
        self._price_panel.update_price(bid, ask, spread)

    def _on_account_updated(self, balance: float, equity: float, daily_pnl: float):
        self._account_panel.update_account(balance, equity, daily_pnl)
        self._account_panel.update_compound(self._risk_manager.compound_factor)
        if balance > 0:
            pct = (daily_pnl / balance) * 100
            self._risk_manager.adjust_compound_factor(pct)

    def _on_agent_decision(self, action: str, reasoning: str, confidence: float):
        self._agent_log.add_entry(action, reasoning, confidence)
        self._skill_mgr.refresh_skills()

    def _on_error(self, message: str):
        self._agent_log.add_status(f"ERROR: {message}")
        logger.error("GUI error: %s", message)

    def _apply_settings(self, new_settings: dict):
        for k, v in new_settings.items():
            if hasattr(self._settings, k):
                setattr(self._settings, k, v)
        self._agent_log.add_status("Settings applied")

    def _apply_dark_style(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #0d1117; color: #c9d1d9; }
            QGroupBox { border: 1px solid #30363d; border-radius: 4px; margin-top: 8px; padding-top: 6px; }
            QGroupBox::title { color: #ffd700; subcontrol-origin: margin; left: 8px; }
            QPushButton { background: #21262d; color: #c9d1d9; border: 1px solid #30363d; border-radius: 3px; padding: 4px 10px; }
            QPushButton:hover { background: #30363d; }
            QPushButton:disabled { color: #555; }
            QTableWidget { gridline-color: #21262d; border: none; }
            QHeaderView::section { background: #161b22; color: #8b949e; border: 1px solid #21262d; }
            QSpinBox, QDoubleSpinBox, QComboBox { background: #21262d; color: #c9d1d9; border: 1px solid #30363d; padding: 2px; }
            QListWidget { background: #161b22; border: 1px solid #30363d; }
            QSplitter::handle { background: #21262d; }
        """)

    def closeEvent(self, event):
        self._stop_bot()
        self._connector.disconnect()
        event.accept()
