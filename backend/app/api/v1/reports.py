"""
Reports API Router — Sprint 1 Stub
=====================================
Full implementation: Sprint 5

Planned endpoints:
  GET  /api/v1/reports                  — List all generated incident reports
  GET  /api/v1/reports/{incident_id}    — Get the report for a resolved incident
  POST /api/v1/reports/{incident_id}/generate — Trigger report generation

Reports are produced by the Reporting Agent after incident resolution.
They include: root cause, selected plan, actual vs. estimated cost, and lessons learned.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix=settings.api_v1_prefix,
    tags=["reports"],
)


@router.get(
    "/reports",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="List Reports — Sprint 5",
    description="Returns a list of generated incident summaries and operational reports. Implemented in Sprint 5.",
    responses={
        501: {"description": "Not yet implemented — available in Sprint 5."},
    },
)
async def list_reports() -> JSONResponse:
    """Placeholder: reports list endpoint (Sprint 5)."""
    logger.debug("Reports list endpoint called — stub returning 501")
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "message": "Reports API requires the Reporting Agent.",
            "available_in": "Sprint 5",
        },
    )
