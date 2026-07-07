"""
Decision Center API Router — Sprint 1 Stub
============================================
Full implementation: Sprint 3

Planned endpoints:
  GET  /api/v1/decisions/{incident_id}  — Retrieve generated recovery plans
  POST /api/v1/decisions/{incident_id}/approve — Approve a selected plan (human-in-the-loop)
  POST /api/v1/decisions/{incident_id}/reject  — Reject plans and request re-analysis

Each decision response contains three plans:
  Plan A — Economical (lowest cost, longer recovery)
  Plan B — Rapid (fastest recovery, higher cost)
  Plan C — Balanced (Pareto-optimal tradeoff)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix=settings.api_v1_prefix,
    tags=["decisions"],
)


@router.get(
    "/decisions/{incident_id}",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Get Recovery Plans — Sprint 3",
    description=(
        "Returns AI-generated recovery plans (Economical, Rapid, Balanced) "
        "for a given incident. Requires the agent analysis pipeline (Sprint 3)."
    ),
    responses={
        501: {"description": "Not yet implemented — available in Sprint 3."},
    },
)
async def get_decision_plans(incident_id: str) -> JSONResponse:
    """Placeholder: decision plans endpoint (Sprint 3)."""
    logger.debug("Decisions endpoint called — stub returning 501", extra={"incident_id": incident_id})
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "message": "Decision Center API requires the AI agent pipeline.",
            "available_in": "Sprint 3",
        },
    )
