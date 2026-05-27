from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal, Any
from pydantic import BaseModel, Field


Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
TargetType = Literal["url", "code", "file", "full"]
LogFormat = Literal["apache", "nginx", "json", "auto"]
ScanProfile = Literal["quick", "standard", "full"]
JobStatusEnum = Literal["queued", "running", "completed", "failed"]


class Finding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent_type: str
    owasp_category: str = ""
    title: str
    description: str
    severity: Severity
    cvss_score: float = Field(0.0, ge=0.0, le=10.0)
    evidence: str = ""
    file_path: str = ""
    line_number: int | None = None
    endpoint: str = ""
    remediation: str = ""


class ScanRequest(BaseModel):
    target_type: TargetType = "code"
    target_url: str = ""
    target_content: str = ""
    filename: str = ""
    scan_profile: ScanProfile = "standard"
    scope: list[str] = Field(default_factory=list)


class MonitorRequest(BaseModel):
    log_content: str = ""
    log_format: LogFormat = "auto"
    time_window_seconds: int = 3600


class PentestRequest(BaseModel):
    target_url: str
    scope: list[str] = Field(default_factory=list)
    allowed_techniques: list[str] = Field(
        default_factory=lambda: ["headers", "xss_probe", "sqli_probe", "auth_check"]
    )


class DeepScanRequest(BaseModel):
    target_url: str = ""
    target_content: str = ""
    filename: str = ""
    log_content: str = ""
    scope: list[str] = Field(default_factory=list)
    stop_on_critical: bool = True
    max_rounds: int = Field(5, ge=1, le=10)


class AuditRequest(BaseModel):
    target_type: TargetType = "full"
    target_url: str = ""
    target_content: str = ""
    filename: str = ""
    log_content: str = ""
    log_format: LogFormat = "auto"
    scope: list[str] = Field(default_factory=list)
    scan_profile: ScanProfile = "standard"


class AgentResult(BaseModel):
    agent_type: str
    findings: list[Finding] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    tokens_used: dict[str, int] = Field(default_factory=dict)
    error: str = ""


class SecurityReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    target: str = ""
    risk_score: float = Field(0.0, ge=0.0, le=10.0)
    executive_summary: str = ""
    findings: list[Finding] = Field(default_factory=list)
    severity_distribution: dict[str, int] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    human_readable: str = ""
    tokens_used: dict[str, int] = Field(default_factory=dict)


class JobStatus(BaseModel):
    job_id: str
    status: JobStatusEnum = "queued"
    progress: int = Field(0, ge=0, le=100)
    result: SecurityReport | None = None
    error: str = ""
