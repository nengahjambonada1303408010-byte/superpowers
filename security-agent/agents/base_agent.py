from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import anthropic

from core.config import settings
from core.models import AgentResult, Finding


class BaseAgent(ABC):
    agent_type: str = "base"
    prompt_file: str = ""
    max_iterations: int = settings.max_agent_iterations

    def __init__(self, client: anthropic.AsyncAnthropic):
        self.client = client
        self.system_prompt = self._load_prompt()
        self.tool_schemas: list[dict] = []

    def _load_prompt(self) -> str:
        if not self.prompt_file:
            return ""
        path = Path(__file__).parent.parent / "prompts" / self.prompt_file
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def _build_system(self) -> list[dict]:
        return [{"type": "text", "text": self.system_prompt, "cache_control": {"type": "ephemeral"}}]

    async def _run_agent_loop(self, user_message: str) -> tuple[str, dict[str, int]]:
        conversation: list[dict[str, Any]] = [{"role": "user", "content": user_message}]
        total_usage: dict[str, int] = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0}

        for _ in range(self.max_iterations):
            response = await self.client.messages.create(
                model=settings.model,
                max_tokens=settings.max_tokens,
                system=self._build_system(),
                tools=self.tool_schemas,
                messages=conversation,
            )

            usage = response.usage
            total_usage["input_tokens"] += getattr(usage, "input_tokens", 0)
            total_usage["output_tokens"] += getattr(usage, "output_tokens", 0)
            total_usage["cache_read_input_tokens"] += getattr(usage, "cache_read_input_tokens", 0)

            if response.stop_reason == "end_turn":
                final_text = "".join(
                    block.text for block in response.content if hasattr(block, "text")
                )
                return final_text, total_usage

            if response.stop_reason == "tool_use":
                tool_results = await self._execute_tools(response.content)
                conversation.append({"role": "assistant", "content": response.content})
                conversation.append({"role": "user", "content": tool_results})
                continue

            break

        final_text = "".join(
            block.text for block in response.content if hasattr(block, "text")
        )
        return final_text, total_usage

    async def _execute_tools(self, content_blocks: list) -> list[dict]:
        results = []
        for block in content_blocks:
            if block.type != "tool_use":
                continue
            result_text = await self._call_tool(block.name, block.input)
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_text,
            })
        return results

    async def _call_tool(self, tool_name: str, tool_input: dict) -> str:
        return json.dumps({"error": f"Tool '{tool_name}' not implemented in {self.agent_type}"})

    def _parse_findings(self, text: str) -> list[Finding]:
        match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
        if not match:
            match = re.search(r'(\{"findings".*?\}|\[.*?\])', text, re.DOTALL)
        if not match:
            return []
        try:
            data = json.loads(match.group(1))
            raw_findings = data if isinstance(data, list) else data.get("findings", [])
            findings = []
            for item in raw_findings:
                item.setdefault("agent_type", self.agent_type)
                item.setdefault("severity", "INFO")
                try:
                    findings.append(Finding(**item))
                except Exception:
                    pass
            return findings
        except Exception:
            return []

    @abstractmethod
    async def run(self, input_data: dict) -> AgentResult:
        pass
