"""
Health & Version Endpoints
============================
GET /api/v1/health  — Liveness probe for infrastructure (Docker, Cloud Run, k8s)
GET /api/v1/version — Deployment confirmation for CI/CD pipelines and humans

These endpoints must:
  - Always be fast (no database calls, no external dependencies)
  - Always return 200 when the application process is alive
  - Be accessible without authentication
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import HealthResponse, VersionResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix=settings.api_v1_prefix,
    tags=["health"],
)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description=(
        "Returns the current liveness status of the FactoryOS API. "
        "Used by Docker HEALTHCHECK, Cloud Run startup probes, and load balancers. "
        "Always returns 200 when the application process is running."
    ),
)
async def health_check() -> HealthResponse:
    """Liveness probe — confirms the application process is alive."""
    logger.debug("Health check requested")
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        environment=settings.environment,
    )


@router.get(
    "/version",
    response_model=VersionResponse,
    summary="Application Version",
    description=(
        "Returns the application name, semantic version, and active environment. "
        "Used by CI/CD pipelines to verify the correct artifact is deployed."
    ),
)
async def get_version() -> VersionResponse:
    """Returns the deployed application version."""
    return VersionResponse(
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
