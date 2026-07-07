"""
FactoryOS Shared API Schemas
==============================
Pydantic models shared across multiple API routers.

These schemas define the response contracts for the FactoryOS API.
FastAPI uses them to:
  - Validate response data
  - Generate OpenAPI documentation automatically
  - Provide IDE autocompletion for API consumers

Naming convention:
  - *Response  → response body schemas (what the API returns)
  - *Request   → request body schemas (what the API accepts) — Sprint 2+
  - API*       → generic utility schemas
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────
# Health & Version
# ──────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Response body for GET /api/v1/health"""

    status: str = Field(
        ...,
        description="Current service health status.",
        examples=["healthy"],
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 UTC timestamp of the health check.",
        examples=["2026-06-28T12:00:00+00:00"],
    )
    environment: str = Field(
        ...,
        description="The environment this instance is running in.",
        examples=["development"],
    )


class VersionResponse(BaseModel):
    """Response body for GET /api/v1/version"""

    name: str = Field(
        ...,
        description="Application name.",
        examples=["FactoryOS"],
    )
    version: str = Field(
        ...,
        description="Semantic version string.",
        examples=["0.1.0"],
    )
    environment: str = Field(
        ...,
        description="The environment this instance is running in.",
        examples=["development"],
    )


# ──────────────────────────────────────────────────────────────
# Generic Utility Schemas
# ──────────────────────────────────────────────────────────────

class APIMessage(BaseModel):
    """
    Generic informational response.

    Used for stub endpoints that document planned functionality.
    A 501 stub is preferable to a 404 — it clearly communicates
    intent rather than suggesting the resource does not exist.
    """

    message: str = Field(
        ...,
        description="Human-readable informational message.",
        examples=["This endpoint will be available in Sprint 2."],
    )
    available_in: Optional[str] = Field(
        default=None,
        description="The sprint in which this endpoint will be implemented.",
        examples=["Sprint 2"],
    )


class APIError(BaseModel):
    """
    Standard error response envelope.

    Returned by global exception handlers for all unhandled errors.
    Using a consistent envelope means API consumers can always parse
    error responses the same way, regardless of which endpoint failed.
    """

    error: str = Field(
        ...,
        description="Machine-readable error code.",
        examples=["InternalServerError", "NotFound", "ValidationError"],
    )
    detail: str = Field(
        ...,
        description="Human-readable explanation of what went wrong.",
        examples=["An unexpected error occurred. Please try again."],
    )
    status_code: int = Field(
        ...,
        description="HTTP status code mirrored in the response body for convenience.",
        examples=[500, 404, 422],
    )
