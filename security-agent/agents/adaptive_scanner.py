from __future__ import annotations

import json
import re
import anthropic

from core.config import settings
from core.models import AgentResult, Finding
from agents.base_agent import BaseAgent
from tools import http_tools, file_tools
from tools.tool_forge import ToolForge, SkillForge, GENERATE_TOOL_SCHEMA, CREATE_SKILL_SCHEMA


class AdaptiveScanner(BaseAgent):
    """Self-evolving scanner: generates its own tools and skills during a scan."""

    agent_type = "adaptive_scanner"
    prompt_file = "adaptive_scanner.md"

    def __init__(self, client: anthropic.AsyncAnthropic, tool_forge: ToolForge, skill_forge: SkillForge):
        super().__init__(client)
        self.tool_forge = tool_forge
        self.skill_forge = skill_forge
        self.max_iterations = settings.max_deep_scan_iterations
        self._scope: list[str] = []

        self.tool_schemas = (
            [GENERATE_TOOL_SCHEMA, CREATE_SKILL_SCHEMA]
            + http_tools.TOOL_SCHEMAS
            + file_tools.TOOL_SCHEMAS
        )

    def _build_system(self) -> list[dict]:
        registry_context = ""
        existing = self.tool_forge.list_tools()
        existing_skills = self.skill_forge.list_skills()
        if existing:
            registry_context = (
                f"\n\n## Already Generated Tools This Session\n"
                + "\n".join(f"- {t['name']}: {t['description']}" for t in existing)
            )
        if existing_skills:
            registry_context += (
                f"\n\n## Already Created Skills This Session\n"
                + "\n".join(f"- {s}" for s in existing_skills)
            )

        system_text = self.system_prompt + registry_context
        return [{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}]

    async def _call_tool(self, tool_name: str, tool_input: dict) -> str:
        url = tool_input.get("url", tool_input.get("base_url", tool_input.get("target_url", "")))
        if url and self._scope:
            from urllib.parse import urlparse
            netloc = urlparse(url).netloc
            in_scope = any(urlparse(s.rstrip("*")).netloc == netloc for s in self._scope)
            if not in_scope:
                return json.dumps({"error": "URL outside declared scope."})

        if tool_name == "generate_and_run_tool":
            return await self.tool_forge.generate_and_run(
                tool_input["tool_description"],
                tool_input.get("target_url", ""),
                tool_input.get("extra_args", {}),
            )

        if tool_name == "create_specialized_skill":
            return await self.skill_forge.create_skill(
                tool_input["technology"],
                tool_input["target_url"],
                tool_input.get("context", ""),
            )

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

        prev_ctx = ""
        if previous_findings:
            crits = sum(1 for f in previous_findings if f.get("severity") == "CRITICAL")
            highs = sum(1 for f in previous_findings if f.get("severity") == "HIGH")
            prev_ctx = (
                f"\n\n---\n## Context from Round {round_number - 1}\n"
                f"Already confirmed: {crits} CRITICAL, {highs} HIGH findings.\n"
                f"Do NOT re-test already confirmed vulnerabilities. Go DEEPER on new vectors.\n"
                f"Previous findings:\n```json\n{json.dumps(previous_findings[:8], indent=2)}\n```"
            )

        if target_url:
            msg = (
                f"**Round {round_number} — Adaptive Security Assessment**\n"
                f"Target: {target_url}\n"
                f"Scope: {', '.join(scope) or target_url}\n\n"
                f"Execute ALL 5 phases. Generate custom tools freely. Create skills for any "
                f"technology you detect. Do not stop until CRITICAL found or all vectors exhausted."
                f"{prev_ctx}"
            )
        elif target_content:
            msg = (
                f"**Round {round_number} — Adaptive Code Security Analysis**\n"
                f"File: {input_data.get('filename', 'code')}\n\n"
                f"```\n{target_content[:60000]}\n```\n\n"
                f"Analyze exhaustively. Generate tools for any dynamic checks needed."
                f"{prev_ctx}"
            )
        else:
            return AgentResult(agent_type=self.agent_type, error="No target provided.")

        try:
            response_text, usage = await self._run_agent_loop(msg)
            findings = self._parse_findings(response_text)
            meta = self._parse_metadata(response_text)
            meta["tools_in_registry"] = len(self.tool_forge.list_tools())
            meta["skills_in_registry"] = self.skill_forge.list_skills()
            meta["round"] = round_number
            return AgentResult(
                agent_type=self.agent_type,
                findings=findings,
                metadata=meta,
                tokens_used=usage,
            )
        except Exception as exc:
            return AgentResult(agent_type=self.agent_type, error=str(exc))

    def _parse_metadata(self, text: str) -> dict:
        meta: dict = {}
        for key in ("tools_generated", "technologies_detected", "skills_created"):
            m = re.search(rf'"{key}"\s*:\s*(\d+|\[[^\]]*\])', text)
            if m:
                try:
                    meta[key] = json.loads(m.group(1))
                except Exception:
                    meta[key] = m.group(1)

        summary_m = re.search(r'"scan_summary"\s*:\s*(\{[^}]+\})', text, re.DOTALL)
        if summary_m:
            try:
                meta["scan_summary"] = json.loads(summary_m.group(1))
                meta["vectors_exhausted"] = meta["scan_summary"].get("vectors_exhausted", False)
            except Exception:
                pass
        return meta
