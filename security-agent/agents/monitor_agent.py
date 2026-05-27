from __future__ import annotations

import anthropic

from core.models import AgentResult
from agents.base_agent import BaseAgent
from tools import log_parser


class MonitorAgent(BaseAgent):
    agent_type = "monitor"
    prompt_file = "monitor_agent.md"

    def __init__(self, client: anthropic.AsyncAnthropic):
        super().__init__(client)
        self.tool_schemas = log_parser.TOOL_SCHEMAS

    async def _call_tool(self, tool_name: str, tool_input: dict) -> str:
        return log_parser.dispatch(tool_name, tool_input)

    async def run(self, input_data: dict) -> AgentResult:
        log_content = input_data.get("log_content", "")
        log_format = input_data.get("log_format", "auto")

        if not log_content:
            return AgentResult(agent_type=self.agent_type, error="No log content provided for monitoring.")

        message = (
            f"Analyze the following HTTP access logs for security threats and attack patterns.\n"
            f"Log format: {log_format}\n\n"
            f"Use the parse_logs tool to process these logs, then report all findings.\n\n"
            f"Log content:\n```\n{log_content[:100000]}\n```"
        )

        try:
            response_text, usage = await self._run_agent_loop(message)
            findings = self._parse_findings(response_text)
            return AgentResult(
                agent_type=self.agent_type,
                findings=findings,
                metadata={"response": response_text[:500]},
                tokens_used=usage,
            )
        except Exception as exc:
            return AgentResult(agent_type=self.agent_type, error=str(exc))
