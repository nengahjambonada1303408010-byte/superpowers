"""
Settings Tab - GUI config editor.
"""
import yaml
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox,
    QFormLayout, QComboBox, QCheckBox, QTabWidget, QMessageBox
)
from PyQt5.QtCore import pyqtSignal
from loguru import logger

CONFIG_FILE = Path("config.yaml")


class SettingsTab(QWidget):
    config_saved = pyqtSignal(dict)

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        inner_tabs = QTabWidget()

        # MT5 tab
        mt5_widget = QWidget()
        mt5_form = QFormLayout(mt5_widget)
        self.login_edit = QLineEdit(str(self.config.get("mt5", {}).get("login", "")))
        self.password_edit = QLineEdit(self.config.get("mt5", {}).get("password", ""))
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.server_edit = QLineEdit(self.config.get("mt5", {}).get("server", ""))
        self.path_edit = QLineEdit(self.config.get("mt5", {}).get("path", ""))
        mt5_form.addRow("Login:", self.login_edit)
        mt5_form.addRow("Password:", self.password_edit)
        mt5_form.addRow("Server:", self.server_edit)
        mt5_form.addRow("Terminal Path:", self.path_edit)
        inner_tabs.addTab(mt5_widget, "MT5 Connection")

        # Risk tab
        risk_widget = QWidget()
        risk_form = QFormLayout(risk_widget)
        risk_cfg = self.config.get("risk", {})
        self.lot_mode_combo = QComboBox()
        self.lot_mode_combo.addItems(["percent_balance", "fixed_lot"])
        self.lot_mode_combo.setCurrentText(risk_cfg.get("mode", "percent_balance"))
        self.fixed_lot_spin = QDoubleSpinBox()
        self.fixed_lot_spin.setRange(0.01, 100)
        self.fixed_lot_spin.setSingleStep(0.01)
        self.fixed_lot_spin.setValue(risk_cfg.get("fixed_lot", 0.01))
        self.risk_pct_spin = QDoubleSpinBox()
        self.risk_pct_spin.setRange(0.1, 10.0)
        self.risk_pct_spin.setSingleStep(0.1)
        self.risk_pct_spin.setValue(risk_cfg.get("risk_percent", 1.0))
        self.max_dd_spin = QDoubleSpinBox()
        self.max_dd_spin.setRange(1.0, 50.0)
        self.max_dd_spin.setValue(risk_cfg.get("max_daily_loss_percent", 5.0))
        self.max_pos_spin = QSpinBox()
        self.max_pos_spin.setRange(1, 20)
        self.max_pos_spin.setValue(risk_cfg.get("max_open_positions", 3))
        risk_form.addRow("Lot Mode:", self.lot_mode_combo)
        risk_form.addRow("Fixed Lot:", self.fixed_lot_spin)
        risk_form.addRow("Risk % / trade:", self.risk_pct_spin)
        risk_form.addRow("Max Daily Loss %:", self.max_dd_spin)
        risk_form.addRow("Max Open Positions:", self.max_pos_spin)
        inner_tabs.addTab(risk_widget, "Risk Management")

        # Training tab
        train_widget = QWidget()
        train_form = QFormLayout(train_widget)
        train_cfg = self.config.get("training", {})
        self.years_spin = QSpinBox()
        self.years_spin.setRange(1, 20)
        self.years_spin.setValue(train_cfg.get("years_of_data", 5))
        self.pop_spin = QSpinBox()
        self.pop_spin.setRange(100, 200000)
        self.pop_spin.setSingleStep(1000)
        self.pop_spin.setValue(train_cfg.get("population_size", 10000))
        self.gen_spin = QSpinBox()
        self.gen_spin.setRange(10, 2000)
        self.gen_spin.setValue(train_cfg.get("max_generations", 200))
        self.retrain_spin = QSpinBox()
        self.retrain_spin.setRange(1, 365)
        self.retrain_spin.setValue(train_cfg.get("retrain_interval_days", 7))
        train_form.addRow("Years of Data:", self.years_spin)
        train_form.addRow("Population:", self.pop_spin)
        train_form.addRow("Max Generations:", self.gen_spin)
        train_form.addRow("Retrain Interval (days):", self.retrain_spin)
        inner_tabs.addTab(train_widget, "Training")

        layout.addWidget(inner_tabs)

        # Save button
        save_btn = QPushButton("💾  Save Settings")
        save_btn.setMinimumHeight(36)
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)
        layout.addStretch()

    def _save(self):
        self.config.setdefault("mt5", {})
        self.config["mt5"]["login"] = self.login_edit.text()
        self.config["mt5"]["password"] = self.password_edit.text()
        self.config["mt5"]["server"] = self.server_edit.text()
        self.config["mt5"]["path"] = self.path_edit.text()

        self.config.setdefault("risk", {})
        self.config["risk"]["mode"] = self.lot_mode_combo.currentText()
        self.config["risk"]["fixed_lot"] = self.fixed_lot_spin.value()
        self.config["risk"]["risk_percent"] = self.risk_pct_spin.value()
        self.config["risk"]["max_daily_loss_percent"] = self.max_dd_spin.value()
        self.config["risk"]["max_open_positions"] = self.max_pos_spin.value()

        self.config.setdefault("training", {})
        self.config["training"]["years_of_data"] = self.years_spin.value()
        self.config["training"]["population_size"] = self.pop_spin.value()
        self.config["training"]["max_generations"] = self.gen_spin.value()
        self.config["training"]["retrain_interval_days"] = self.retrain_spin.value()

        try:
            with open(CONFIG_FILE, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            logger.info("Config saved to config.yaml")
            QMessageBox.information(self, "Saved", "Settings saved successfully!")
            self.config_saved.emit(self.config)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")
