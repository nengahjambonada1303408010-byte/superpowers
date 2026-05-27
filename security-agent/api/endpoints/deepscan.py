from __future__ import annotations

import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse

from core.models import DeepScanRequest, SecurityReport, JobStatus
from core.orchestrator import Orchestrator

router = APIRouter(prefix="/deepscan", tags=["Deep Scan"])


def get_orchestrator() -> Orchestrator:
    from main import orchestrator
    return orchestrator


@router.post("", response_model=SecurityReport, summary="Persistent deep scan — runs until CRITICAL found or all vectors exhausted")
async def deep_scan(request: DeepScanRequest, orc: Orchestrator = Depends(get_orchestrator)):
    return await orc.run_deep_scan(request)


@router.post("/upload", response_model=SecurityReport, summary="Upload file for persistent deep vulnerability scan")
async def deep_scan_upload(
    file: UploadFile = File(...),
    stop_on_critical: bool = Form(True),
    max_rounds: int = Form(5),
    orc: Orchestrator = Depends(get_orchestrator),
):
    content = (await file.read()).decode("utf-8", errors="replace")
    request = DeepScanRequest(
        target_content=content,
        filename=file.filename or "uploaded_file",
        stop_on_critical=stop_on_critical,
        max_rounds=max_rounds,
    )
    return await orc.run_deep_scan(request)


@router.post("/async", response_model=JobStatus, summary="Start async deep scan (for large targets)")
async def deep_scan_async(request: DeepScanRequest, orc: Orchestrator = Depends(get_orchestrator)):
    job_id = orc.create_job()
    asyncio.create_task(orc.run_deep_scan_async(job_id, request))
    return orc.get_job(job_id)


@router.get("/{job_id}", response_model=JobStatus, summary="Poll deep scan job status")
async def deep_scan_status(job_id: str, orc: Orchestrator = Depends(get_orchestrator)):
    job = orc.get_job(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"detail": f"Job '{job_id}' not found."})
    return job
