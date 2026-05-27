from __future__ import annotations

import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from core.models import AuditRequest, SecurityReport, JobStatus
from core.orchestrator import Orchestrator

router = APIRouter(prefix="/audit", tags=["Full Audit"])


def get_orchestrator() -> Orchestrator:
    from main import orchestrator
    return orchestrator


@router.post("", response_model=SecurityReport, summary="Run full security audit (scan + monitor + pentest)")
async def audit(request: AuditRequest, orc: Orchestrator = Depends(get_orchestrator)):
    return await orc.run_full_audit(request)


@router.post("/async", response_model=JobStatus, summary="Start async full audit")
async def audit_async(request: AuditRequest, orc: Orchestrator = Depends(get_orchestrator)):
    job_id = orc.create_job()
    asyncio.create_task(orc.run_audit_async(job_id, request))
    return orc.get_job(job_id)


@router.get("/{job_id}", response_model=JobStatus, summary="Get audit job status")
async def audit_status(job_id: str, orc: Orchestrator = Depends(get_orchestrator)):
    job = orc.get_job(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"detail": f"Job '{job_id}' not found."})
    return job
