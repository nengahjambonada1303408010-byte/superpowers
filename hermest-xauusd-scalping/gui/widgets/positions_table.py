from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class PositionsTable(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Open Positions", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self._table = QTableWidget(0, 8)
        self._table.setHorizontalHeaderLabels(
            ["Ticket", "Type", "Lots", "Open Price", "SL", "TP", "Current", "P&L"]
        )
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self._table)

    def update_positions(self, positions: list):
        self._table.setRowCount(len(positions))
        for row, p in enumerate(positions):
            side = "BUY" if p.get("type") == 0 else "SELL"
            profit = p.get("profit", 0.0)

            values = [
                str(p.get("ticket", "")),
                side,
                f"{p.get('volume', 0):.2f}",
                f"{p.get('price_open', 0):.2f}",
                f"{p.get('sl', 0):.2f}",
                f"{p.get('tp', 0):.2f}",
                f"{p.get('price_current', 0):.2f}",
                f"{profit:+.2f}",
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if col == 7:
                    item.setForeground(QColor("#44ff44" if profit >= 0 else "#ff4444"))
                self._table.setItem(row, col, item)
