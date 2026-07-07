"""
FactoryOS AI Platform Service
===============================
The single entry point for the AI Platform subsystem.

AIPlatformService is responsible for:
  1. Constructing all dependencies (Gemini client, tool registry, agents)
  2. Wiring them together (dependency injection)
  3. Exposing a clean analyze_incident() method to the API layer

This is the Composition Root — all construction happens here.
The API layer (analysis.py) only calls analyze_incident(), it never
knows about individual agents, tools, or skills.

Design rationale — why a service class instead of global singletons?
  - Testable: You can inject mocks for gemini_client or tool_registry
  - Replaceable: Future Sprint can swap CostIntelligenceAgent v2 in one place
  - Lifecycle-managed: The service can be initialized at FastAPI startup
    and cleaned up at shutdown without affecting the API layer

Singleton pattern:
  get_ai_platform() returns a module-level singleton.
  This is appropriate because:
  - All state is in the Gemini API and tool registry (no mutable state here)
  - Creating GeminiClient per request would be wasteful
"""

from __future__ import annotations

import logging
from typing import Optional

from app.agents.cost.cost_agent import CostIntelligenceAgent
from app.agents.inventory.inventory_agent import InventoryAgent
from app.agents.maintenance.maintenance_agent import MaintenanceAgent
from app.agents.orchestrator.manager_agent import ManagerAgent
from app.agents.production.production_agent import ProductionAgent
from app.agents.registry import AgentRegistry
from app.agents.reporting.reporting_agent import ReportingAgent
from app.core.gemini import GeminiClient, get_gemini_client
from app.mcp.registry import MCPToolRegistry, create_tool_registry
from app.schemas.incident import IncidentInput
from app.schemas.recovery import OrchestratorResult

logger = logging.getLogger(__name__)


class AIPlatformService:
    """
    Composition root for the FactoryOS AI Platform.

    Constructs and wires all components:
      - GeminiClient (shared across all agents)
      - MCPToolRegistry (7 tools available to agents)
      - 5 domain agents (maintenance, inventory, production, cost, reporting)
      - ManagerAgent (orchestrator)
      - AgentRegistry (for API introspection)
    """

    def __init__(self) -> None:
        logger.info("Initializing FactoryOS AI Platform...")

        # ── Infrastructure ─────────────────────────────────
        self.gemini: GeminiClient = get_gemini_client()
        self.tool_registry: MCPToolRegistry = create_tool_registry()

        # ── Domain Agents ──────────────────────────────────
        self.maintenance_agent = MaintenanceAgent(self.tool_registry, self.gemini)
        self.inventory_agent = InventoryAgent(self.tool_registry, self.gemini)
        self.production_agent = ProductionAgent(self.tool_registry, self.gemini)
        self.cost_agent = CostIntelligenceAgent(self.tool_registry, self.gemini)
        self.reporting_agent = ReportingAgent(self.tool_registry, self.gemini)

        # ── Orchestrator ───────────────────────────────────
        self.manager_agent = ManagerAgent(
            tool_registry=self.tool_registry,
            gemini_client=self.gemini,
            maintenance_agent=self.maintenance_agent,
            inventory_agent=self.inventory_agent,
            production_agent=self.production_agent,
            cost_agent=self.cost_agent,
            reporting_agent=self.reporting_agent,
        )

        # ── Agent Registry (introspection) ─────────────────
        self.agent_registry = AgentRegistry()
        for agent in [
            self.maintenance_agent,
            self.inventory_agent,
            self.production_agent,
            self.cost_agent,
            self.reporting_agent,
        ]:
            self.agent_registry.register(agent)

        logger.info(
            "AI Platform ready",
            extra={
                "agents": self.agent_registry.list_names(),
                "tools": self.tool_registry.list_names(),
                "gemini_mock_mode": self.gemini.is_mock,
            },
        )

    async def analyze_incident(self, incident: IncidentInput) -> OrchestratorResult:
        """
        Analyze a manufacturing incident through the full agent pipeline.

        This is the only method the API layer calls.
        All orchestration, tool calls, and Gemini calls happen inside here.

        Args:
            incident: The validated IncidentInput from the API request

        Returns:
            OrchestratorResult with 3 recovery plans, agent findings, and executive summary
        """
        return await self.manager_agent.run_analysis(incident)

    def get_platform_status(self) -> dict:
        """Return the current status of the AI Platform for health checks."""
        return {
            "status": "operational",
            "gemini_mode": "mock" if self.gemini.is_mock else "live",
            "gemini_model": self.gemini._model,
            "agents": self.agent_registry.list_metadata(),
            "tools": self.tool_registry.list_names(),
            "tool_count": len(self.tool_registry),
            "agent_count": len(self.agent_registry),
        }


# ─── Module-level Singleton ───────────────────────────────────

_platform: Optional[AIPlatformService] = None


def get_ai_platform() -> AIPlatformService:
    """
    Return the shared AIPlatformService singleton.

    Called by FastAPI dependency injection and by the analysis router.
    The singleton is created on first call (lazy initialization).
    """
    global _platform
    if _platform is None:
        _platform = AIPlatformService()
    return _platform
