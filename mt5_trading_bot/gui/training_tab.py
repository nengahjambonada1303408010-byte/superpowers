"""
Training Tab - GUI for running and monitoring the evolution engine.
"""
import threading
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QProgressBar, QPlainTextEdit, QFormLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont
from loguru import logger

try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False

from core.mt5_connector import MT5Connector
from core.training_manager import TrainingManager

SYMBOLS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "US30", "NAS100", "BTCUSD", "ETHUSD"]
TIMEFRAMES = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]


class TrainingWorker(QObject):
    progress = pyqtSignal(int, float, str, int)  # gen, winrate, formula_desc, max_gen
    finished = pyqtSignal(bool, str)             # success, message
    log_msg = pyqtSignal(str)

    def __init__(self, training_manager: TrainingManager, symbol: str):
        super().__init__()
        self.training_manager = training_manager
        self.symbol = symbol
        self._stopped = False

    def run(self):
        def callback(gen, best_wr, best_formula, max_gen):
            if self._stopped:
                raise InterruptedError("Stopped")
            desc = ""
            if best_formula:
                from core.formula_engine import FormulaEngine
                fe = FormulaEngine()
                desc = fe.describe_formula(best_formula)
            self.progress.emit(gen, best_wr, desc, max_gen)
            self.log_msg.emit(f"Gen {gen}/{max_gen} | Best WR: {best_wr:.1%} | {desc[:60]}")

        try:
            result = self.training_manager.run_training(self.symbol, callback=callback)
            if result:
                self.finished.emit(True, f"Training complete! Formula saved for {self.symbol}")
            else:
                self.finished.emit(False, f"No valid formula found for {self.symbol}")
        except Exception as e:
            self.finished.emit(False, str(e))


