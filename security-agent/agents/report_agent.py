from __future__ import annotations

import json
import re
import anthropic

from core.models import AgentResult, Finding, SecurityReport
from agents.base_agent import BaseAgent


class ReportAgent(BaseAgent):
    agent_type = "report"
    prompt_file = "report_agent.md"

    def __init__(self, client: anthropic.AsyncAnthropic):
        super().__init__(client)
        self.tool_schemas = []

    async def run(self, input_data: dict) -> AgentResult:
        agent_results: list[AgentResult] = input_data.get("agent_results", [])
        target = input_data.get("target", "")

        all_findings = []
        total_tokens: dict[str, int] = {}
        for result in agent_results:
            all_findings.extend(result.findings)
            for k, v in result.tokens_used.items():
                total_tokens[k] = total_tokens.get(k, 0) + v

        findings_json = json.dumps(
            [f.model_dump() for f in all_findings], indent=2
        )

        message = (
            f"Target assessed: {target or 'Not specified'}\n\n"
            f"Total findings from all agents: {len(all_findings)}\n\n"
            f"Findings data:\n```json\n{findings_json[:80000]}\n```\n\n"
            "Generate a complete security report including the JSON block and human-readable Markdown report."
        )

        try:
            response_text, usage = await self._run_agent_loop(message)

            report = self._build_report(response_text, all_findings, target)
            total_tokens_combined = {k: total_tokens.get(k, 0) + usage.get(k, 0) for k in set(total_tokens) | set(usage)}
            report.tokens_used = total_tokens_combined

            return AgentResult(
                agent_type=self.agent_type,
                findings=all_findings,
                metadata={"report": report.model_dump()},
                tokens_used=usage,
            )
        except Exception as exc:
            return AgentResult(agent_type=self.agent_type, error=str(exc))

    def _build_report(self, response_text: str, findings: list[Finding], target: str) -> SecurityReport:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        json_data: dict = {}
        if match:
            try:
                json_data = json.loads(match.group(1))
            except Exception:
                pass

        human_readable = response_text
        if match:
            human_readable = response_text[match.end():].strip()

        severity_dist: dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for f in findings:
            severity_dist[f.severity] = severity_dist.get(f.severity, 0) + 1

        risk_score = json_data.get("risk_score", self._calc_risk_score(findings))

        return SecurityReport(
            target=target,
            risk_score=risk_score,
            executive_summary=json_data.get("executive_summary", ""),
            findings=findings,
            severity_distribution=severity_dist,
            recommendations=json_data.get("recommendations", []),
            human_readable=human_readable,
        )

    def _calc_risk_score(self, findings: list[Finding]) -> float:
        if not findings:
            return 0.0
        weights = {"CRITICAL": 1.0, "HIGH": 0.7, "MEDIUM": 0.4, "LOW": 0.2, "INFO": 0.05}
        weighted = sum(weights.get(f.severity, 0) for f in findings)
        max_cvss = max((f.cvss_score for f in findings), default=0.0)
        score = min(10.0, weighted / max(1, len(findings)) * 3.0 + max_cvss * 0.5)
        return round(score, 1)
