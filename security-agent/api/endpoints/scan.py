from __future__ import annotations

import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse

from core.models import ScanRequest, SecurityReport, JobStatus
from core.orchestrator import Orchestrator

router = APIRouter(prefix="/scan", tags=["Vulnerability Scan"])


def get_orchestrator() -> Orchestrator:
    from main import orchestrator
    return orchestrator


@router.post("", response_model=SecurityReport, summary="Scan code or URL for vulnerabilities")
async def scan(request: ScanRequest, orc: Orchestrator = Depends(get_orchestrator)):
    return await orc.run_scan(request)


@router.post("/upload", response_model=SecurityReport, summary="Upload a file for vulnerability scan")
async def scan_upload(
    file: UploadFile = File(...),
    scan_profile: str = Form("standard"),
    orc: Orchestrator = Depends(get_orchestrator),
):
    content = (await file.read()).decode("utf-8", errors="replace")
    request = ScanRequest(
        target_type="file",
        target_content=content,
        filename=file.filename or "uploaded_file",
        scan_profile=scan_profile,
    )
    return await orc.run_scan(request)


@router.post("/async", response_model=JobStatus, summary="Start async vulnerability scan")
async def scan_async(request: ScanRequest, orc: Orchestrator = Depends(get_orchestrator)):
    job_id = orc.create_job()
    asyncio.create_task(orc.run_audit_async(job_id, request))
    return orc.get_job(job_id)


@router.get("/{job_id}", response_model=JobStatus, summary="Get scan job status")
async def scan_status(job_id: str, orc: Orchestrator = Depends(get_orchestrator)):
    job = orc.get_job(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"detail": f"Job '{job_id}' not found."})
    return job