class TrainingTab(QWidget):
    def __init__(self, config: dict, connector: MT5Connector, training_manager: TrainingManager):
        super().__init__()
        self.config = config
        self.connector = connector
        self.training_manager = training_manager
        self._thread: QThread = None
        self._worker: TrainingWorker = None
        self._history_fitness = []
        self._history_winrate = []
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)

        # Left panel: controls
        left = QVBoxLayout()
        left.setSpacing(8)

        # --- Config group ---
        cfg_group = QGroupBox("Training Configuration")
        cfg_form = QFormLayout(cfg_group)

        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(SYMBOLS)
        cfg_form.addRow("Symbol:", self.symbol_combo)

        self.htf_combo = QComboBox()
        self.htf_combo.addItems(TIMEFRAMES)
        self.htf_combo.setCurrentText(self.config.get("training", {}).get("timeframe_htf", "H1"))
        cfg_form.addRow("Higher TF:", self.htf_combo)

        self.entry_combo = QComboBox()
        self.entry_combo.addItems(TIMEFRAMES)
        self.entry_combo.setCurrentText(self.config.get("training", {}).get("timeframe_entry", "M15"))
        cfg_form.addRow("Entry TF:", self.entry_combo)

        self.pop_spin = QSpinBox()
        self.pop_spin.setRange(100, 200000)
        self.pop_spin.setValue(self.config.get("training", {}).get("population_size", 10000))
        self.pop_spin.setSingleStep(1000)
        cfg_form.addRow("Population:", self.pop_spin)

        self.gen_spin = QSpinBox()
        self.gen_spin.setRange(10, 2000)
        self.gen_spin.setValue(self.config.get("training", {}).get("max_generations", 200))
        cfg_form.addRow("Max Generations:", self.gen_spin)

        self.wr_spin = QDoubleSpinBox()
        self.wr_spin.setRange(0.5, 0.99)
        self.wr_spin.setSingleStep(0.01)
        self.wr_spin.setValue(self.config.get("training", {}).get("target_winrate", 0.75))
        self.wr_spin.setDecimals(2)
        cfg_form.addRow("Target Winrate:", self.wr_spin)

        self.years_spin = QSpinBox()
        self.years_spin.setRange(1, 20)
        self.years_spin.setValue(self.config.get("training", {}).get("years_of_data", 5))
        cfg_form.addRow("Years of Data:", self.years_spin)

        left.addWidget(cfg_group)

        # --- Buttons ---
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶  START TRAINING")
        self.start_btn.setObjectName("start_btn")
        self.start_btn.setMinimumHeight(36)
        self.stop_btn = QPushButton("■  STOP")
        self.stop_btn.setObjectName("stop_btn")
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        left.addLayout(btn_layout)

        # --- Progress ---
        progress_group = QGroupBox("Progress")
        pg_layout = QVBoxLayout(progress_group)

        self.progress_label = QLabel("Ready")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.gen_label = QLabel("Generation: 0 / 0")
        self.wr_label = QLabel("Best Winrate: --")
        self.wr_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #00aaff;")

        pg_layout.addWidget(self.progress_label)
        pg_layout.addWidget(self.progress_bar)
        pg_layout.addWidget(self.gen_label)
        pg_layout.addWidget(self.wr_label)
        left.addWidget(progress_group)

        # --- Formula Preview ---
        formula_group = QGroupBox("Best Formula")
        f_layout = QVBoxLayout(formula_group)
        self.formula_label = QLabel("(no formula yet)")
        self.formula_label.setWordWrap(True)
        self.formula_label.setStyleSheet("color: #88ff88; font-family: monospace;")
        f_layout.addWidget(self.formula_label)
        left.addWidget(formula_group)
        left.addStretch()

        main_layout.addLayout(left, 1)

        # Right panel: charts + log
        right = QVBoxLayout()

        # Evolution chart
        if PYQTGRAPH_AVAILABLE:
            self.plot_widget = pg.PlotWidget(title="Evolution Progress")
            self.plot_widget.setBackground("#1e1e1e")
            self.plot_widget.setLabel("left", "Value")
            self.plot_widget.setLabel("bottom", "Generation")
            self.plot_widget.addLegend()
            self.plot_widget.setMinimumHeight(250)
            self._fitness_curve = self.plot_widget.plot(pen=pg.mkPen("#007acc", width=2), name="Fitness")
            self._wr_curve = self.plot_widget.plot(pen=pg.mkPen("#00cc66", width=2), name="Win Rate")
            right.addWidget(self.plot_widget)
        else:
            right.addWidget(QLabel("(pyqtgraph not available - no chart)"))

        # Log
        log_group = QGroupBox("Training Log")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(500)
        self.log_text.setStyleSheet("font-family: monospace; font-size: 11px; background: #111; color: #ccc;")
        log_layout.addWidget(self.log_text)
        right.addWidget(log_group, 1)

        main_layout.addLayout(right, 2)

        # Connect signals
        self.start_btn.clicked.connect(self._start_training)
        self.stop_btn.clicked.connect(self._stop_training)

    def _start_training(self):
        symbol = self.symbol_combo.currentText()

        # Apply config overrides from UI
        self.config.setdefault("training", {})
        self.config["training"]["timeframe_htf"] = self.htf_combo.currentText()
        self.config["training"]["timeframe_entry"] = self.entry_combo.currentText()
        self.config["training"]["population_size"] = self.pop_spin.value()
        self.config["training"]["max_generations"] = self.gen_spin.value()
        self.config["training"]["target_winrate"] = self.wr_spin.value()
        self.config["training"]["years_of_data"] = self.years_spin.value()

        self.training_manager.evolution_engine.population_size = self.pop_spin.value()
        self.training_manager.evolution_engine.max_generations = self.gen_spin.value()
        self.training_manager.evolution_engine.target_winrate = self.wr_spin.value()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self._history_fitness = []
        self._history_winrate = []
        self.log_text.clear()
        self._append_log(f"Starting training: {symbol}...")

        self._thread = QThread()
        self._worker = TrainingWorker(self.training_manager, symbol)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.log_msg.connect(self._append_log)
        self._worker.finished.connect(self._thread.quit)

        self._thread.start()

    def _stop_training(self):
        self.training_manager.stop()
        self.stop_btn.setEnabled(False)
        self._append_log("Stop signal sent...")

    def _on_progress(self, gen: int, best_wr: float, formula_desc: str, max_gen: int):
        pct = int(gen / max_gen * 100) if max_gen > 0 else 0
        self.progress_bar.setValue(pct)
        self.gen_label.setText(f"Generation: {gen} / {max_gen}")
        self.wr_label.setText(f"Best Winrate: {best_wr:.1%}")
        self.progress_label.setText(f"Evolving... Gen {gen}/{max_gen}")
        if formula_desc:
            self.formula_label.setText(formula_desc)

        self._history_winrate.append(best_wr)
        self._history_fitness.append(gen)

        if PYQTGRAPH_AVAILABLE and len(self._history_winrate) > 1:
            self._wr_curve.setData(self._history_fitness, self._history_winrate)

        if best_wr >= self.wr_spin.value():
            self.wr_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #00cc66;")
        else:
            self.wr_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #00aaff;")

    def _on_finished(self, success: bool, message: str):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        color = "#00cc66" if success else "#cc3300"
        self._append_log(f"{'SUCCESS' if success else 'FAILED'}: {message}")
        self.progress_label.setText(message)

    def _append_log(self, msg: str):
        self.log_text.appendPlainText(msg)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
