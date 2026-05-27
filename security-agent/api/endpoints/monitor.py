from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse

from core.models import MonitorRequest, SecurityReport, JobStatus
from core.orchestrator import Orchestrator

router = APIRouter(prefix="/monitor", tags=["Log Monitor"])


def get_orchestrator() -> Orchestrator:
    from main import orchestrator
    return orchestrator


@router.post("", response_model=SecurityReport, summary="Analyze HTTP logs for attacks")
async def monitor(request: MonitorRequest, orc: Orchestrator = Depends(get_orchestrator)):
    return await orc.run_monitor(request)


@router.post("/upload", response_model=SecurityReport, summary="Upload a log file for analysis")
async def monitor_upload(
    logfile: UploadFile = File(...),
    log_format: str = Form("auto"),
    orc: Orchestrator = Depends(get_orchestrator),
):
    content = (await logfile.read()).decode("utf-8", errors="replace")
    request = MonitorRequest(log_content=content, log_format=log_format)
    return await orc.run_monitor(request)
