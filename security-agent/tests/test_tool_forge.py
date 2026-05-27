from __future__ import annotations

import json
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from tools.tool_forge import ToolForge, SkillForge


def make_mock_client(response_text: str):
    client = AsyncMock()
    msg = MagicMock()
    block = MagicMock()
    block.text = response_text
    msg.content = [block]
    client.messages.create = AsyncMock(return_value=msg)
    return client


GOOD_TOOL_CODE = '''
async def run_check(url: str, args: dict) -> dict:
    import httpx
    try:
        async with httpx.AsyncClient(verify=False, timeout=5) as c:
            r = await c.get(url)
            return {"vulnerable": r.status_code == 200, "severity": "INFO", "findings": [f"Status: {r.status_code}"], "evidence": str(r.status_code)}
    except Exception as e:
        return {"vulnerable": False, "severity": "INFO", "findings": [], "evidence": str(e)}
'''

BAD_TOOL_CODE = "import os; os.system('rm -rf /')"


@pytest.mark.asyncio
async def test_tool_forge_validates_forbidden_code():
    client = make_mock_client(BAD_TOOL_CODE)
    forge = ToolForge(client)
    result = json.loads(await forge.generate_and_run("test", "http://example.com"))
    assert "error" in result
    assert "validation" in result["error"].lower() or "Forbidden" in result.get("error", "")


@pytest.mark.asyncio
async def test_tool_forge_generates_and_runs_good_code():
    client = make_mock_client(GOOD_TOOL_CODE)
    forge = ToolForge(client)
    result = json.loads(await forge.generate_and_run("Check HTTP status", "http://httpbin.org/status/200"))
    assert "error" not in result or result.get("status") == "tool_generated_and_executed"


@pytest.mark.asyncio
async def test_tool_forge_registry():
    client = make_mock_client(GOOD_TOOL_CODE)
    forge = ToolForge(client)
    await forge.generate_and_run("Check 1", "http://example.com")
    tools = forge.list_tools()
    assert len(tools) >= 1
    assert "description" in tools[0]


@pytest.mark.asyncio
async def test_skill_forge_creates_skill():
    skill_text = "1. Check /wp-login.php\n2. Test xmlrpc.php\n3. Enumerate users via ?author=1"
    client = make_mock_client(skill_text)
    forge = SkillForge(client)
    result = json.loads(await forge.create_skill("WordPress 6.2", "https://example.com", "Found wp-content in HTML"))
    assert result["skill_created"] is True
    assert "WordPress" in result["technology"]
    assert len(result["instructions"]) > 10


@pytest.mark.asyncio
async def test_skill_forge_caches_skill():
    client = make_mock_client("Step 1. Do something")
    forge = SkillForge(client)
    await forge.create_skill("Laravel", "https://example.com")
    result2 = json.loads(await forge.create_skill("Laravel", "https://example.com"))
    assert result2.get("cached") is True
    assert client.messages.create.call_count == 1
