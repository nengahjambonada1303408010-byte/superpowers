from __future__ import annotations

import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


SAMPLE_VULNERABLE_PHP = """<?php
$id = $_GET['id'];
$query = "SELECT * FROM users WHERE id=" . $id;
$result = mysql_query($query);

$username = $_POST['username'];
echo "<div>Welcome " . $username . "</div>";

$pass = md5($_POST['password']);
?>"""

SAMPLE_ATTACK_LOG = """192.168.1.100 - - [27/May/2026:10:00:01 +0000] "GET /login?id=1+OR+1=1-- HTTP/1.1" 200 1234
192.168.1.100 - - [27/May/2026:10:00:02 +0000] "GET /search?q=<script>alert(1)</script> HTTP/1.1" 200 567
10.0.0.1 - - [27/May/2026:10:00:03 +0000] "GET /index.html HTTP/1.1" 200 4321
192.168.1.100 - - [27/May/2026:10:00:04 +0000] "GET /../../etc/passwd HTTP/1.1" 403 0
"""

MOCK_SCAN_RESPONSE = {
    "findings": [
        {
            "agent_type": "vulnerability_scanner",
            "owasp_category": "A03:2021",
            "title": "SQL Injection in GET parameter",
            "description": "User input concatenated directly into SQL query.",
            "severity": "CRITICAL",
            "cvss_score": 9.8,
            "evidence": "SELECT * FROM users WHERE id=\" . $id",
            "file_path": "test.php",
            "line_number": 3,
            "remediation": "Use prepared statements.",
        }
    ]
}


def make_mock_message(text: str, tool_calls: list | None = None):
    msg = MagicMock()
    msg.stop_reason = "end_turn" if not tool_calls else "tool_use"
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = text
    msg.content = [text_block]
    if tool_calls:
        msg.stop_reason = "tool_use"
        msg.content = tool_calls
    usage = MagicMock()
    usage.input_tokens = 100
    usage.output_tokens = 200
    usage.cache_read_input_tokens = 0
    msg.usage = usage
    return msg


@pytest.fixture
def mock_anthropic_client():
    client = AsyncMock()
    response_text = f"Analysis complete.\n```json\n{json.dumps(MOCK_SCAN_RESPONSE)}\n```"
    client.messages.create = AsyncMock(return_value=make_mock_message(response_text))
    return client


@pytest.fixture
def test_client():
    with patch("core.config.settings.anthropic_api_key", "test-key"):
        with patch("core.config.settings.service_api_key", "test-service-key"):
            from main import app
            from core.orchestrator import Orchestrator
            mock_orc = AsyncMock(spec=Orchestrator)
            from core.models import SecurityReport
            mock_orc.run_scan = AsyncMock(return_value=SecurityReport(risk_score=9.8, executive_summary="Critical SQL injection found."))
            mock_orc.run_monitor = AsyncMock(return_value=SecurityReport(risk_score=7.0, executive_summary="Attack patterns detected."))
            mock_orc.run_pentest = AsyncMock(return_value=SecurityReport(risk_score=6.0, executive_summary="Missing security headers."))
            mock_orc.run_full_audit = AsyncMock(return_value=SecurityReport(risk_score=9.5, executive_summary="Multiple critical issues found."))
            import main
            main.orchestrator = mock_orc
            yield TestClient(app), mock_orc
