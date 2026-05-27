import json
import asyncio
import re
from urllib.parse import urljoin, urlparse, parse_qs
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
        "name": "crawl_website",
        "description": "Crawl a website to discover all links, forms, input fields, and URL parameters. Returns a map of all discoverable attack surface.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Starting URL to crawl from"},
                "max_pages": {"type": "integer", "default": 30, "description": "Maximum number of pages to crawl"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "discover_endpoints",
        "description": "Probe a base URL for common security-relevant endpoints (admin panels, API paths, config files, backup files, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "base_url": {"type": "string", "description": "Base URL of the website (e.g. https://example.com)"},
            },
            "required": ["base_url"],
        },
    },
    {
        "name": "check_auth_bypass",
        "description": "Test a login or authentication endpoint for common authentication bypass techniques.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Login endpoint URL"},
                "username_field": {"type": "string", "default": "username", "description": "Form field name for username"},
                "password_field": {"type": "string", "default": "password", "description": "Form field name for password"},
            },
            "required": ["url"],
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


COMMON_PATHS = [
    "/admin", "/admin/", "/administrator", "/admin.php", "/admin/login",
    "/wp-admin", "/wp-login.php", "/wp-config.php",
    "/login", "/signin", "/auth", "/api", "/api/v1", "/api/v2",
    "/api/users", "/api/admin", "/api/config", "/api/debug",
    "/.env", "/.env.local", "/.env.backup", "/.git/config",
    "/config.php", "/config.js", "/config.json", "/settings.php",
    "/backup.sql", "/backup.zip", "/db.sql", "/database.sql",
    "/phpinfo.php", "/info.php", "/test.php", "/debug.php",
    "/robots.txt", "/sitemap.xml", "/.well-known/security.txt",
    "/server-status", "/server-info", "/_profiler", "/actuator",
    "/actuator/health", "/actuator/env", "/actuator/mappings",
    "/swagger-ui.html", "/api/docs", "/api/swagger.json", "/openapi.json",
    "/graphql", "/graphiql", "/__admin", "/console",
    "/phpmyadmin", "/adminer.php", "/mysql", "/pma",
    "/upload", "/uploads", "/files", "/static",
    "/user", "/users", "/profile", "/account",
    "/reset-password", "/forgot-password", "/register",
    "/health", "/status", "/version", "/metrics",
]

AUTH_BYPASS_PAYLOADS = [
    {"username": "admin", "password": "admin"},
    {"username": "admin", "password": "password"},
    {"username": "admin", "password": "123456"},
    {"username": "admin'--", "password": "anything"},
    {"username": "' OR '1'='1'--", "password": "anything"},
    {"username": "admin' OR 1=1--", "password": "x"},
    {"username": "' OR 1=1#", "password": "x"},
    {"username": "admin", "password": "' OR '1'='1"},
    {"username": "admin@admin.com", "password": "admin"},
    {"username": "root", "password": "root"},
]


async def crawl_website_async(url: str, max_pages: int = 30) -> str:
    base = urlparse(url)
    base_origin = f"{base.scheme}://{base.netloc}"
    visited: set[str] = set()
    queue: list[str] = [url]
    pages: list[dict] = []
    all_params: set[str] = set()
    all_forms: list[dict] = []

    async with httpx.AsyncClient(follow_redirects=True, verify=False, timeout=10) as client:
        while queue and len(visited) < max_pages:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            try:
                resp = await client.get(current)
                body = resp.text

                parsed_url = urlparse(current)
                params = list(parse_qs(parsed_url.query).keys())
                all_params.update(params)

                links = re.findall(r'href=["\']([^"\']+)["\']', body, re.I)
                forms = re.findall(r'<form[^>]*action=["\']([^"\']*)["\'][^>]*>(.*?)</form>', body, re.I | re.S)
                inputs = re.findall(r'<input[^>]+name=["\']([^"\']+)["\']', body, re.I)
                inline_params = re.findall(r'\?([a-zA-Z_][a-zA-Z0-9_]*)=', body)

                for form_action, form_body in forms:
                    form_inputs = re.findall(r'name=["\']([^"\']+)["\']', form_body, re.I)
                    absolute_action = urljoin(current, form_action) if form_action else current
                    all_forms.append({"action": absolute_action, "fields": form_inputs})

                all_params.update(inputs)
                all_params.update(inline_params)

                for link in links:
                    abs_link = urljoin(current, link)
                    lp = urlparse(abs_link)
                    if lp.netloc == base.netloc and abs_link not in visited and "#" not in abs_link:
                        queue.append(abs_link)

                pages.append({
                    "url": current,
                    "status": resp.status_code,
                    "params": params,
                    "forms": len(forms),
                    "inputs": inputs[:20],
                })
            except Exception:
                pass

    return json.dumps({
        "pages_crawled": len(pages),
        "pages": pages[:50],
        "all_discovered_params": list(all_params)[:50],
        "all_forms": all_forms[:20],
        "base_origin": base_origin,
        "summary": f"Crawled {len(pages)} pages, found {len(all_params)} unique parameters, {len(all_forms)} forms.",
    })


