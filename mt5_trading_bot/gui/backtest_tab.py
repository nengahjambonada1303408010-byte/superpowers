"""
Backtest Tab - display saved formula results with equity curve.
"""
import json
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFormLayout, QComboBox, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

try:
    import pyqtgraph as pg
    import numpy as np
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False

REGISTRY_FILE = Path("data/formulas/registry.json")


class BacktestTab(QWidget):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self._formulas = []
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Top: controls
        ctrl_h = QHBoxLayout()
        self.refresh_btn = QPushButton("↻  Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        ctrl_h.addWidget(self.refresh_btn)
        ctrl_h.addStretch()
        layout.addLayout(ctrl_h)

        splitter = QSplitter(Qt.Horizontal)

        # Formula list
        left = QWidget()
        left_layout = QVBoxLayout(left)

        self.formula_table = QTableWidget(0, 5)
        self.formula_table.setHorizontalHeaderLabels(
            ["Symbol", "Val WR", "Test WR", "PF", "Date"]
        )
        self.formula_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.formula_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.formula_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.formula_table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        left_layout.addWidget(QLabel("Saved Formulas:"))
        left_layout.addWidget(self.formula_table)
        splitter.addWidget(left)

        # Detail panel
        right = QWidget()
        right_layout = QVBoxLayout(right)

        self.detail_group = QGroupBox("Formula Details")
        detail_form = QFormLayout(self.detail_group)
        self.lbl_symbol = QLabel("--")
        self.lbl_val_wr = QLabel("--")
        self.lbl_test_wr = QLabel("--")
        self.lbl_val_pf = QLabel("--")
        self.lbl_val_trades = QLabel("--")
        self.lbl_val_dd = QLabel("--")
        self.lbl_trained_at = QLabel("--")
        self.lbl_formula_id = QLabel("--")
        self.lbl_conditions = QLabel("--")
        self.lbl_conditions.setWordWrap(True)
        detail_form.addRow("Symbol:", self.lbl_symbol)
        detail_form.addRow("Val WinRate:", self.lbl_val_wr)
        detail_form.addRow("Test WinRate:", self.lbl_test_wr)
        detail_form.addRow("Val Profit Factor:", self.lbl_val_pf)
        detail_form.addRow("Val Trades:", self.lbl_val_trades)
        detail_form.addRow("Val Max DD:", self.lbl_val_dd)
        detail_form.addRow("Trained At:", self.lbl_trained_at)
        detail_form.addRow("Formula ID:", self.lbl_formula_id)
        detail_form.addRow("Conditions:", self.lbl_conditions)
        right_layout.addWidget(self.detail_group)

        # Placeholder for equity curve
        if PYQTGRAPH_AVAILABLE:
            self.plot_widget = pg.PlotWidget(title="Equity Curve (Backtest)")
            self.plot_widget.setBackground("#1e1e1e")
            self.plot_widget.setLabel("left", "Equity (R)")
            self.plot_widget.setLabel("bottom", "Trade #")
            self._equity_curve = self.plot_widget.plot(pen=pg.mkPen("#007acc", width=2))
            right_layout.addWidget(self.plot_widget)
        else:
            right_layout.addWidget(QLabel("(pyqtgraph not available)"))

        right_layout.addStretch()
        splitter.addWidget(right)
        splitter.setSizes([400, 600])
        layout.addWidget(splitter)

    def refresh(self):
        """Reload formula registry from disk."""
        self._formulas = []
        if REGISTRY_FILE.exists():
            try:
                with open(REGISTRY_FILE) as f:
                    self._formulas = json.load(f)
            except Exception:
                pass

        self.formula_table.setRowCount(0)
        for entry in reversed(self._formulas):
            m = entry.get("metrics", {})
            row = self.formula_table.rowCount()
            self.formula_table.insertRow(row)
            val_wr = m.get("val_winrate", 0)
            test_wr = m.get("test_winrate", 0)
            items = [
                (m.get("symbol", "?"), "#fff"),
                (f"{val_wr:.1%}", "#00cc66" if val_wr >= 0.75 else "#ffaa00"),
                (f"{test_wr:.1%}", "#00cc66" if test_wr >= 0.75 else "#ffaa00"),
                (f"{m.get('val_profit_factor', 0):.2f}", "#aaa"),
                (m.get("trained_at", "")[:10], "#888"),
            ]
            for col, (txt, color) in enumerate(items):
                item = QTableWidgetItem(txt)
                item.setForeground(QColor(color))
                self.formula_table.setItem(row, col, item)

    def _on_selection_changed(self):
        rows = self.formula_table.selectionModel().selectedRows()
        if not rows:
            return
        idx = rows[0].row()
        # Reverse index since we display newest first
        entry_idx = len(self._formulas) - 1 - idx
        if 0 <= entry_idx < len(self._formulas):
            entry = self._formulas[entry_idx]
            self._show_formula_details(entry)

    def _show_formula_details(self, entry: dict):
        m = entry.get("metrics", {})
        f = entry.get("formula", {})

        val_wr = m.get("val_winrate", 0)
        test_wr = m.get("test_winrate", 0)
        wr_color = lambda wr: "#00cc66" if wr >= 0.75 else "#ffaa00"

        self.lbl_symbol.setText(m.get("symbol", "?"))
        self.lbl_val_wr.setText(
            f"<span style='color:{wr_color(val_wr)}'>{val_wr:.1%}</span>"
        )
        self.lbl_val_wr.setTextFormat(Qt.RichText)
        self.lbl_test_wr.setText(
            f"<span style='color:{wr_color(test_wr)}'>{test_wr:.1%}</span>"
        )
        self.lbl_test_wr.setTextFormat(Qt.RichText)
        self.lbl_val_pf.setText(f"{m.get('val_profit_factor', 0):.2f}")
        self.lbl_val_trades.setText(str(m.get("val_trades", 0)))
        dd = m.get("val_max_drawdown", 0)
        self.lbl_val_dd.setText(f"{dd:.1%}")
        self.lbl_trained_at.setText(str(m.get("trained_at", ""))[:19])
        self.lbl_formula_id.setText(f.get("id", "?"))
        conds = ", ".join(f.get("conditions", []))
        self.lbl_conditions.setText(
            f"[{f.get('direction','?').upper()}] {conds}"
        )
