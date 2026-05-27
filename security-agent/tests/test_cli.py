from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile

from core.models import SecurityReport


MOCK_REPORT = SecurityReport(
    target="https://example.com",
    risk_score=8.5,
    executive_summary="Critical SQL injection found.",
    severity_distribution={"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 0, "INFO": 0},
    findings=[],
    recommendations=["Fix SQL injection immediately"],
)


def test_cli_help(capsys):
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "cli.py", "--help"],
        capture_output=True, text=True, cwd="."
    )
    assert result.returncode == 0
    assert "scan" in result.stdout
    assert "monitor" in result.stdout
    assert "adaptive" in result.stdout


def test_cli_scan_help(capsys):
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "cli.py", "scan", "--help"],
        capture_output=True, text=True, cwd="."
    )
    assert result.returncode == 0
    assert "--url" in result.stdout
    assert "--file" in result.stdout


def test_save_report_creates_files():
    from pathlib import Path as P
    # Ensure the reports directory exists before calling save_report
    reports_dir = P.home() / "security-reports"
    reports_dir.mkdir(exist_ok=True)

    import sys
    sys.path.insert(0, str(P(__file__).parent.parent))
    import importlib, cli as cli_mod
    importlib.reload(cli_mod)

    report = MOCK_REPORT.model_dump()
    path = cli_mod.save_report(report, "https://example.com", "test")
    json_file = P(path + ".json")
    md_file   = P(path + ".md")
    assert json_file.exists()
    assert md_file.exists()
    data = json.loads(json_file.read_text())
    assert data["risk_score"] == 8.5
    json_file.unlink(missing_ok=True)
    md_file.unlink(missing_ok=True)


def test_cli_no_api_key_exits():
    import subprocess, sys, os
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    env.pop("ANTHROPIC_API_KEY", None)
    result = subprocess.run(
        [sys.executable, "cli.py", "scan", "--url", "https://example.com"],
        capture_output=True, text=True, cwd=".", env=env
    )
    assert result.returncode == 1
    assert "ANTHROPIC_API_KEY" in result.stdout or "ANTHROPIC_API_KEY" in result.stderr
