from pathlib import Path

from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QListWidget,
                              QPushButton, QTextEdit, QDialog, QLabel)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

SKILLS_DIR = Path(__file__).parent.parent.parent / "agent" / "skills"


class SkillManagerPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Hermes Skill Manager", parent)
        self._setup_ui()
        self.refresh_skills()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self._list = QListWidget()
        self._list.setFont(QFont("Consolas", 10))
        layout.addWidget(self._list)

        btn_layout = QHBoxLayout()
        view_btn = QPushButton("View")
        view_btn.clicked.connect(self._view_skill)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_skills)
        open_btn = QPushButton("Open Folder")
        open_btn.clicked.connect(self._open_folder)
        btn_layout.addWidget(view_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(open_btn)
        layout.addLayout(btn_layout)

        self._legend = QLabel("* = created by Hermes Agent autonomously")
        self._legend.setStyleSheet("color: #888; font-size: 9px;")
        layout.addWidget(self._legend)

    def refresh_skills(self):
        self._list.clear()
        base_skills = {"technical_analysis", "risk_assessment", "trade_execution",
                       "profit_compounding", "market_session"}
        for skill_file in sorted(SKILLS_DIR.glob("*.md")):
            name = skill_file.stem
            marker = "" if name in base_skills else " *"
            self._list.addItem(f"✓ {name}{marker}")

    def _view_skill(self):
        item = self._list.currentItem()
        if not item:
            return
        name = item.text().replace("✓ ", "").replace(" *", "").strip()
        path = SKILLS_DIR / f"{name}.md"
        if not path.exists():
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Skill: {name}")
        dialog.resize(600, 500)
        layout = QVBoxLayout(dialog)
        editor = QTextEdit()
        editor.setReadOnly(True)
        editor.setFont(QFont("Consolas", 10))
        editor.setPlainText(path.read_text(encoding="utf-8"))
        layout.addWidget(editor)
        dialog.exec_()

    def _open_folder(self):
        import subprocess, sys
        if sys.platform == "win32":
            subprocess.Popen(["explorer", str(SKILLS_DIR)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(SKILLS_DIR)])
        else:
            subprocess.Popen(["xdg-open", str(SKILLS_DIR)])
