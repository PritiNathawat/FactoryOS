"""
FactoryOS — FastAPI Application Factory
=========================================
Entry point for the Uvicorn ASGI server: `uvicorn app.main:app`

Architecture decisions:
  - Factory pattern: create_application() separates construction from the module-level instance,
    allowing tests to create isolated app instances with different configurations.
  - lifespan context manager: replaces deprecated @app.on_event("startup"/"shutdown").
  - Global exception handler: prevents raw stack traces from leaking in API error responses.
  - CORS middleware: configured from settings — no hardcoded origins.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Code before `yield` runs on startup.
    Code after `yield` runs on graceful shutdown.
    Using asynccontextmanager here (not @app.on_event) is the FastAPI-recommended pattern.
    """
    # ── Startup ───────────────────────────────────────────────
    configure_logging(
        environment=settings.environment,
        log_level=settings.log_level,
    )
    logger.info(
        "FactoryOS API starting",
        extra={
            "version": settings.app_version,
            "environment": settings.environment,
            "database": "sqlite" if settings.is_sqlite else "postgresql",
            "docs": "/api/docs",
        },
    )

    yield

    # ── Shutdown ──────────────────────────────────────────────
    logger.info("FactoryOS API shutting down gracefully")


def create_application() -> FastAPI:
    """
    Application factory.

    Creates and fully configures the FastAPI instance.
    This function is called once at module import time to produce `app`.
    """
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "**FactoryOS** — Production-grade Multi-Agent Manufacturing Operations Platform.\n\n"
            "Built with **Google ADK**, **Gemini**, and **Model Context Protocol (MCP)**.\n\n"
            "Helps Plant Managers detect operational disruptions, evaluate AI-generated "
            "recovery strategies, and coordinate human-approved decisions."
        ),
        # Serve API docs at /api/docs so they don't conflict with Next.js frontend routes.
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
        openapi_tags=[
            {
                "name": "health",
                "description": "Service liveness, readiness, and version information.",
            },
            {
                "name": "incidents",
                "description": "Manufacturing disruption incident lifecycle management.",
            },
            {
                "name": "decisions",
                "description": (
                    "AI-assisted recovery Decision Center. "
                    "Produces three recovery plans: Economical, Rapid, and Balanced."
                ),
            },
            {
                "name": "reports",
                "description": "Incident summaries and operational analytics reports.",
            },
        ],
    )

    # ── CORS Middleware ───────────────────────────────────────
    # In development, the Next.js proxy handles /api/* routing to this server,
    # making CORS headers only relevant for direct API access (Swagger UI, curl).
    # In production, set CORS_ORIGINS to the deployed frontend domain(s).
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # ── Global Exception Handler ──────────────────────────────
    # Catches any unhandled exception that escapes route handlers.
    # Returns a consistent JSON error envelope instead of a raw 500 HTML page.
    @application.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.error(
            "Unhandled exception",
            exc_info=exc,
            extra={
                "method": request.method,
                "url": str(request.url),
            },
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "detail": "An unexpected error occurred. Please try again.",
                "status_code": 500,
            },
        )

    # ── Router Registration ───────────────────────────────────
    # Include the root API router — it aggregates all versioned routes.
    # This is the only router import needed here.
    application.include_router(api_router)

    return application


# ── Module-level application instance ─────────────────────────
# Uvicorn references this: `uvicorn app.main:app`
# Docker CMD and docker-compose reference this via the same string.
app = create_application()
