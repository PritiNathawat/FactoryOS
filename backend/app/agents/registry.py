"""
FactoryOS Agent Registry
=========================
Lightweight registry for introspection of all deployed agents.

The registry is separate from the Manager Agent's direct references —
it is used for:
  - API endpoints (/api/v1/analysis/agents) that list available agents
  - Logging and observability
  - Future: dynamic agent routing by the Manager Agent

All 6 agents (5 domain + 1 manager) are registered at startup.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Manages all registered FactoryOS agents."""

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        """Register an agent. Logs a warning if overwriting an existing entry."""
        if agent.name in self._agents:
            logger.warning("Agent already registered, overwriting: %s", agent.name)
        self._agents[agent.name] = agent
        logger.debug("Agent registered: %s", agent.name)

    def get(self, name: str) -> Optional[BaseAgent]:
        """Retrieve an agent by name. Returns None if not found."""
        return self._agents.get(name)

    def require(self, name: str) -> BaseAgent:
        """Retrieve an agent by name. Raises KeyError if not found."""
        agent = self._agents.get(name)
        if agent is None:
            raise KeyError(f"Agent '{name}' not registered. Available: {self.list_names()}")
        return agent

    def list_names(self) -> list[str]:
        """List all registered agent names."""
        return list(self._agents.keys())

    def list_metadata(self) -> list[dict[str, Any]]:
        """Serialize all agents to a list of metadata dicts for API responses."""
        return [
            {
                "name": agent.name,
                "description": agent.description,
                "version": agent.version,
            }
            for agent in self._agents.values()
        ]

    def __len__(self) -> int:
        return len(self._agents)

    def __repr__(self) -> str:
        return f"AgentRegistry(agents={self.list_names()})"
