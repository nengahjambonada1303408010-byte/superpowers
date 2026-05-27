from PyQt5.QtWidgets import QGroupBox, QFormLayout, QLabel
from PyQt5.QtGui import QFont


class AccountPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Account", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout(self)
        font = QFont("Consolas", 11)

        self._balance = QLabel("--")
        self._equity = QLabel("--")
        self._daily_pnl = QLabel("--")
        self._compound = QLabel("1.00×")

        for lbl in (self._balance, self._equity, self._daily_pnl, self._compound):
            lbl.setFont(font)

        layout.addRow("Balance:", self._balance)
        layout.addRow("Equity:", self._equity)
        layout.addRow("Day P&L:", self._daily_pnl)
        layout.addRow("Compound:", self._compound)

    def update_account(self, balance: float, equity: float, daily_pnl: float):
        self._balance.setText(f"${balance:,.2f}")
        self._equity.setText(f"${equity:,.2f}")
        color = "#44ff44" if daily_pnl >= 0 else "#ff4444"
        self._daily_pnl.setText(f"${daily_pnl:+.2f}")
        self._daily_pnl.setStyleSheet(f"color: {color};")

    def update_compound(self, factor: float):
        self._compound.setText(f"{factor:.2f}×")
