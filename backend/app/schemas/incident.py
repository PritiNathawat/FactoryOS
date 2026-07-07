"""
FactoryOS Incident Schemas
===========================
Pydantic models for manufacturing incident input and classification.

These are the entry types for the AI Platform. The Manager Agent receives
an IncidentInput and every downstream agent receives an AgentContext
derived from it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ─── Enumerations ─────────────────────────────────────────────

class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentCategory(str, Enum):
    EQUIPMENT_FAILURE = "equipment_failure"
    SUPPLY_CHAIN = "supply_chain"
    QUALITY_ISSUE = "quality_issue"
    SAFETY_EVENT = "safety_event"
    SCHEDULED_MAINTENANCE = "scheduled_maintenance"
    UNPLANNED_DOWNTIME = "unplanned_downtime"
    UNKNOWN = "unknown"


class IncidentStatus(str, Enum):
    OPEN = "open"
    ANALYZING = "analyzing"
    PLANS_READY = "plans_ready"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


# ─── Input Models ─────────────────────────────────────────────

class IncidentInput(BaseModel):
    """
    The raw incident report submitted by a plant operator.
    This is the entry point to the FactoryOS AI Platform.
    """

    incident_id: str = Field(
        ...,
        description="Unique incident identifier (e.g., INC-2026-001)",
        examples=["INC-2026-042"],
    )
    title: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Short description of the incident",
        examples=["CNC Machine M-12 Bearing Failure"],
    )
    description: str = Field(
        ...,
        min_length=10,
        description="Full incident description with all available details",
        examples=["Machine M-12 in Bay 3 has stopped due to a reported bearing failure. Loud grinding noise was observed before shutdown. Machine has been producing inconsistent tolerances for the past 3 days."],
    )
    equipment_id: Optional[str] = Field(
        default=None,
        description="Affected equipment identifier",
        examples=["M-12"],
    )
    location: Optional[str] = Field(
        default=None,
        description="Plant location or bay number",
        examples=["Bay 3, Line A"],
    )
    reported_by: str = Field(
        default="operator",
        description="Person or system that reported the incident",
    )
    reported_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of incident report",
    )
    severity: IncidentSeverity = Field(
        default=IncidentSeverity.MEDIUM,
        description="Initial severity estimate from the reporting operator",
    )
    additional_context: Optional[dict] = Field(
        default=None,
        description="Any additional structured data the caller wants to include",
    )


class AnalysisRequest(BaseModel):
    """
    The full request body for POST /api/v1/analysis/incidents
    """

    incident: IncidentInput
    # Future: human_context, override_agents, priority_plan_type etc.


# ─── Classification Result (produced by IncidentClassificationSkill) ──

class IncidentClassification(BaseModel):
    """
    Output of the IncidentClassificationSkill.
    Used by the Manager Agent to route the incident to the correct domain agents.
    """

    category: IncidentCategory
    severity: IncidentSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    affected_systems: list[str] = Field(default_factory=list)
    requires_immediate_action: bool = False
    classification_reasoning: str = ""
