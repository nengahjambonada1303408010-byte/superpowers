from __future__ import annotations

import ast
import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime

import httpx
import anthropic

GENERATE_TOOL_SCHEMA = {
    "name": "generate_and_run_tool",
    "description": (
        "Generate a brand-new Python security scanning tool for ANY check not covered by existing tools, "
        "then immediately execute it. Use this when you need to test: JWT weaknesses, GraphQL injection, "
        "OAuth flaws, WebSocket security, prototype pollution, deserialization bugs, SSRF via specific protocols, "
        "CMS-specific CVEs, API key exposure, business logic flaws, race conditions, or ANY custom check. "
        "Describe exactly what you need — the tool will be written and run automatically."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "tool_description": {
                "type": "string",
                "description": (
                    "Precise description of the security check. Include: what vulnerability to test, "
                    "what URL/endpoint, what request format, what response pattern indicates vulnerability."
                ),
            },
            "target_url": {"type": "string", "description": "Primary target URL for the tool"},
            "extra_args": {
                "type": "object",
                "description": "Additional parameters (headers, params, payloads, etc.)",
                "default": {},
            },
        },
        "required": ["tool_description"],
    },
}

CREATE_SKILL_SCHEMA = {
    "name": "create_specialized_skill",
    "description": (
        "Create a specialized security scanning strategy (skill) tailored to a specific technology, "
        "framework, or vulnerability class discovered. Use when you identify the target uses: "
        "WordPress, Joomla, Drupal, Laravel, Django, Rails, Spring Boot, GraphQL, gRPC, "
        "JWT auth, OAuth2, Kubernetes, Docker API, Elasticsearch, Redis, MongoDB exposed, etc. "
        "The skill will define exactly how to attack that technology."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "technology": {"type": "string", "description": "Technology/framework detected (e.g. 'WordPress 6.2', 'Laravel 10', 'GraphQL API')"},
            "target_url": {"type": "string"},
            "context": {"type": "string", "description": "Evidence that led to this detection"},
        },
        "required": ["technology", "target_url"],
    },
}

FORBIDDEN_PATTERNS = [
    r"\bimport\s+os\b", r"\bimport\s+subprocess\b", r"\bimport\s+sys\b",
    r"\bimport\s+shutil\b", r"\bimport\s+socket\b", r"\bimport\s+pickle\b",
    r"\bos\.system\b", r"\bos\.popen\b", r"\bos\.exec\b", r"\bos\.spawn\b",
    r"\bsubprocess\.", r"\beval\s*\(", r"\bexec\s*\(",
    r"\bopen\s*\(", r"\b__import__\b", r"\bcompile\s*\(",
    r"\bgetattr\s*\(.*__", r"\b__class__\b", r"\b__bases__\b",
]


@dataclass
class GeneratedTool:
    name: str
    description: str
    code: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    run_count: int = 0
    last_result: dict = field(default_factory=dict)


