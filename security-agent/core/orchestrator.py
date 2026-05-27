from __future__ import annotations

import asyncio
import uuid
from typing import Any

import anthropic

from core.config import settings
from core.models import (
    AgentResult, AuditRequest, JobStatus, MonitorRequest,
    PentestRequest, ScanRequest, SecurityReport,
)
from agents.vulnerability_scanner import VulnerabilityAgent
from agents.monitor_agent import MonitorAgent
from agents.pentest_agent import PentestAgent
from agents.report_agent import ReportAgent


class Orchestrator:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.vuln_agent = VulnerabilityAgent(self.client)
        self.monitor_agent = MonitorAgent(self.client)
        self.pentest_agent = PentestAgent(self.client)
        self.report_agent = ReportAgent(self.client)
        self._jobs: dict[str, JobStatus] = {}

    async def run_full_audit(self, request: AuditRequest) -> SecurityReport:
        target = request.target_url or request.filename or "provided content"

        scan_input: dict[str, Any] = {
            "target_type": request.target_type,
            "target_url": request.target_url,
            "target_content": request.target_content,
            "filename": request.filename,
            "scan_profile": request.scan_profile,
            "scope": request.scope,
        }
        monitor_input: dict[str, Any] = {
            "log_content": request.log_content,
            "log_format": request.log_format,
        }
        pentest_input: dict[str, Any] = {
            "target_url": request.target_url,
            "scope": request.scope or ([request.target_url] if request.target_url else []),
        }

        tasks = []
        if scan_input.get("target_content") or scan_input.get("target_url"):
            tasks.append(self.vuln_agent.run(scan_input))
        if monitor_input.get("log_content"):
            tasks.append(self.monitor_agent.run(monitor_input))
        if pentest_input.get("target_url"):
            tasks.append(self.pentest_agent.run(pentest_input))

        if not tasks:
            return SecurityReport(target=target, executive_summary="No input provided for analysis.")

        agent_results: list[AgentResult] = await asyncio.gather(*tasks)

        report_result = await self.report_agent.run({
            "agent_results": list(agent_results),
            "target": target,
        })
        report: SecurityReport = report_result.metadata.get("report", SecurityReport(target=target))
        if isinstance(report, dict):
            report = SecurityReport(**report)
        report.target = target
        return report

    async def run_scan(self, request: ScanRequest) -> SecurityReport:
        result = await self.vuln_agent.run(request.model_dump())
        report_result = await self.report_agent.run({"agent_results": [result], "target": request.target_url or request.filename})
        report = report_result.metadata.get("report", SecurityReport())
        if isinstance(report, dict):
            report = SecurityReport(**report)
        return report

    async def run_monitor(self, request: MonitorRequest) -> SecurityReport:
        result = await self.monitor_agent.run(request.model_dump())
        report_result = await self.report_agent.run({"agent_results": [result], "target": "log analysis"})
        report = report_result.metadata.get("report", SecurityReport())
        if isinstance(report, dict):
            report = SecurityReport(**report)
        return report

    async def run_pentest(self, request: PentestRequest) -> SecurityReport:
        result = await self.pentest_agent.run(request.model_dump())
        report_result = await self.report_agent.run({"agent_results": [result], "target": request.target_url})
        report = report_result.metadata.get("report", SecurityReport())
        if isinstance(report, dict):
            report = SecurityReport(**report)
        return report

    def create_job(self) -> str:
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = JobStatus(job_id=job_id, status="queued")
        return job_id

    def get_job(self, job_id: str) -> JobStatus | None:
        return self._jobs.get(job_id)

    def update_job(self, job_id: str, **kwargs: Any) -> None:
        job = self._jobs.get(job_id)
        if job:
            for k, v in kwargs.items():
                setattr(job, k, v)

    async def run_audit_async(self, job_id: str, request: AuditRequest) -> None:
        self.update_job(job_id, status="running", progress=10)
        try:
            report = await self.run_full_audit(request)
            self.update_job(job_id, status="completed", progress=100, result=report)
        except Exception as exc:
            self.update_job(job_id, status="failed", error=str(exc))
