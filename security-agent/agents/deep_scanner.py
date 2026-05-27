from __future__ import annotations

import json
import re
import anthropic

from core.config import settings
from core.models import AgentResult, Finding
from agents.base_agent import BaseAgent
from tools import http_tools, file_tools


class DeepScanAgent(BaseAgent):
    agent_type = "deep_scanner"
    prompt_file = "deep_scanner.md"

    def __init__(self, client: anthropic.AsyncAnthropic):
        super().__init__(client)
        self.max_iterations = settings.max_deep_scan_iterations
        self.tool_schemas = http_tools.TOOL_SCHEMAS + file_tools.TOOL_SCHEMAS
        self._scope: list[str] = []

    async def _call_tool(self, tool_name: str, tool_input: dict) -> str:
        url = tool_input.get("url", tool_input.get("base_url", ""))
        if url and self._scope:
            from urllib.parse import urlparse
            base = urlparse(url).netloc
            allowed = any(urlparse(s.rstrip("*")).netloc == base for s in self._scope)
            if not allowed:
                return json.dumps({"error": "URL outside declared scope. Skipping."})

        if tool_name in {s["name"] for s in http_tools.TOOL_SCHEMAS}:
            return await http_tools.dispatch_async(tool_name, tool_input)
        return file_tools.dispatch(tool_name, tool_input)

    async def run(self, input_data: dict) -> AgentResult:
        target_url = input_data.get("target_url", "")
        target_content = input_data.get("target_content", "")
        scope = input_data.get("scope", [target_url] if target_url else [])
        previous_findings: list[dict] = input_data.get("previous_findings", [])
        round_number: int = input_data.get("round_number", 1)

        self._scope = scope

        prev_summary = ""
        if previous_findings:
            critical_count = sum(1 for f in previous_findings if f.get("severity") == "CRITICAL")
            high_count = sum(1 for f in previous_findings if f.get("severity") == "HIGH")
            prev_summary = (
                f"\n\n## Previous Findings (Round {round_number - 1})\n"
                f"Already found: {critical_count} CRITICAL, {high_count} HIGH, {len(previous_findings)} total.\n"
                f"Details:\n```json\n{json.dumps(previous_findings[:10], indent=2)}\n```\n\n"
                f"Continue deeper. Test ALL vectors not yet covered above."
            )

        if target_url:
            message = (
                f"Round {round_number} — Deep security assessment of: {target_url}\n"
                f"Scope: {', '.join(scope)}\n"
                f"Execute ALL 5 phases of the scan sequence systematically."
                f"{prev_summary}"
            )
        elif target_content:
            message = (
                f"Round {round_number} — Deep code security analysis.\n"
                f"Filename: {input_data.get('filename', 'code')}\n\n"
                f"```\n{target_content[:60000]}\n```\n\n"
                f"Analyze exhaustively. Test every code path for every OWASP category."
                f"{prev_summary}"
            )
        else:
            return AgentResult(agent_type=self.agent_type, error="No target provided.")

        try:
            response_text, usage = await self._run_agent_loop(message)
            findings = self._parse_findings(response_text)
            scan_summary = self._parse_scan_summary(response_text)
            return AgentResult(
                agent_type=self.agent_type,
                findings=findings,
                metadata={
                    "scan_summary": scan_summary,
                    "round": round_number,
                    "vectors_exhausted": scan_summary.get("vectors_exhausted", False),
                },
                tokens_used=usage,
            )
        except Exception as exc:
            return AgentResult(agent_type=self.agent_type, error=str(exc))

    def _parse_scan_summary(self, text: str) -> dict:
        match = re.search(r'"scan_summary"\s*:\s*(\{[^}]+\})', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        return {}
