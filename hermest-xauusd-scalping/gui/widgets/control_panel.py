from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QComboBox
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont


class ControlPanel(QWidget):
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    close_all_clicked = pyqtSignal()
    timeframe_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._start_btn = QPushButton("▶ START BOT")
        self._start_btn.setStyleSheet("background: #238636; color: white; font-weight: bold; padding: 8px 16px;")
        self._start_btn.clicked.connect(self.start_clicked)

        self._stop_btn = QPushButton("■ STOP")
        self._stop_btn.setStyleSheet("background: #da3633; color: white; font-weight: bold; padding: 8px 16px;")
        self._stop_btn.clicked.connect(self.stop_clicked)
        self._stop_btn.setEnabled(False)

        self._close_all_btn = QPushButton("✕ Close All Positions")
        self._close_all_btn.setStyleSheet("background: #6e40c9; color: white; padding: 8px 16px;")
        self._close_all_btn.clicked.connect(self.close_all_clicked)

        self._tf_combo = QComboBox()
        self._tf_combo.addItems(["M1", "M5", "M15", "H1"])
        self._tf_combo.setCurrentText("M5")
        self._tf_combo.currentTextChanged.connect(self.timeframe_changed)

        self._status_label = QLabel("● STOPPED")
        self._status_label.setStyleSheet("color: #888; font-weight: bold;")
        self._status_label.setFont(QFont("Consolas", 11))

        layout.addWidget(self._start_btn)
        layout.addWidget(self._stop_btn)
        layout.addWidget(self._close_all_btn)
        layout.addSpacing(20)
        layout.addWidget(QLabel("Chart:"))
        layout.addWidget(self._tf_combo)
        layout.addStretch()
        layout.addWidget(self._status_label)

    def set_running(self, running: bool):
        self._start_btn.setEnabled(not running)
        self._stop_btn.setEnabled(running)
        if running:
            self._status_label.setText("● RUNNING")
            self._status_label.setStyleSheet("color: #44ff44; font-weight: bold;")
        else:
            self._status_label.setText("● STOPPED")
            self._status_label.setStyleSheet("color: #888; font-weight: bold;")

    def update_status_text(self, text: str):
        self._status_label.setText(f"● {text[:40]}")
