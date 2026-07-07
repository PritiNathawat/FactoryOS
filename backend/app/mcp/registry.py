"""
FactoryOS MCP Tool Registry
=============================
Central registry for all MCP tools available to FactoryOS agents.

The registry serves two purposes:
  1. Runtime: Agents call tools by name — registry.get("machine_history").run(...)
  2. Discovery: Agents can inspect all available tools via registry.list_definitions()
     This list is what gets sent to the LLM for dynamic tool selection (Sprint 3+)

ADK Parallel:
  In google-adk, tools are passed as a list to Agent(tools=[...]).
  This registry is the FactoryOS equivalent — a managed collection of tools
  that can be filtered by permission level and serialized for LLM consumption.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.mcp.base import BaseMCPTool, ToolPermission

logger = logging.getLogger(__name__)


class MCPToolRegistry:
    """
    Manages all registered MCP tools.

    Tools self-register via register() at application startup.
    Agents request tools by name at analysis time.
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseMCPTool] = {}

    def register(self, tool: BaseMCPTool) -> None:
        """Register a tool. Called once at application startup."""
        if tool.name in self._tools:
            logger.warning("MCP tool already registered, overwriting: %s", tool.name)
        self._tools[tool.name] = tool
        logger.debug("MCP tool registered: %s", tool.name)

    def get(self, name: str) -> Optional[BaseMCPTool]:
        """Retrieve a tool by its canonical name. Returns None if not found."""
        return self._tools.get(name)

    def require(self, name: str) -> BaseMCPTool:
        """Retrieve a tool by name. Raises KeyError if not found."""
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(
                f"MCP tool '{name}' is not registered. "
                f"Available tools: {list(self._tools.keys())}"
            )
        return tool

    def list_names(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def list_definitions(
        self,
        permissions: Optional[list[ToolPermission]] = None,
    ) -> list[dict]:
        """
        Serialize all tools to MCP protocol format.

        Optionally filter by permission level.
        This output is included in agent prompts so the LLM knows what tools exist.
        """
        definitions = []
        for tool in self._tools.values():
            if permissions is None or any(p in tool.permissions for p in permissions):
                definitions.append(tool.to_mcp_definition())
        return definitions

    def __len__(self) -> int:
        return len(self._tools)

    def __repr__(self) -> str:
        return f"MCPToolRegistry(tools={list(self._tools.keys())})"


# ─── Factory ──────────────────────────────────────────────────

def create_tool_registry() -> MCPToolRegistry:
    """
    Build and return the fully-populated MCP tool registry.

    Called once at application startup from services/ai_platform.py.
    All 7 tools are instantiated and registered here.
    """
    from app.mcp.tools.machine_history import MachineHistoryTool
    from app.mcp.tools.inventory_lookup import InventoryLookupTool
    from app.mcp.tools.supplier_lookup import SupplierLookupTool
    from app.mcp.tools.maintenance_logs import MaintenanceLogsTool
    from app.mcp.tools.production_schedule import ProductionScheduleTool
    from app.mcp.tools.cost_estimator import CostEstimatorTool
    from app.mcp.tools.incident_history import IncidentHistoryTool

    registry = MCPToolRegistry()
    registry.register(MachineHistoryTool())
    registry.register(InventoryLookupTool())
    registry.register(SupplierLookupTool())
    registry.register(MaintenanceLogsTool())
    registry.register(ProductionScheduleTool())
    registry.register(CostEstimatorTool())
    registry.register(IncidentHistoryTool())

    logger.info("MCP tool registry created with %d tools", len(registry))
    return registry
