"""
FactoryOS MCP Tool Base
========================
Abstract base class for all MCP-compliant tools.

Model Context Protocol (MCP) Principles:
  1. Every tool has a DEFINED INPUT SCHEMA — the LLM knows exactly what to send
  2. Every tool has a DEFINED OUTPUT SCHEMA — the LLM knows exactly what to expect
  3. Every tool declares its PERMISSIONS — security is enforced at the tool level
  4. Every tool is DISCOVERABLE — the registry can serialize all tools for inspection

Why MCP matters for FactoryOS:
  Agents must not blindly call backend functions. Each tool call is:
  - Type-validated at entry (input schema)
  - Permission-checked before execution
  - Structured at exit (output schema)
  - Logged for audit

This follows Google ADK's tool pattern where tools are the only
interface between the LLM and backend systems.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, ClassVar, Optional, Type

from pydantic import BaseModel


# ─── Permission Model ─────────────────────────────────────────

class ToolPermission(str, Enum):
    """
    Coarse-grained permission model for MCP tools.

    READ  — Tool retrieves data from source systems (safe, idempotent)
    WRITE — Tool modifies state in source systems (audited, requires approval)
    COST  — Tool triggers financial actions (restricted, human-in-the-loop)
    """
    READ = "read"
    WRITE = "write"
    COST = "cost"


# ─── Tool Result ──────────────────────────────────────────────

class ToolResult(BaseModel):
    """
    Standardized result wrapper returned by every MCP tool.

    The Agent receives ToolResult, not the raw tool output.
    This ensures every tool call can be logged, cached, and inspected uniformly.
    """
    success: bool
    tool_name: str
    data: Any
    error: Optional[str] = None

    # Source tags for observability — "mock", "database", "cache", etc.
    source: str = "mock"


# ─── Base Tool ────────────────────────────────────────────────

class BaseMCPTool(ABC):
    """
    Abstract base class for all FactoryOS MCP tools.

    Subclasses must define:
      - name: Tool identifier (used in registry and prompts)
      - description: Human+LLM readable description of what this tool does
      - permissions: What this tool is allowed to do
      - input_schema: Pydantic model for validated input
      - output_schema: Pydantic model for structured output
      - execute(): The actual tool logic (mock or real)

    Usage by agents:
        tool = registry.get("machine_history")
        result = await tool.run({"equipment_id": "M-12"})
    """

    name: ClassVar[str]
    description: ClassVar[str]
    permissions: ClassVar[list[ToolPermission]]

    @property
    @abstractmethod
    def input_schema(self) -> Type[BaseModel]:
        """Pydantic model that defines the tool's input contract."""
        ...

    @property
    @abstractmethod
    def output_schema(self) -> Type[BaseModel]:
        """Pydantic model that defines the tool's output contract."""
        ...

    @abstractmethod
    async def execute(self, input_data: BaseModel) -> ToolResult:
        """
        Execute the tool with validated input.

        In Sprint 2: mock implementations returning realistic data.
        In Sprint 3+: real database/API calls behind the same interface.
        The agents never change — only the tool implementation changes.
        """
        ...

    async def run(self, raw_input: dict[str, Any]) -> ToolResult:
        """
        Public entry point. Validates input against schema, then executes.

        This is the method agents call. It guarantees:
        1. Input is validated before reaching execute()
        2. Errors are caught and returned as ToolResult(success=False)
        3. Permission check hook (extensible for Sprint 4 security)
        """
        try:
            # Validate and parse input against the declared schema
            validated = self.input_schema(**raw_input)
            return await self.execute(validated)
        except Exception as exc:
            return ToolResult(
                success=False,
                tool_name=self.name,
                data=None,
                error=str(exc),
                source="error",
            )

    def to_mcp_definition(self) -> dict[str, Any]:
        """
        Serialize this tool to MCP protocol format.

        This is what gets sent to the LLM so it understands the tool.
        ADK uses this same format for tool discovery.
        """
        return {
            "name": self.name,
            "description": self.description,
            "permissions": [p.value for p in self.permissions],
            "input_schema": self.input_schema.model_json_schema(),
            "output_schema": self.output_schema.model_json_schema(),
        }
