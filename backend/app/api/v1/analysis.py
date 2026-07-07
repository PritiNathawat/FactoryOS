"""
FactoryOS Analysis API
=======================
REST endpoints for the AI Platform.

Endpoints:
  POST /api/v1/analysis/incidents       → Run full agent pipeline, return 3 recovery plans
  GET  /api/v1/analysis/status          → AI Platform status (agents, tools, mode)
  GET  /api/v1/analysis/tools           → List all registered MCP tools with schemas
  GET  /api/v1/analysis/agents          → List all registered agents with metadata
  GET  /api/v1/analysis/incidents/demo  → Run demo analysis with a preset incident (no body needed)

The analysis endpoint is the main demonstration endpoint for the capstone.
It accepts a POST with an IncidentInput and returns a full OrchestratorResult.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.incident import AnalysisRequest, IncidentInput, IncidentSeverity
from app.schemas.recovery import OrchestratorResult
from app.services.ai_platform import get_ai_platform

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analysis", tags=["AI Platform — Analysis"])



# ─── Main Analysis Endpoint ───────────────────────────────────

@router.post(
    "/incidents",
    response_model=OrchestratorResult,
    summary="Analyze a manufacturing incident",
    description=(
        "Runs the complete FactoryOS multi-agent pipeline:\n\n"
        "1. Manager Agent classifies the incident and assesses risk\n"
        "2. Four domain agents run in parallel (Maintenance, Inventory, Production, Cost)\n"
        "3. Manager Agent synthesizes 3 recovery plans (Economical, Rapid, Balanced)\n"
        "4. Reporting Agent generates an executive summary\n\n"
        "Returns a structured result with all plans and agent findings. "
        "Requires `GEMINI_API_KEY` in environment for real AI responses. "
        "Returns mock responses when key is not configured."
    ),
    status_code=status.HTTP_200_OK,
)
async def analyze_incident(request: AnalysisRequest) -> OrchestratorResult:
    """Analyze a manufacturing incident through the full agent pipeline."""
    platform = get_ai_platform()

    try:
        logger.info(
            "Analysis request received",
            extra={
                "incident_id": request.incident.incident_id,
                "severity": request.incident.severity,
                "equipment_id": request.incident.equipment_id,
            },
        )
        result = await platform.analyze_incident(request.incident)
        return result

    except Exception as exc:
        logger.error("Analysis endpoint error", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(exc)}",
        ) from exc


# ─── Demo Endpoint ────────────────────────────────────────────

@router.get(
    "/incidents/demo",
    response_model=OrchestratorResult,
    summary="Run a demo analysis (Machine M-12 bearing failure)",
    description=(
        "Runs the full analysis pipeline with a pre-configured demo incident "
        "(Machine M-12 bearing failure at Plant Alpha). "
        "Use this endpoint to test the AI Platform without providing a request body."
    ),
)
async def run_demo_analysis() -> OrchestratorResult:
    """Run a demonstration analysis with the canonical M-12 incident."""
    platform = get_ai_platform()

    demo_incident = IncidentInput(
        incident_id="INC-DEMO-2026-001",
        title="CNC Machine M-12 Bearing Failure — Bay 3",
        description=(
            "Machine M-12 (CNC Milling Machine) in Bay 3, Line A has stopped "
            "production due to a suspected spindle bearing failure. A loud grinding "
            "noise was observed for approximately 3 days before the machine tripped "
            "on thermal overload and shut down. The machine was producing part "
            "AEC-4412-B for Aerospace Components Ltd. with a critical deadline of "
            "July 8, 2026. Preliminary inspection confirms bearing damage. "
            "The machine has had a previous bearing failure in March 2026."
        ),
        equipment_id="M-12",
        location="Bay 3, Line A",
        reported_by="operator_torres",
        severity=IncidentSeverity.HIGH,
    )

    try:
        return await platform.analyze_incident(demo_incident)
    except Exception as exc:
        logger.error("Demo analysis failed", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demo analysis failed: {str(exc)}",
        ) from exc


# ─── Introspection Endpoints ──────────────────────────────────

@router.get(
    "/status",
    summary="AI Platform operational status",
)
async def get_platform_status() -> dict:
    """Return AI Platform status including mode, agents, and tools."""
    return get_ai_platform().get_platform_status()


@router.get(
    "/tools",
    summary="List all registered MCP tools",
    description="Returns all MCP tools with their input/output schemas and permissions.",
)
async def list_tools() -> dict:
    """List all registered MCP tools with their schemas."""
    platform = get_ai_platform()
    return {
        "tool_count": len(platform.tool_registry),
        "tools": platform.tool_registry.list_definitions(),
    }


@router.get(
    "/agents",
    summary="List all registered AI agents",
    description="Returns metadata about all deployed agents in the FactoryOS platform.",
)
async def list_agents() -> dict:
    """List all registered agents with their metadata."""
    platform = get_ai_platform()
    return {
        "agent_count": len(platform.agent_registry),
        "agents": platform.agent_registry.list_metadata(),
    }
