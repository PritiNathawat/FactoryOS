"""
Incidents API Router — Sprint 1 Stub
======================================
Full implementation: Sprint 2

Planned endpoints:
  GET    /api/v1/incidents          — List all incidents (paginated)
  POST   /api/v1/incidents          — Create a new incident
  GET    /api/v1/incidents/{id}     — Get a specific incident
  PATCH  /api/v1/incidents/{id}     — Update incident status
  POST   /api/v1/incidents/{id}/analyze — Trigger AI agent analysis pipeline

This stub documents the planned surface in the OpenAPI spec and returns
501 Not Implemented for all routes, clearly communicating intent.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix=settings.api_v1_prefix,
    tags=["incidents"],
)


@router.get(
    "/incidents",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="List Incidents — Sprint 2",
    description="Returns a paginated list of manufacturing incidents. Implemented in Sprint 2.",
    responses={
        501: {"description": "Not yet implemented — available in Sprint 2."},
    },
)
async def list_incidents() -> JSONResponse:
    """Placeholder: incident list endpoint (Sprint 2)."""
    logger.debug("Incidents list endpoint called — stub returning 501")
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "message": "Incidents API is under active development.",
            "available_in": "Sprint 2",
        },
    )
