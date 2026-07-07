"""
FactoryOS Recovery Plan Schemas
=================================
Pydantic models for AI-generated recovery plans and the final
orchestrator result returned from the AI Platform.

The Manager Agent produces an OrchestratorResult containing three plans:
  Plan A — Economical (minimize cost)
  Plan B — Rapid (minimize downtime)
  Plan C — Balanced (optimal tradeoff)

The human Plant Manager reviews these plans and selects one.
This implements the Human-in-the-Loop pattern.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ─── Enumerations ─────────────────────────────────────────────

class PlanType(str, Enum):
    ECONOMICAL = "economical"
    RAPID = "rapid"
    BALANCED = "balanced"


# ─── Recovery Plan Components ─────────────────────────────────

class RecoveryStep(BaseModel):
    """A single action step within a recovery plan."""

    step_number: int
    action: str = Field(..., description="What needs to be done")
    responsible_party: str = Field(..., description="Who executes this step")
    estimated_duration_hours: float
    resources_required: list[str] = Field(default_factory=list)
    dependencies: list[int] = Field(
        default_factory=list,
        description="Step numbers this step depends on",
    )


class RecoveryPlan(BaseModel):
    """
    A complete AI-generated recovery plan.

    Three plans are generated per incident (A/B/C), each optimizing for
    a different objective. The Plant Manager selects one to execute.
    """

    plan_id: str = Field(..., description="'A', 'B', or 'C'")
    plan_type: PlanType
    label: str = Field(..., description="Human-readable label, e.g. 'Economical Recovery'")
    description: str

    estimated_cost_usd: float = Field(..., description="Total estimated cost in USD")
    estimated_downtime_hours: float = Field(..., description="Total downtime in hours")
    production_impact_units: Optional[int] = Field(
        default=None,
        description="Estimated units of lost production",
    )

    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(..., description="Why this plan was designed this way")

    steps: list[RecoveryStep] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list, description="Known risks of this plan")
    prerequisites: list[str] = Field(
        default_factory=list,
        description="What must be in place before execution",
    )


# ─── Orchestrator Result ──────────────────────────────────────

class OrchestratorResult(BaseModel):
    """
    The complete output of the FactoryOS AI Platform for one incident.

    This is what the API endpoint returns. It contains:
    - Three recovery plans for human review
    - Individual agent responses for transparency
    - Executive summary from the Reporting Agent
    - Human-in-the-loop flags

    Human-in-the-Loop principle: requires_human_approval is True when:
    - Severity is HIGH or CRITICAL
    - Confidence overall is below 0.70
    - Any plan involves safety systems
    """

    incident_id: str
    status: str

    # Which agents were consulted
    agents_consulted: list[str] = Field(default_factory=list)

    # Classification results
    incident_category: str
    incident_severity: str

    # The three recovery plans
    plans: list[RecoveryPlan] = Field(
        default_factory=list,
        description="Recovery plans ordered: Economical, Balanced, Rapid",
    )

    # Executive summary from the Reporting Agent
    executive_summary: str

    # Overall confidence across all agents (weighted average)
    confidence_overall: float = Field(ge=0.0, le=1.0)

    # Human-in-the-Loop decision flag
    requires_human_approval: bool = True
    human_approval_reason: Optional[str] = None

    # Timestamps
    analyzed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Raw agent responses — provides full transparency into AI reasoning
    # Agents are keyed by their name: "maintenance", "inventory", etc.
    agent_responses: dict[str, Any] = Field(default_factory=dict)

    # Metadata
    model_used: str = "gemini-2.0-flash"
    platform_version: str = "0.1.0"
