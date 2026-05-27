from PyQt5.QtWidgets import QGroupBox, QGridLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class PricePanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Live Price", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QGridLayout(self)
        font_big = QFont("Consolas", 20, QFont.Bold)
        font_med = QFont("Consolas", 11)

        self._bid = QLabel("---.--")
        self._bid.setFont(font_big)
        self._bid.setStyleSheet("color: #ff4444;")

        self._ask = QLabel("---.--")
        self._ask.setFont(font_big)
        self._ask.setStyleSheet("color: #44ff44;")

        self._spread = QLabel("Spread: --")
        self._spread.setFont(font_med)

        self._atr = QLabel("ATR: --")
        self._atr.setFont(font_med)

        self._rsi = QLabel("RSI: --")
        self._rsi.setFont(font_med)

        self._ema = QLabel("EMA20: --")
        self._ema.setFont(font_med)

        layout.addWidget(QLabel("BID"), 0, 0, Qt.AlignCenter)
        layout.addWidget(QLabel("ASK"), 0, 1, Qt.AlignCenter)
        layout.addWidget(self._bid, 1, 0, Qt.AlignCenter)
        layout.addWidget(self._ask, 1, 1, Qt.AlignCenter)
        layout.addWidget(self._spread, 2, 0, 1, 2, Qt.AlignCenter)
        layout.addWidget(self._atr, 3, 0)
        layout.addWidget(self._rsi, 3, 1)
        layout.addWidget(self._ema, 4, 0, 1, 2)

    def update_price(self, bid: float, ask: float, spread: float):
        self._bid.setText(f"{bid:.2f}")
        self._ask.setText(f"{ask:.2f}")
        self._spread.setText(f"Spread: {spread:.3f} ({spread/0.01:.0f} pts)")

    def update_indicators(self, atr: float, rsi: float, ema: float):
        self._atr.setText(f"ATR14: {atr:.2f}")
        color = "#ff4444" if rsi > 65 else "#44ff44" if rsi < 35 else "#ffffff"
        self._rsi.setText(f"RSI14: {rsi:.1f}")
        self._rsi.setStyleSheet(f"color: {color};")
        self._ema.setText(f"EMA20: {ema:.2f}")
