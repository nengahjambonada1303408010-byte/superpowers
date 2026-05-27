import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt5.QtWidgets import QGroupBox, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPicture, QColor, QPen

from utils.indicators import ema


class CandlestickItem(pg.GraphicsObject):
    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self._df = df
        self._picture = QPicture()
        self._generate_picture()

    def _generate_picture(self):
        painter = QPainter(self._picture)
        painter.setPen(pg.mkPen("w"))
        w = 0.4

        for i, row in self._df.reset_index(drop=True).iterrows():
            x = float(i)
            o, h, l, c = row["open"], row["high"], row["low"], row["close"]
            if c >= o:
                painter.setBrush(pg.mkBrush("#26a641"))
                painter.setPen(pg.mkPen("#26a641"))
            else:
                painter.setBrush(pg.mkBrush("#da3633"))
                painter.setPen(pg.mkPen("#da3633"))

            from PyQt5.QtCore import QRectF, QLineF
            painter.drawLine(QLineF(x, l, x, h))
            painter.drawRect(QRectF(x - w / 2, min(o, c), w, abs(c - o) or 0.001))

        painter.end()

    def paint(self, painter, *_):
        painter.drawPicture(0, 0, self._picture)

    def boundingRect(self):
        return pg.QtCore.QRectF(self._picture.boundingRect())


class ChartWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("XAUUSD Chart (M5)", parent)
        self._setup_ui()
        self._current_tf = "M5"

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        pg.setConfigOption("background", "#0d1117")
        pg.setConfigOption("foreground", "#c9d1d9")

        self._plot = pg.PlotWidget()
        self._plot.showGrid(x=True, y=True, alpha=0.3)
        self._plot.getAxis("left").setStyle(tickFont=pg.QtGui.QFont("Consolas", 8))
        layout.addWidget(self._plot)

        self._candle_item = None
        self._ema_line = None

    def update_candles(self, df: pd.DataFrame):
        if df is None or df.empty:
            return
        self._plot.clear()

        display_df = df.tail(80).reset_index(drop=True)

        candles = CandlestickItem(display_df)
        self._plot.addItem(candles)

        ema_vals = ema(display_df["close"], 20).values
        ema_pen = pg.mkPen(color="#ff9500", width=1.5)
        self._plot.plot(list(range(len(ema_vals))), ema_vals, pen=ema_pen, name="EMA20")

        self._plot.setTitle(f"XAUUSD {self._current_tf}", color="#c9d1d9", size="10pt")

    def set_timeframe(self, tf: str):
        self._current_tf = tf
        self.setTitle(f"XAUUSD Chart ({tf})")
