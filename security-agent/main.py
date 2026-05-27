from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from core.config import settings
from core.orchestrator import Orchestrator
from api.router import router
from api.middleware import APIKeyMiddleware, RateLimitMiddleware

orchestrator: Orchestrator = None  # type: ignore


@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator
    orchestrator = Orchestrator()
    yield


app = FastAPI(
    title="Agentic AI Security Service",
    description=(
        "Multi-agent security service powered by Claude AI. "
        "Supports vulnerability scanning, log monitoring, penetration testing, and security report generation. "
        "Accepts website URLs or application file uploads as input."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(APIKeyMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)

app.include_router(router)


@app.get("/api/v1/health", tags=["Health"])
async def health():
    return {"status": "ok", "model": settings.model, "environment": settings.environment}


@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse({"message": "Agentic AI Security Service. See /docs for API reference."})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.environment == "development")
