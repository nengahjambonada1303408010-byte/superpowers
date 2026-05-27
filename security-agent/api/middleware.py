from __future__ import annotations

import time
from collections import defaultdict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import settings


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/api/v1/health", "/", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != settings.service_api_key:
            return JSONResponse(status_code=401, content={"detail": "Invalid or missing X-API-Key header."})
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.rpm = requests_per_minute
        self._counts: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/api/v1/health", "/docs", "/openapi.json"):
            return await call_next(request)
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = [t for t in self._counts[ip] if now - t < 60]
        if len(window) >= self.rpm:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Try again in a minute."})
        window.append(now)
        self._counts[ip] = window
        return await call_next(request)
