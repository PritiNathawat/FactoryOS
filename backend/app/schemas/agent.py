"""
FactoryOS Agent Schemas
========================
Pydantic models for agent context, responses, and inter-agent communication.

AgentContext — the structured input every agent receives.
AgentResponse — the structured output every agent produces.

This is the contract between the Manager Agent and all domain agents.
No agent knows about any other agent's internals — only these schemas.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ─── Enumerations ─────────────────────────────────────────────

class AgentStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"   # Agent completed but with degraded confidence
    SKIPPED = "skipped"   # Agent was not invoked for this incident type
    MOCK = "mock"         # No API key configured — mock response returned


# ─── Agent Context ────────────────────────────────────────────

class AgentContext(BaseModel):
    """
    The structured context passed to every domain agent.

    Built by the Manager Agent from the IncidentInput and enriched with:
    - Classification from IncidentClassificationSkill
    - Risk score from RiskAssessmentSkill
    - MCP tool results fetched by the Manager before routing
    """

    incident_id: str
    title: str
    description: str
    equipment_id: Optional[str] = None
    location: Optional[str] = None
    severity: str
    category: str
    risk_score: float = Field(default=0.5, ge=0.0, le=1.0)
    requires_immediate_action: bool = False

    # MCP tool results fetched by Manager Agent
    # Keys are tool names (e.g., "machine_history"), values are tool output dicts
    tool_results: dict[str, Any] = Field(default_factory=dict)

    # Results from other agents (used by the Reporting Agent only)
    agent_results: dict[str, Any] = Field(default_factory=dict)


# ─── Agent Response ───────────────────────────────────────────

class AgentResponse(BaseModel):
    """
    The structured output produced by every domain agent.

    All agents return this same contract. The Manager Agent collects
    all AgentResponses and synthesizes them into recovery plans.

    Design principle: agents express meaning through structured fields,
    not free-form text. The `data` field carries agent-specific structured
    output. The Manager Agent knows the expected shape of `data` per agent.
    """

    agent_name: str = Field(..., description="Canonical name of the agent (e.g., 'maintenance')")
    status: AgentStatus

    # Confidence in this agent's analysis (0.0 = uncertain, 1.0 = highly confident)
    confidence: float = Field(ge=0.0, le=1.0)

    # Human-readable explanation of the agent's reasoning process
    reasoning: str

    # The primary actionable recommendation from this agent
    recommendation: str

    # Tools this agent used to form its recommendation
    tools_used: list[str] = Field(default_factory=list)

    # Agent-specific structured output — each agent defines its own data shape
    data: dict[str, Any] = Field(default_factory=dict)

    # Performance tracking (milliseconds)
    execution_time_ms: Optional[int] = None

    # Error message if status is ERROR or PARTIAL
    error_message: Optional[str] = None
