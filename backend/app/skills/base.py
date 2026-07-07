"""
FactoryOS Skills Base
======================
Abstract base class for all reusable skills.

Skills vs. Agents — the critical distinction:
  Agents: Make LLM calls. Have personas. Handle uncertainty. Return recommendations.
  Skills: Deterministic. Reusable. Domain-logic computation. Return structured data.

A skill is called BY agents, not instead of them.
For example, the Manager Agent calls IncidentClassificationSkill,
then passes the classification result to the MaintenanceAgent.

ADK Parallel:
  Skills map to "sub-functions" or "helper tools" in ADK terminology.
  They are not registered in the tool registry (no LLM-facing interface),
  but they are called programmatically by agent code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseSkill(ABC):
    """
    Abstract base class for all FactoryOS skills.

    Skills are stateless — they receive input, compute output, return result.
    No I/O, no LLM calls, no side effects.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Canonical skill identifier."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this skill computes."""
        ...

    @abstractmethod
    def run(self, **kwargs: Any) -> dict[str, Any]:
        """
        Execute the skill with named parameters.

        Returns a dict that can be directly included in agent context
        or used to enrich a prompt.
        """
        ...
