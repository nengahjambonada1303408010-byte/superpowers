from __future__ import annotations

import pytest
from tests.conftest import SAMPLE_VULNERABLE_PHP, SAMPLE_ATTACK_LOG


def test_health(test_client):
    client, _ = test_client
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_missing_api_key(test_client):
    client, _ = test_client
    resp = client.post("/api/v1/scan", json={"target_content": "test", "target_type": "code"})
    assert resp.status_code == 401


def test_scan_code(test_client):
    client, mock_orc = test_client
    resp = client.post(
        "/api/v1/scan",
        headers={"X-API-Key": "test-service-key"},
        json={"target_type": "code", "target_content": SAMPLE_VULNERABLE_PHP, "scan_profile": "full"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "risk_score" in data
    assert "findings" in data
    mock_orc.run_scan.assert_called_once()


def test_scan_url(test_client):
    client, mock_orc = test_client
    resp = client.post(
        "/api/v1/scan",
        headers={"X-API-Key": "test-service-key"},
        json={"target_type": "url", "target_url": "https://example.com", "scan_profile": "standard"},
    )
    assert resp.status_code == 200
    mock_orc.run_scan.assert_called_once()


def test_monitor_logs(test_client):
    client, mock_orc = test_client
    resp = client.post(
        "/api/v1/monitor",
        headers={"X-API-Key": "test-service-key"},
        json={"log_content": SAMPLE_ATTACK_LOG, "log_format": "apache"},
    )
    assert resp.status_code == 200
    mock_orc.run_monitor.assert_called_once()


def test_pentest(test_client):
    client, mock_orc = test_client
    resp = client.post(
        "/api/v1/pentest",
        headers={"X-API-Key": "test-service-key"},
        json={"target_url": "https://example.com", "scope": ["https://example.com/*"]},
    )
    assert resp.status_code == 200
    mock_orc.run_pentest.assert_called_once()


def test_full_audit(test_client):
    client, mock_orc = test_client
    resp = client.post(
        "/api/v1/audit",
        headers={"X-API-Key": "test-service-key"},
        json={
            "target_type": "full",
            "target_url": "https://example.com",
            "target_content": SAMPLE_VULNERABLE_PHP,
            "log_content": SAMPLE_ATTACK_LOG,
            "scope": ["https://example.com/*"],
            "scan_profile": "full",
        },
    )
    assert resp.status_code == 200
    mock_orc.run_full_audit.assert_called_once()


def test_scan_file_upload(test_client):
    client, mock_orc = test_client
    resp = client.post(
        "/api/v1/scan/upload",
        headers={"X-API-Key": "test-service-key"},
        files={"file": ("vulnerable.php", SAMPLE_VULNERABLE_PHP.encode(), "text/plain")},
        data={"scan_profile": "full"},
    )
    assert resp.status_code == 200
    mock_orc.run_scan.assert_called_once()