class ToolForge:
    def __init__(self, client: anthropic.AsyncAnthropic):
        self.client = client
        self._registry: dict[str, GeneratedTool] = {}

    def _validate(self, code: str) -> tuple[bool, str]:
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, code):
                return False, f"Forbidden pattern: {pattern}"
        try:
            ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        return True, ""

    async def _write_code(self, description: str, target_url: str, extra_args: dict) -> str:
        prompt = (
            f"Write a Python async function for this security check:\n\n"
            f"Task: {description}\n"
            f"Target URL: {target_url}\n"
            f"Extra args: {json.dumps(extra_args)}\n\n"
            "Rules:\n"
            "- Function signature: async def run_check(url: str, args: dict) -> dict\n"
            "- Allowed imports: httpx, json, re, asyncio, urllib.parse, base64, hashlib\n"
            "- FORBIDDEN: os, subprocess, open(), eval(), exec(), socket, sys, pickle\n"
            "- Return: {\"vulnerable\": bool, \"severity\": str, \"findings\": list[str], \"evidence\": str}\n"
            "- Use: async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=10) as c:\n"
            "- Handle ALL exceptions, never raise\n"
            "- Max 80 lines\n\n"
            "Return ONLY the Python function code. No markdown, no explanation."
        )
        resp = await self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        code = resp.content[0].text.strip()
        code = re.sub(r"^```python\s*", "", code)
        code = re.sub(r"\s*```$", "", code)
        return code.strip()

    async def _execute(self, code: str, url: str, args: dict) -> Any:
        safe_builtins: dict[str, Any] = {
            "print": print, "len": len, "range": range, "list": list,
            "dict": dict, "set": set, "tuple": tuple,
            "str": str, "int": int, "float": float, "bool": bool,
            "bytes": bytes, "bytearray": bytearray,
            "None": None, "True": True, "False": False,
            "isinstance": isinstance, "issubclass": issubclass,
            "enumerate": enumerate, "zip": zip, "map": map,
            "filter": filter, "sorted": sorted, "reversed": reversed,
            "max": max, "min": min, "sum": sum, "abs": abs,
            "any": any, "all": all, "next": next, "iter": iter,
            "hasattr": hasattr, "getattr": getattr,
            "Exception": Exception, "ValueError": ValueError,
            "TypeError": TypeError, "KeyError": KeyError,
            "IndexError": IndexError, "AttributeError": AttributeError,
        }
        ns: dict[str, Any] = {
            "__builtins__": safe_builtins,
            "httpx": httpx,
            "json": json,
            "re": re,
            "asyncio": asyncio,
        }
        try:
            from urllib import parse as _parse
            import base64 as _b64
            import hashlib as _hash
            ns["urllib"] = type("urllib", (), {"parse": _parse})()
            ns["base64"] = _b64
            ns["hashlib"] = _hash
        except Exception:
            pass

        exec(compile(code, "<forge>", "exec"), ns)
        if "run_check" not in ns:
            return {"error": "run_check() not defined in generated code"}
        try:
            result = await asyncio.wait_for(ns["run_check"](url, args), timeout=30.0)
            return result if isinstance(result, dict) else {"result": str(result)}
        except asyncio.TimeoutError:
            return {"error": "Execution timed out (30s)"}
        except Exception as exc:
            return {"error": f"Runtime error: {exc}"}

    async def generate_and_run(self, description: str, target_url: str = "", extra_args: dict | None = None) -> str:
        extra_args = extra_args or {}
        try:
            code = await self._write_code(description, target_url, extra_args)
            valid, err = self._validate(code)
            if not valid:
                return json.dumps({"error": f"Code validation failed: {err}", "snippet": code[:300]})

            result = await self._execute(code, target_url, extra_args)

            name = f"tool_{len(self._registry) + 1:03d}"
            tool = GeneratedTool(name=name, description=description, code=code, last_result=result)
            self._registry[name] = tool

            return json.dumps({
                "status": "tool_generated_and_executed",
                "tool_name": name,
                "code_lines": len(code.splitlines()),
                "result": result,
            })
        except Exception as exc:
            return json.dumps({"error": str(exc)})

    def list_tools(self) -> list[dict]:
        return [{"name": t.name, "description": t.description[:80], "runs": t.run_count}
                for t in self._registry.values()]


class SkillForge:
    def __init__(self, client: anthropic.AsyncAnthropic):
        self.client = client
        self._registry: dict[str, str] = {}

    async def create_skill(self, technology: str, target_url: str, context: str = "") -> str:
        if technology in self._registry:
            return json.dumps({
                "technology": technology,
                "cached": True,
                "instructions": self._registry[technology],
            })

        prompt = (
            f"You are a senior penetration tester. Create a SPECIFIC security scanning strategy for:\n"
            f"Technology: {technology}\n"
            f"Target: {target_url}\n"
            f"Evidence found: {context or 'Not specified'}\n\n"
            f"Write a numbered checklist (10-15 steps) covering:\n"
            f"1. Known CVEs and exploits specific to {technology}\n"
            f"2. Default credentials, admin paths, and backdoors\n"
            f"3. Common misconfigurations specific to this technology\n"
            f"4. Injection points and attack vectors unique to it\n"
            f"5. Which generate_and_run_tool calls to make and what to look for\n\n"
            f"Be specific to {technology} — not generic. Include real CVE IDs if known.\n"
            f"Max 400 words. Return only the checklist."
        )

        resp = await self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        skill_text = resp.content[0].text.strip()
        self._registry[technology] = skill_text

        return json.dumps({
            "technology": technology,
            "skill_created": True,
            "instructions": skill_text,
            "note": "Follow these steps immediately using your available tools.",
        })

    def list_skills(self) -> list[str]:
        return list(self._registry.keys())
