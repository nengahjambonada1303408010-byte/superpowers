from __future__ import annotations

import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse

from core.models import AdaptiveScanRequest, SecurityReport, JobStatus
from core.orchestrator import Orchestrator

router = APIRouter(prefix="/adaptive", tags=["Adaptive Scan — Self-Creating Tools"])


def get_orchestrator() -> Orchestrator:
    from main import orchestrator
    return orchestrator


@router.post(
    "",
    response_model=SecurityReport,
    summary="Adaptive scan — agent writes its own tools and skills to find critical vulnerabilities",
)
async def adaptive_scan(request: AdaptiveScanRequest, orc: Orchestrator = Depends(get_orchestrator)):
    return await orc.run_adaptive_scan(request)


@router.post(
    "/upload",
    response_model=SecurityReport,
    summary="Upload file — adaptive scanner generates custom tools to analyze it thoroughly",
)
async def adaptive_upload(
    file: UploadFile = File(...),
    stop_on_critical: bool = Form(True),
    max_rounds: int = Form(5),
    orc: Orchestrator = Depends(get_orchestrator),
):
    content = (await file.read()).decode("utf-8", errors="replace")
    return await orc.run_adaptive_scan(AdaptiveScanRequest(
        target_content=content,
        filename=file.filename or "uploaded_file",
        stop_on_critical=stop_on_critical,
        max_rounds=max_rounds,
    ))


@router.post(
    "/async",
    response_model=JobStatus,
    summary="Start async adaptive scan (recommended for large/complex targets)",
)
async def adaptive_scan_async(request: AdaptiveScanRequest, orc: Orchestrator = Depends(get_orchestrator)):
    job_id = orc.create_job()
    asyncio.create_task(orc.run_adaptive_scan_async(job_id, request))
    return orc.get_job(job_id)


@router.get("/{job_id}", response_model=JobStatus, summary="Poll adaptive scan job status")
async def adaptive_status(job_id: str, orc: Orchestrator = Depends(get_orchestrator)):
    job = orc.get_job(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"detail": f"Job '{job_id}' not found."})
    return job
