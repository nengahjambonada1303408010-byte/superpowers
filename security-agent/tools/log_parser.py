import re
import json
from typing import Any

TOOL_SCHEMAS = [
    {
        "name": "parse_logs",
        "description": "Parse and analyze HTTP access logs (Apache, Nginx, or JSON format) to detect attack patterns.",
        "input_schema": {
            "type": "object",
            "properties": {
                "log_content": {"type": "string", "description": "Raw log content (multiple lines)"},
                "log_format": {
                    "type": "string",
                    "enum": ["apache", "nginx", "json", "auto"],
                    "description": "Log format. Use 'auto' to detect automatically.",
                },
            },
            "required": ["log_content"],
        },
    },
]

APACHE_PATTERN = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<method>\S+) (?P<path>\S+) \S+" (?P<status>\d+) (?P<size>\S+)'
)
NGINX_PATTERN = re.compile(
    r'(?P<ip>\S+) - \S+ \[(?P<time>[^\]]+)\] "(?P<method>\S+) (?P<path>\S+) \S+" (?P<status>\d+) (?P<size>\d+)'
)

ATTACK_SIGNATURES: list[tuple[str, str, str]] = [
    (r"(?i)(union\s+select|select\s+.*\s+from|insert\s+into|drop\s+table|--|;--)", "SQL Injection", "CRITICAL"),
    (r"(?i)(<script|javascript:|onerror=|onload=|alert\(|document\.cookie)", "XSS Attempt", "HIGH"),
    (r"(?i)(\.\.\/|\.\.\\|%2e%2e%2f|%252e%252e)", "Path Traversal", "HIGH"),
    (r"(?i)(\/etc\/passwd|\/etc\/shadow|\/proc\/self)", "LFI Attempt", "CRITICAL"),
    (r"(?i)(cmd\.exe|\/bin\/sh|\/bin\/bash|powershell|wget\s|curl\s)", "Command Injection", "CRITICAL"),
    (r"(?i)(\.php\?.*=http|\.php\?.*=ftp|allow_url_include)", "RFI Attempt", "CRITICAL"),
    (r"(?i)(wp-admin|wp-login|xmlrpc\.php|phpmyadmin|adminer)", "Admin Panel Probe", "MEDIUM"),
    (r"(?i)(nikto|sqlmap|nmap|masscan|zgrab|dirbuster|gobuster)", "Scanner Detected", "HIGH"),
    (r"(?i)(\bor\b\s+1=1|\band\b\s+1=1|'\s+or\s+')", "Boolean SQLi", "CRITICAL"),
    (r"(?i)(sleep\(\d+\)|benchmark\(\d+)", "Time-based SQLi", "CRITICAL"),
]


def _detect_format(content: str) -> str:
    first_line = content.strip().split("\n")[0] if content.strip() else ""
    if first_line.startswith("{"):
        return "json"
    if re.match(r'\S+ - \S+ \[', first_line):
        return "apache"
    return "nginx"


def _parse_line(line: str, fmt: str) -> dict[str, Any] | None:
    pattern = APACHE_PATTERN if fmt == "apache" else NGINX_PATTERN
    m = pattern.match(line)
    if m:
        return m.groupdict()
    if fmt == "json":
        try:
            return json.loads(line)
        except Exception:
            return None
    return None


def parse_logs(log_content: str, log_format: str = "auto") -> str:
    if log_format == "auto":
        log_format = _detect_format(log_content)

    lines = [l for l in log_content.splitlines() if l.strip()]
    parsed: list[dict] = []
    for line in lines[:5000]:
        entry = _parse_line(line, log_format)
        if entry:
            parsed.append(entry)

    attacks: list[dict] = []
    ip_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}

    for entry in parsed:
        path = entry.get("path", "") + entry.get("request", "")
        ip = entry.get("ip", entry.get("remote_addr", ""))
        status = str(entry.get("status", entry.get("status_code", "")))

        if ip:
            ip_counts[ip] = ip_counts.get(ip, 0) + 1
        if status:
            status_counts[status] = status_counts.get(status, 0) + 1

        for pattern, attack_type, severity in ATTACK_SIGNATURES:
            if re.search(pattern, path):
                attacks.append({
                    "type": attack_type,
                    "severity": severity,
                    "ip": ip,
                    "path": path[:500],
                    "status": status,
                })
                break

    top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    suspicious_ips = [ip for ip, count in top_ips if count > 100]

    return json.dumps({
        "total_lines": len(lines),
        "parsed_entries": len(parsed),
        "format_detected": log_format,
        "attacks_detected": attacks[:50],
        "attack_count": len(attacks),
        "status_distribution": status_counts,
        "top_ips": [{"ip": ip, "requests": count} for ip, count in top_ips],
        "suspicious_ips": suspicious_ips,
    })


def dispatch(tool_name: str, tool_input: dict) -> str:
    if tool_name == "parse_logs":
        return parse_logs(
            tool_input["log_content"],
            tool_input.get("log_format", "auto"),
        )
    return json.dumps({"error": f"Unknown tool: {tool_name}"})
