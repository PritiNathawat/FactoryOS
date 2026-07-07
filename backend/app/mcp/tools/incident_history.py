"""
IncidentHistoryTool
--------------------
Retrieves historical incidents similar to the current one.

Used by the Manager Agent to provide context to all domain agents.
Pattern matching on incident type helps agents learn from past resolutions.
"""

from __future__ import annotations

from typing import ClassVar, Type

from pydantic import BaseModel, Field

from app.mcp.base import BaseMCPTool, ToolPermission, ToolResult


class IncidentHistoryInput(BaseModel):
    equipment_id: str | None = Field(default=None, description="Filter by equipment")
    category: str | None = Field(default=None, description="Filter by incident category")
    limit: int = Field(default=5, ge=1, le=20)


class HistoricalIncident(BaseModel):
    incident_id: str
    date: str
    title: str
    category: str
    equipment_id: str
    severity: str
    resolution_time_hours: float
    resolution_approach: str
    total_cost_usd: float
    outcome: str  # "fully_resolved", "partial_fix", "recurring"
    lessons_learned: str


class IncidentHistoryOutput(BaseModel):
    total_matching_incidents: int
    incidents: list[HistoricalIncident]
    average_resolution_time_hours: float
    most_common_resolution: str
    success_rate: float


_INCIDENTS = [
    {
        "incident_id": "INC-2026-0032",
        "date": "2026-03-10",
        "title": "M-12 Spindle Bearing Seizure",
        "category": "equipment_failure",
        "equipment_id": "M-12",
        "severity": "high",
        "resolution_time_hours": 8.5,
        "resolution_approach": "bearing_replacement",
        "total_cost_usd": 32450.0,
        "outcome": "fully_resolved",
        "lessons_learned": "Vibration monitoring should have triggered earlier. Recommend IoT sensor installation.",
    },
    {
        "incident_id": "INC-2025-0198",
        "date": "2025-11-20",
        "title": "M-12 Coolant System Leak",
        "category": "equipment_failure",
        "equipment_id": "M-12",
        "severity": "medium",
        "resolution_time_hours": 4.0,
        "resolution_approach": "component_swap",
        "total_cost_usd": 13600.0,
        "outcome": "fully_resolved",
        "lessons_learned": "Seal kits should be stocked at higher quantities. Current stock sufficient.",
    },
    {
        "incident_id": "INC-2025-0087",
        "date": "2025-06-08",
        "title": "M-12 Y-Axis Servo Drive Fault",
        "category": "equipment_failure",
        "equipment_id": "M-12",
        "severity": "high",
        "resolution_time_hours": 12.0,
        "resolution_approach": "component_swap",
        "total_cost_usd": 58800.0,
        "outcome": "fully_resolved",
        "lessons_learned": "Servo drives for M-12 should be held in critical spare inventory. Lead time of 14 days is unacceptable.",
    },
]


class IncidentHistoryTool(BaseMCPTool):
    name: ClassVar[str] = "incident_history"
    description: ClassVar[str] = (
        "Retrieves historical incidents matching the current equipment or category. "
        "Provides resolution patterns, costs, and lessons learned from past incidents."
    )
    permissions: ClassVar[list[ToolPermission]] = [ToolPermission.READ]

    @property
    def input_schema(self) -> Type[BaseModel]:
        return IncidentHistoryInput

    @property
    def output_schema(self) -> Type[BaseModel]:
        return IncidentHistoryOutput

    async def execute(self, input_data: IncidentHistoryInput) -> ToolResult:
        results = _INCIDENTS.copy()
        if input_data.equipment_id:
            results = [i for i in results if i["equipment_id"] == input_data.equipment_id]
        if input_data.category:
            results = [i for i in results if i["category"] == input_data.category]
        results = results[: input_data.limit]

        avg_time = sum(i["resolution_time_hours"] for i in results) / len(results) if results else 0.0
        success = sum(1 for i in results if i["outcome"] == "fully_resolved") / len(results) if results else 0.0

        return ToolResult(
            success=True,
            tool_name=self.name,
            data={
                "total_matching_incidents": len(results),
                "incidents": results,
                "average_resolution_time_hours": avg_time,
                "most_common_resolution": "bearing_replacement",
                "success_rate": success,
            },
            source="mock",
        )
