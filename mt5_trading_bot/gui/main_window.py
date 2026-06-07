"""
Main Window - PyQt5 application window with tabbed interface.
"""
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget,
    QLabel, QStatusBar, QHBoxLayout, QVBoxLayout
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor
from loguru import logger

from core.mt5_connector import MT5Connector
from core.training_manager import TrainingManager
from trading.live_trader import LiveTrader
from gui.training_tab import TrainingTab
from gui.live_tab import LiveTab
from gui.backtest_tab import BacktestTab
from gui.settings_tab import SettingsTab


class MainWindow(QMainWindow):
    status_update = pyqtSignal(str)

    def __init__(self, config: dict, connector: MT5Connector,
                 training_manager: TrainingManager, live_trader: LiveTrader):
        super().__init__()
        self.config = config
        self.connector = connector
        self.training_manager = training_manager
        self.live_trader = live_trader

        self._setup_ui()
        self._setup_status_timer()

    def _setup_ui(self):
        self.setWindowTitle("MT5 Mathematical Trading Bot v1.0")
        self.setMinimumSize(1100, 700)
        self._apply_dark_theme()

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.training_tab = TrainingTab(
            self.config, self.connector, self.training_manager
        )
        self.live_tab = LiveTab(
            self.config, self.connector, self.live_trader
        )
        self.backtest_tab = BacktestTab(self.config)
        self.settings_tab = SettingsTab(self.config)

        self.tabs.addTab(self.training_tab, "Training")
        self.tabs.addTab(self.live_tab, "Live Trading")
        self.tabs.addTab(self.backtest_tab, "Backtest Results")
        self.tabs.addTab(self.settings_tab, "Settings")

        layout.addWidget(self.tabs)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._status_connection = QLabel("MT5: Disconnected")
        self._status_balance = QLabel("Balance: --")
        self._status_mode = QLabel("Mode: --")
        self.status_bar.addPermanentWidget(self._status_connection)
        self.status_bar.addPermanentWidget(QLabel("|"))
        self.status_bar.addPermanentWidget(self._status_balance)
        self.status_bar.addPermanentWidget(QLabel("|"))
        self.status_bar.addPermanentWidget(self._status_mode)

        # Connect settings changes
        self.settings_tab.config_saved.connect(self._on_config_saved)

    def _setup_status_timer(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_status)
        self._timer.start(3000)

    def _update_status(self):
        connected = self.connector.is_connected()
        if connected:
            self._status_connection.setText("MT5: Connected ●")
            self._status_connection.setStyleSheet("color: #00cc00;")
            acct = self.connector.get_account_info()
            balance = acct.get("balance", 0)
            equity = acct.get("equity", 0)
            self._status_balance.setText(
                f"Balance: {balance:,.2f} | Equity: {equity:,.2f}"
            )
        else:
            self._status_connection.setText("MT5: Disconnected ○")
            self._status_connection.setStyleSheet("color: #cc0000;")

        mode = self.live_trader.mode.upper() if self.live_trader.is_running() else "IDLE"
        running = "RUNNING" if self.live_trader.is_running() else "STOPPED"
        self._status_mode.setText(f"Live: {running} ({mode})")

    def _on_config_saved(self, new_config: dict):
        self.config.update(new_config)
        logger.info("Configuration updated")

    def _apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
        palette.setColor(QPalette.Base, QColor(40, 40, 40))
        palette.setColor(QPalette.AlternateBase, QColor(50, 50, 50))
        palette.setColor(QPalette.Text, QColor(220, 220, 220))
        palette.setColor(QPalette.Button, QColor(55, 55, 55))
        palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
        palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        QApplication.setPalette(palette)
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #1e1e1e; color: #dcdcdc; }
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background: #2d2d2d; color: #aaa; padding: 8px 16px; }
            QTabBar::tab:selected { background: #1e1e1e; color: #fff; border-bottom: 2px solid #007acc; }
            QPushButton { background: #2d2d2d; color: #ddd; border: 1px solid #555; padding: 6px 16px; border-radius: 3px; }
            QPushButton:hover { background: #3c3c3c; }
            QPushButton#start_btn { background: #0a7a0a; color: white; }
            QPushButton#stop_btn { background: #7a0a0a; color: white; }
            QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {
                background: #2d2d2d; color: #ddd; border: 1px solid #555; padding: 4px;
            }
            QTableWidget { gridline-color: #444; }
            QHeaderView::section { background: #2d2d2d; color: #aaa; border: none; padding: 4px; }
            QProgressBar { background: #2d2d2d; border: 1px solid #555; border-radius: 3px; }
            QProgressBar::chunk { background: #007acc; }
            QLabel#win { color: #00cc66; }
            QLabel#loss { color: #cc3300; }
            QGroupBox { border: 1px solid #444; margin-top: 8px; padding-top: 8px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; color: #888; }
        """)

    def closeEvent(self, event):
        self.live_trader.stop()
        self.training_manager.stop()
        event.accept()
