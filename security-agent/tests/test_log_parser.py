import json
import pytest
from tools.log_parser import parse_logs


APACHE_LOG = """192.168.1.1 - - [27/May/2026:10:00:01 +0000] "GET /login?id=1+OR+1=1-- HTTP/1.1" 200 1234
10.0.0.5 - - [27/May/2026:10:00:02 +0000] "GET /index.html HTTP/1.1" 200 4321
192.168.1.1 - - [27/May/2026:10:00:03 +0000] "GET /search?q=<script>alert(1)</script> HTTP/1.1" 200 567
192.168.1.1 - - [27/May/2026:10:00:04 +0000] "GET /../../etc/passwd HTTP/1.1" 403 0
"""


def test_parse_apache_log_detects_sqli():
    result = json.loads(parse_logs(APACHE_LOG, "apache"))
    attack_types = [a["type"] for a in result["attacks_detected"]]
    assert "SQL Injection" in attack_types


def test_parse_apache_log_detects_xss():
    result = json.loads(parse_logs(APACHE_LOG, "apache"))
    attack_types = [a["type"] for a in result["attacks_detected"]]
    assert "XSS Attempt" in attack_types


def test_parse_apache_log_detects_path_traversal():
    result = json.loads(parse_logs(APACHE_LOG, "apache"))
    attack_types = [a["type"] for a in result["attacks_detected"]]
    assert "Path Traversal" in attack_types


def test_auto_format_detection():
    result = json.loads(parse_logs(APACHE_LOG, "auto"))
    assert result["format_detected"] in ("apache", "nginx")
    assert result["parsed_entries"] > 0


def test_clean_log_no_attacks():
    clean_log = '10.0.0.1 - - [27/May/2026:10:00:01 +0000] "GET /index.html HTTP/1.1" 200 1234\n'
    result = json.loads(parse_logs(clean_log, "apache"))
    assert result["attack_count"] == 0
