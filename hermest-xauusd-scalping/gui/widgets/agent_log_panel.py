from datetime import datetime

from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QTextEdit, QHBoxLayout, QPushButton
from PyQt5.QtGui import QFont, QTextCursor, QColor
from PyQt5.QtCore import Qt


ACTION_COLORS = {
    "BUY": "#44ff44",
    "SELL": "#ff4444",
    "HOLD": "#ffaa00",
    "CLOSE_ALL": "#ff44ff",
}


class AgentLogPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Hermes Agent Log", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Consolas", 9))
        self._log.setStyleSheet("background: #0d1117; color: #c9d1d9;")
        layout.addWidget(self._log)

        btn_layout = QHBoxLayout()
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._log.clear)
        save_btn = QPushButton("Save Log")
        save_btn.clicked.connect(self._save_log)
        btn_layout.addWidget(clear_btn)
        btn_layout.addWidget(save_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def add_entry(self, action: str, reasoning: str, confidence: float):
        ts = datetime.now().strftime("%H:%M:%S")
        color = ACTION_COLORS.get(action.upper(), "#ffffff")
        html = (
            f'<span style="color:#888">[{ts}]</span> '
            f'<span style="color:{color}; font-weight:bold">ACTION: {action}</span> '
            f'<span style="color:#aaa">(conf: {confidence:.2f})</span><br>'
            f'<span style="color:#c9d1d9; margin-left:10px">{reasoning[:300]}</span>'
            f'<hr style="border-color:#30363d; margin:4px 0;">'
        )
        self._log.moveCursor(QTextCursor.End)
        self._log.insertHtml(html)
        self._log.moveCursor(QTextCursor.End)

    def add_status(self, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color:#888">[{ts}] {message}</span><br>'
        self._log.moveCursor(QTextCursor.End)
        self._log.insertHtml(html)
        self._log.moveCursor(QTextCursor.End)

    def _save_log(self):
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "Save Log", "agent_log.txt", "Text Files (*.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._log.toPlainText())
