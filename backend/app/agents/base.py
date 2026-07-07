"""
FactoryOS BaseAgent
====================
Abstract base class for all FactoryOS AI agents.

Design follows Google ADK's agent pattern:
  - Every agent has a name, description, and version
  - Every agent receives a tool registry and Gemini client at construction
  - Every agent exposes a single execute(context) -> AgentResponse interface
  - The Manager Agent treats all domain agents polymorphically through this interface

ADK Migration Path:
  When migrating to google-adk, replace:
    class MaintenanceAgent(BaseAgent)  →  Agent(name=..., tools=[...], instruction=PROMPT)
  The agent.execute() maps to agent.run() in ADK.
  The tool_registry maps to Agent(tools=[...]) in ADK.

The BaseAgent provides helpers for:
  - Safe tool calls that never throw (returns ToolResult with success=False)
  - Standardized error responses
  - Execution time tracking
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Optional

from app.core.gemini import GeminiClient
from app.mcp.base import ToolResult
from app.mcp.registry import MCPToolRegistry
from app.schemas.agent import AgentContext, AgentResponse, AgentStatus

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base for all FactoryOS agents.

    Each subclass represents a specialist domain agent with:
      - A fixed system prompt (expertise definition)
      - A defined set of MCP tools it uses
      - Its own Gemini call with its own context
    """

    name: ClassVar[str]
    description: ClassVar[str]
    version: ClassVar[str] = "0.1.0"

    def __init__(
        self,
        tool_registry: MCPToolRegistry,
        gemini_client: GeminiClient,
    ) -> None:
        self.tools = tool_registry
        self.gemini = gemini_client
        self._logger = logging.getLogger(f"agents.{self.name}")

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResponse:
        """
        Execute this agent with the given incident context.

        Must be implemented by every domain agent.
        Should never raise — return AgentResponse with status=ERROR instead.
        """
        ...

    async def _safe_tool_call(
        self, tool_name: str, input_data: dict[str, Any]
    ) -> ToolResult:
        """
        Call a tool safely — exceptions become ToolResult(success=False).

        Agents should always use this method instead of calling tools directly,
        so a single tool failure doesn't crash the entire agent.
        """
        try:
            tool = self.tools.require(tool_name)
            result = await tool.run(input_data)
            if not result.success:
                self._logger.warning(
                    "Tool call failed",
                    extra={"tool": tool_name, "error": result.error},
                )
            return result
        except KeyError:
            self._logger.error("Tool not found in registry: %s", tool_name)
            return ToolResult(
                success=False,
                tool_name=tool_name,
                data=None,
                error=f"Tool '{tool_name}' is not registered",
            )
        except Exception as exc:
            self._logger.error("Unexpected tool error: %s", exc, exc_info=True)
            return ToolResult(
                success=False,
                tool_name=tool_name,
                data=None,
                error=str(exc),
            )

    def _error_response(
        self,
        error_msg: str,
        recommendation: str = "Manual investigation required.",
    ) -> AgentResponse:
        """Return a standardized error response. Never raises."""
        self._logger.error("Agent error response: %s", error_msg)
        return AgentResponse(
            agent_name=self.name,
            status=AgentStatus.ERROR,
            confidence=0.0,
            reasoning=f"Agent execution failed: {error_msg}",
            recommendation=recommendation,
            tools_used=[],
            error_message=error_msg,
        )

    def _parse_response(
        self,
        raw: dict[str, Any],
        tools_used: list[str],
        elapsed_ms: int,
    ) -> AgentResponse:
        """
        Parse a Gemini JSON response dict into a typed AgentResponse.

        Provides safe defaults for every field so a partial Gemini response
        never causes a parsing error.
        """
        status_str = raw.get("status", "success")
        try:
            status = AgentStatus(status_str)
        except ValueError:
            status = AgentStatus.PARTIAL

        return AgentResponse(
            agent_name=self.name,
            status=status,
            confidence=float(raw.get("confidence", 0.5)),
            reasoning=str(raw.get("reasoning", "No reasoning provided.")),
            recommendation=str(raw.get("recommendation", "No recommendation provided.")),
            tools_used=tools_used,
            data=raw.get("data", {}),
            execution_time_ms=elapsed_ms,
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, version={self.version!r})"