async def discover_endpoints_async(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    found: list[dict] = []
    sensitive: list[dict] = []

    async with httpx.AsyncClient(follow_redirects=False, verify=False, timeout=6) as client:
        tasks = [client.get(f"{base_url}{path}") for path in COMMON_PATHS]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    for path, resp in zip(COMMON_PATHS, responses):
        if isinstance(resp, Exception):
            continue
        entry = {"path": path, "status": resp.status_code, "size": len(resp.text)}
        if resp.status_code in (200, 301, 302, 403):
            found.append(entry)
        if resp.status_code == 200 and any(kw in path for kw in [".env", "config", "backup", "admin", "debug", "phpinfo", "actuator", "swagger"]):
            sensitive.append(entry)

    return json.dumps({
        "base_url": base_url,
        "paths_checked": len(COMMON_PATHS),
        "accessible_endpoints": found,
        "sensitive_endpoints_exposed": sensitive,
        "summary": f"Found {len(found)} accessible endpoints, {len(sensitive)} potentially sensitive.",
    })


async def check_auth_bypass_async(url: str, username_field: str = "username", password_field: str = "password") -> str:
    results = []
    async with httpx.AsyncClient(follow_redirects=True, verify=False, timeout=8) as client:
        for payload in AUTH_BYPASS_PAYLOADS:
            body = {username_field: payload["username"], password_field: payload["password"]}
            try:
                resp = await client.post(url, data=body)
                body_lower = resp.text.lower()
                success_signals = any(kw in body_lower for kw in [
                    "dashboard", "welcome", "logout", "profile", "admin panel",
                    "signed in", "logged in", "success", "token", "session"
                ])
                fail_signals = any(kw in body_lower for kw in [
                    "invalid", "incorrect", "wrong", "failed", "error", "denied"
                ])
                results.append({
                    "payload": payload,
                    "status_code": resp.status_code,
                    "possible_bypass": success_signals and not fail_signals,
                    "redirect": str(resp.url) if str(resp.url) != url else None,
                })
            except Exception as exc:
                results.append({"payload": payload, "error": str(exc)})

    bypassed = [r for r in results if r.get("possible_bypass")]
    return json.dumps({
        "url": url,
        "payloads_tested": len(AUTH_BYPASS_PAYLOADS),
        "results": results,
        "possible_bypass_found": len(bypassed) > 0,
        "bypass_attempts": bypassed,
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
    if tool_name == "crawl_website":
        return await crawl_website_async(tool_input["url"], tool_input.get("max_pages", 30))
    if tool_name == "discover_endpoints":
        return await discover_endpoints_async(tool_input["base_url"])
    if tool_name == "check_auth_bypass":
        return await check_auth_bypass_async(
            tool_input["url"],
            tool_input.get("username_field", "username"),
            tool_input.get("password_field", "password"),
        )
    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def dispatch(tool_name: str, tool_input: dict) -> str:
    return asyncio.get_event_loop().run_until_complete(dispatch_async(tool_name, tool_input))
