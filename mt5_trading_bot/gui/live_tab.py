"""
Live Trading Tab - monitor live trades, handle manual signal confirmation.
"""
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QCheckBox, QHeaderView, QFrame, QDialog,
    QDialogButtonBox, QFormLayout, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from loguru import logger

from core.mt5_connector import MT5Connector
from trading.live_trader import LiveTrader, TradeSignal

SYMBOLS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "US30", "NAS100", "BTCUSD"]


class SignalDialog(QDialog):
    """Modal dialog for manual trade confirmation."""
    def __init__(self, signal: TradeSignal, parent=None):
        super().__init__(parent)
        self.signal = signal
        self.setWindowTitle("Trade Signal - Manual Confirmation")
        self.setMinimumWidth(350)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        direction_color = "#00cc66" if self.signal.direction == "buy" else "#cc3300"
        dir_label = QLabel(f"{self.signal.direction.upper()} {self.signal.symbol}")
        dir_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {direction_color};")
        dir_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(dir_label)

        form = QFormLayout()
        form.addRow("Entry:", QLabel(f"{self.signal.entry:.5f}"))
        form.addRow("Stop Loss:", QLabel(f"{self.signal.sl:.5f}  ({self.signal.sl_distance:.5f} pts)"))
        form.addRow("Take Profit:", QLabel(f"{self.signal.tp:.5f}  ({self.signal.tp_distance:.5f} pts)"))
        form.addRow("RR Ratio:", QLabel(f"1:{self.signal.rr:.1f}"))
        form.addRow("Formula WR:", QLabel(f"{self.signal.winrate:.1%}"))
        form.addRow("Formula ID:", QLabel(self.signal.formula_id))
        layout.addLayout(form)

        btns = QDialogButtonBox()
        execute_btn = btns.addButton("✓  EXECUTE", QDialogButtonBox.AcceptRole)
        skip_btn = btns.addButton("✗  SKIP", QDialogButtonBox.RejectRole)
        execute_btn.setStyleSheet("background: #0a7a0a; color: white; padding: 8px 16px;")
        skip_btn.setStyleSheet("background: #7a0a0a; color: white; padding: 8px 16px;")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)


