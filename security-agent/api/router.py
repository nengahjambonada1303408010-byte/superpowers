from fastapi import APIRouter
from api.endpoints import scan, monitor, pentest, audit, deepscan

router = APIRouter(prefix="/api/v1")

router.include_router(deepscan.router)
router.include_router(scan.router)
router.include_router(monitor.router)
router.include_router(pentest.router)
router.include_router(audit.router)
