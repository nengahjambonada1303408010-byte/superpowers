from PyQt5.QtWidgets import (QGroupBox, QFormLayout, QDoubleSpinBox, QSpinBox, QPushButton,
                              QCheckBox)
from PyQt5.QtCore import pyqtSignal


class RiskConfigPanel(QGroupBox):
    settings_applied = pyqtSignal(dict)

    def __init__(self, settings, parent=None):
        super().__init__("Risk Configuration", parent)
        self._settings = settings
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout(self)

        self._risk_pct = QDoubleSpinBox()
        self._risk_pct.setRange(0.1, 5.0)
        self._risk_pct.setSingleStep(0.1)
        self._risk_pct.setValue(self._settings.RISK_PCT_PER_TRADE)
        self._risk_pct.setSuffix(" %")

        self._max_loss = QDoubleSpinBox()
        self._max_loss.setRange(1.0, 10.0)
        self._max_loss.setSingleStep(0.5)
        self._max_loss.setValue(self._settings.MAX_DAILY_LOSS_PCT)
        self._max_loss.setSuffix(" %")

        self._max_pos = QSpinBox()
        self._max_pos.setRange(1, 10)
        self._max_pos.setValue(self._settings.MAX_CONCURRENT_POSITIONS)

        self._atr_period = QSpinBox()
        self._atr_period.setRange(5, 50)
        self._atr_period.setValue(self._settings.ATR_PERIOD)

        self._sl_mult = QDoubleSpinBox()
        self._sl_mult.setRange(0.5, 5.0)
        self._sl_mult.setSingleStep(0.1)
        self._sl_mult.setValue(self._settings.ATR_SL_MULTIPLIER)

        self._rr_ratio = QDoubleSpinBox()
        self._rr_ratio.setRange(1.0, 5.0)
        self._rr_ratio.setSingleStep(0.1)
        self._rr_ratio.setValue(self._settings.RR_RATIO)

        self._compound = QCheckBox("Enable")
        self._compound.setChecked(self._settings.COMPOUND_PROFIT)

        self._loop_interval = QSpinBox()
        self._loop_interval.setRange(5, 120)
        self._loop_interval.setValue(self._settings.LOOP_INTERVAL_SECONDS)
        self._loop_interval.setSuffix(" s")

        apply_btn = QPushButton("Apply Settings")
        apply_btn.clicked.connect(self._apply)

        layout.addRow("Risk / Trade:", self._risk_pct)
        layout.addRow("Max Daily Loss:", self._max_loss)
        layout.addRow("Max Positions:", self._max_pos)
        layout.addRow("ATR Period:", self._atr_period)
        layout.addRow("SL Multiplier:", self._sl_mult)
        layout.addRow("RR Ratio:", self._rr_ratio)
        layout.addRow("Compounding:", self._compound)
        layout.addRow("Loop Interval:", self._loop_interval)
        layout.addRow("", apply_btn)

    def _apply(self):
        self.settings_applied.emit({
            "RISK_PCT_PER_TRADE": self._risk_pct.value(),
            "MAX_DAILY_LOSS_PCT": self._max_loss.value(),
            "MAX_CONCURRENT_POSITIONS": self._max_pos.value(),
            "ATR_PERIOD": self._atr_period.value(),
            "ATR_SL_MULTIPLIER": self._sl_mult.value(),
            "RR_RATIO": self._rr_ratio.value(),
            "COMPOUND_PROFIT": self._compound.isChecked(),
            "LOOP_INTERVAL_SECONDS": self._loop_interval.value(),
        })