class LiveTab(QWidget):
    def __init__(self, config: dict, connector: MT5Connector, live_trader: LiveTrader):
        super().__init__()
        self.config = config
        self.connector = connector
        self.live_trader = live_trader
        self._setup_ui()
        self._setup_callbacks()
        self._setup_refresh_timer()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Top: controls
        ctrl_group = QGroupBox("Live Trading Control")
        ctrl_h = QHBoxLayout(ctrl_group)

        # Symbol selection
        ctrl_h.addWidget(QLabel("Symbols:"))
        self.symbols_list = QComboBox()
        self.symbols_list.addItems(SYMBOLS)
        self.symbols_list.setEditable(False)
        ctrl_h.addWidget(self.symbols_list)

        ctrl_h.addWidget(QLabel("Mode:"))
        self.mode_auto = QCheckBox("Auto")
        self.mode_manual = QCheckBox("Manual")
        self.mode_manual.setChecked(True)
        self.mode_auto.stateChanged.connect(lambda s: self.mode_manual.setChecked(not s))
        self.mode_manual.stateChanged.connect(lambda s: self.mode_auto.setChecked(not s))
        ctrl_h.addWidget(self.mode_auto)
        ctrl_h.addWidget(self.mode_manual)

        self.start_btn = QPushButton("▶  START")
        self.start_btn.setObjectName("start_btn")
        self.stop_btn = QPushButton("■  STOP")
        self.stop_btn.setObjectName("stop_btn")
        self.stop_btn.setEnabled(False)
        ctrl_h.addStretch()
        ctrl_h.addWidget(self.start_btn)
        ctrl_h.addWidget(self.stop_btn)

        main_layout.addWidget(ctrl_group)

        # Middle row
        middle = QHBoxLayout()

        # Active formulas table
        formula_group = QGroupBox("Active Formulas")
        formula_layout = QVBoxLayout(formula_group)
        self.formula_table = QTableWidget(0, 4)
        self.formula_table.setHorizontalHeaderLabels(["Symbol", "WinRate", "Direction", "Status"])
        self.formula_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.formula_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.formula_table.setAlternatingRowColors(True)
        formula_layout.addWidget(self.formula_table)
        middle.addWidget(formula_group, 1)

        # Account info
        acct_group = QGroupBox("Account")
        acct_layout = QFormLayout(acct_group)
        self.lbl_balance = QLabel("--")
        self.lbl_equity = QLabel("--")
        self.lbl_profit = QLabel("--")
        self.lbl_positions = QLabel("--")
        acct_layout.addRow("Balance:", self.lbl_balance)
        acct_layout.addRow("Equity:", self.lbl_equity)
        acct_layout.addRow("Open P&L:", self.lbl_profit)
        acct_layout.addRow("Positions:", self.lbl_positions)
        middle.addWidget(acct_group)

        main_layout.addLayout(middle)

        # Open positions table
        pos_group = QGroupBox("Open Positions")
        pos_layout = QVBoxLayout(pos_group)
        self.positions_table = QTableWidget(0, 7)
        self.positions_table.setHorizontalHeaderLabels(
            ["Ticket", "Symbol", "Type", "Volume", "Open Price", "SL", "Profit"]
        )
        self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.positions_table.setEditTriggers(QTableWidget.NoEditTriggers)
        pos_layout.addWidget(self.positions_table)
        main_layout.addWidget(pos_group)

        # Trade log
        log_group = QGroupBox("Trade Log")
        log_layout = QVBoxLayout(log_group)
        self.trade_table = QTableWidget(0, 6)
        self.trade_table.setHorizontalHeaderLabels(
            ["Time", "Symbol", "Direction", "Entry", "Exit/Status", "P&L (R)"]
        )
        self.trade_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.trade_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.trade_table.setMaximumHeight(150)
        log_layout.addWidget(self.trade_table)
        main_layout.addWidget(log_group)

        # Connect buttons
        self.start_btn.clicked.connect(self._start_trading)
        self.stop_btn.clicked.connect(self._stop_trading)

    def _setup_callbacks(self):
        self.live_trader.on_signal = self._on_signal_received
        self.live_trader.on_trade_opened = self._on_trade_opened

    def _setup_refresh_timer(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh_data)
        self._timer.start(5000)

    def _start_trading(self):
        mode = "auto" if self.mode_auto.isChecked() else "manual"
        self.live_trader.set_mode(mode)
        symbol = self.symbols_list.currentText()
        self.live_trader.start([symbol])
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self._refresh_formulas()

    def _stop_trading(self):
        self.live_trader.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def _on_signal_received(self, signal: TradeSignal):
        """Called from background thread - must use QTimer to show dialog."""
        QTimer.singleShot(0, lambda: self._show_signal_dialog(signal))

    def _show_signal_dialog(self, signal: TradeSignal):
        dlg = SignalDialog(signal, self)
        if dlg.exec_() == dlg.Accepted:
            self.live_trader.confirm_signal(signal)
        else:
            self.live_trader.reject_signal(signal)

    def _on_trade_opened(self, trade_info: dict):
        """Add trade to log table."""
        row = self.trade_table.rowCount()
        self.trade_table.insertRow(row)
        t = trade_info
        items = [
            str(t.get("entry_time", "")[:19]),
            t.get("symbol", ""),
            t.get("direction", "").upper(),
            f"{t.get('entry_price', 0):.5f}",
            "OPEN",
            "--",
        ]
        for col, txt in enumerate(items):
            item = QTableWidgetItem(txt)
            if txt == t.get("direction", "").upper():
                item.setForeground(QColor("#00cc66") if txt == "BUY" else QColor("#cc3300"))
            self.trade_table.setItem(row, col, item)

    def _refresh_data(self):
        if not self.connector.is_connected():
            return
        # Update account info
        acct = self.connector.get_account_info()
        if acct:
            self.lbl_balance.setText(f"{acct.get('balance', 0):,.2f}")
            self.lbl_equity.setText(f"{acct.get('equity', 0):,.2f}")
            profit = acct.get("profit", 0)
            color = "#00cc66" if profit >= 0 else "#cc3300"
            self.lbl_profit.setText(f"<span style='color:{color}'>{profit:+.2f}</span>")

        # Update open positions
        positions = self.connector.get_open_positions()
        self.lbl_positions.setText(str(len(positions)))
        self.positions_table.setRowCount(0)
        for pos in positions:
            row = self.positions_table.rowCount()
            self.positions_table.insertRow(row)
            items = [
                str(pos.get("ticket", "")),
                pos.get("symbol", ""),
                pos.get("type", "").upper(),
                str(pos.get("volume", "")),
                f"{pos.get('open_price', 0):.5f}",
                f"{pos.get('sl', 0):.5f}",
                f"{pos.get('profit', 0):+.2f}",
            ]
            for col, txt in enumerate(items):
                item = QTableWidgetItem(txt)
                if col == 6:
                    try:
                        v = float(txt)
                        item.setForeground(QColor("#00cc66") if v >= 0 else QColor("#cc3300"))
                    except ValueError:
                        pass
                self.positions_table.setItem(row, col, item)

    def _refresh_formulas(self):
        formulas = self.live_trader._active_formulas
        winrates = self.live_trader._formula_winrates
        self.formula_table.setRowCount(0)
        for symbol, formula in formulas.items():
            row = self.formula_table.rowCount()
            self.formula_table.insertRow(row)
            wr = winrates.get(symbol, 0)
            wr_color = "#00cc66" if wr >= 0.75 else "#ffaa00"
            items_data = [
                (symbol, "#fff"),
                (f"{wr:.1%}", wr_color),
                (formula.get("direction", "both").upper(), "#aaa"),
                ("ACTIVE", "#00cc66"),
            ]
            for col, (txt, color) in enumerate(items_data):
                item = QTableWidgetItem(txt)
                item.setForeground(QColor(color))
                self.formula_table.setItem(row, col, item)
