import json
import asyncio
import httpx

TOOL_SCHEMAS = [
    {
        "name": "http_get",
        "description": "Send an HTTP GET request to a URL and return status code, headers, and body snippet.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "headers": {"type": "object", "description": "Optional request headers"},
                "timeout": {"type": "integer", "default": 10},
            },
            "required": ["url"],
        },
    },
    {
        "name": "http_post",
        "description": "Send an HTTP POST request with a JSON or form body.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "body": {"type": "object"},
                "headers": {"type": "object"},
                "timeout": {"type": "integer", "default": 10},
            },
            "required": ["url", "body"],
        },
    },
    {
        "name": "check_security_headers",
        "description": "Check a URL for the presence/absence of important HTTP security headers (CSP, HSTS, X-Frame-Options, CORS, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"}
            },
            "required": ["url"],
        },
    },
    {
        "name": "test_sqli_probe",
        "description": "Send non-destructive SQL injection probe payloads to a URL parameter and check for error signatures.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "param": {"type": "string", "description": "Query parameter name to test"},
            },
            "required": ["url", "param"],
        },
    },
    {
        "name": "test_xss_probe",
        "description": "Send reflected XSS probe payloads to a URL parameter and check for reflection in response.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "param": {"type": "string", "description": "Query parameter name to test"},
            },
            "required": ["url", "param"],
        },
    },
]

SECURITY_HEADERS = [
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Frame-Options",
    "X-Content-Type-Options",
    "Referrer-Policy",
    "Permissions-Policy",
    "X-XSS-Protection",
    "Access-Control-Allow-Origin",
]

SQLI_PAYLOADS = ["'", "' OR '1'='1", "'; DROP TABLE users; --", "1 AND 1=2", "1 UNION SELECT NULL--"]
SQLI_ERROR_PATTERNS = [
    "sql syntax", "mysql_fetch", "ORA-", "pg_query", "sqlite_", "SQLSTATE",
    "Unclosed quotation mark", "syntax error", "mysql error",
]

XSS_MARKER = "xss_probe_8f3a"
XSS_PAYLOADS = [f"<script>{XSS_MARKER}</script>", f'"><img src=x onerror="{XSS_MARKER}">']


async def _get(url: str, params: dict | None = None, headers: dict | None = None, timeout: int = 10) -> httpx.Response:
    async with httpx.AsyncClient(follow_redirects=True, verify=False, timeout=timeout) as client:
        return await client.get(url, params=params, headers=headers or {})


async def _post(url: str, json_body: dict, headers: dict | None = None, timeout: int = 10) -> httpx.Response:
    async with httpx.AsyncClient(follow_redirects=True, verify=False, timeout=timeout) as client:
        return await client.post(url, json=json_body, headers=headers or {})


def _response_summary(resp: httpx.Response) -> dict:
    body = resp.text[:2000] if resp.text else ""
    return {
        "status_code": resp.status_code,
        "headers": dict(resp.headers),
        "body_snippet": body,
        "url": str(resp.url),
    }


async def http_get_async(url: str, headers: dict | None = None, timeout: int = 10) -> str:
    try:
        resp = await _get(url, headers=headers, timeout=timeout)
        return json.dumps(_response_summary(resp))
    except Exception as exc:
        return json.dumps({"error": str(exc)})


async def http_post_async(url: str, body: dict, headers: dict | None = None, timeout: int = 10) -> str:
    try:
        resp = await _post(url, body, headers=headers, timeout=timeout)
        return json.dumps(_response_summary(resp))
    except Exception as exc:
        return json.dumps({"error": str(exc)})


async def check_security_headers_async(url: str) -> str:
    try:
        resp = await _get(url, timeout=10)
        headers = {k.lower(): v for k, v in resp.headers.items()}
        result = {"url": url, "status_code": resp.status_code, "headers": {}}
        for h in SECURITY_HEADERS:
            key = h.lower()
            result["headers"][h] = {
                "present": key in headers,
                "value": headers.get(key, ""),
            }
        missing = [h for h, v in result["headers"].items() if not v["present"]]
        result["missing_security_headers"] = missing
        result["score"] = round((len(SECURITY_HEADERS) - len(missing)) / len(SECURITY_HEADERS) * 10, 1)
        return json.dumps(result)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


async def test_sqli_probe_async(url: str, param: str) -> str:
    findings = []
    for payload in SQLI_PAYLOADS:
        try:
            resp = await _get(url, params={param: payload}, timeout=8)
            body_lower = resp.text.lower()
            triggered = [e for e in SQLI_ERROR_PATTERNS if e.lower() in body_lower]
            if triggered or resp.status_code == 500:
                findings.append({
                    "payload": payload,
                    "status_code": resp.status_code,
                    "error_signatures": triggered,
                    "vulnerable": True,
                })
        except Exception as exc:
            findings.append({"payload": payload, "error": str(exc)})
    return json.dumps({
        "url": url,
        "param": param,
        "payloads_tested": len(SQLI_PAYLOADS),
        "vulnerable_responses": findings,
        "likely_vulnerable": any(f.get("vulnerable") for f in findings),
    })


async def test_xss_probe_async(url: str, param: str) -> str:
    findings = []
    for payload in XSS_PAYLOADS:
        try:
            resp = await _get(url, params={param: payload}, timeout=8)
            reflected = XSS_MARKER in resp.text
            findings.append({
                "payload": payload,
                "status_code": resp.status_code,
                "reflected": reflected,
            })
        except Exception as exc:
            findings.append({"payload": payload, "error": str(exc)})
    return json.dumps({
        "url": url,
        "param": param,
        "payloads_tested": len(XSS_PAYLOADS),
        "results": findings,
        "likely_vulnerable": any(f.get("reflected") for f in findings),
    })


async def dispatch_async(tool_name: str, tool_input: dict) -> str:
    if tool_name == "http_get":
        return await http_get_async(tool_input["url"], tool_input.get("headers"), tool_input.get("timeout", 10))
    if tool_name == "http_post":
        return await http_post_async(tool_input["url"], tool_input["body"], tool_input.get("headers"), tool_input.get("timeout", 10))
    if tool_name == "check_security_headers":
        return await check_security_headers_async(tool_input["url"])
    if tool_name == "test_sqli_probe":
        return await test_sqli_probe_async(tool_input["url"], tool_input["param"])
    if tool_name == "test_xss_probe":
        return await test_xss_probe_async(tool_input["url"], tool_input["param"])
    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def dispatch(tool_name: str, tool_input: dict) -> str:
    return asyncio.get_event_loop().run_until_complete(dispatch_async(tool_name, tool_input))
