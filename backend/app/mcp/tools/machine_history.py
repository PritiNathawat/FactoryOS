"""
MachineHistoryTool
-------------------
Retrieves the full operational and failure history for a piece of equipment.

In Sprint 2: Returns realistic mock data for Plant Alpha's machine fleet.
In Sprint 3+: Queries the FactoryOS Equipment database via SQLAlchemy.

The Maintenance Agent uses this tool to understand:
  - How often this machine has failed
  - What kind of failures it has had
  - How overdue it is for maintenance
  - Whether a pattern indicates root cause
"""

from __future__ import annotations

from typing import ClassVar, Type

from pydantic import BaseModel, Field

from app.mcp.base import BaseMCPTool, ToolPermission, ToolResult


# ─── Input / Output Schemas ───────────────────────────────────

class MachineHistoryInput(BaseModel):
    equipment_id: str = Field(..., description="Equipment identifier (e.g., M-12)")


class FailureEvent(BaseModel):
    date: str
    failure_type: str
    description: str
    downtime_hours: float
    resolution: str
    cost_usd: float


class MachineHistoryOutput(BaseModel):
    equipment_id: str
    equipment_name: str
    equipment_type: str
    location: str
    manufacturer: str
    model_number: str
    installation_date: str
    total_operating_hours: int
    maintenance_interval_hours: int
    hours_since_last_maintenance: int
    last_maintenance_date: str
    next_scheduled_maintenance: str
    failure_history: list[FailureEvent]
    current_health_score: float = Field(ge=0.0, le=1.0)
    mtbf_hours: float  # Mean Time Between Failures
    reliability_rating: str


# ─── Mock Dataset ─────────────────────────────────────────────

_MACHINE_DATA: dict[str, dict] = {
    "M-12": {
        "equipment_id": "M-12",
        "equipment_name": "CNC Milling Machine M-12",
        "equipment_type": "CNC Machining Center",
        "location": "Bay 3, Line A",
        "manufacturer": "DMG Mori",
        "model_number": "DMU 50 3rd Generation",
        "installation_date": "2019-03-15",
        "total_operating_hours": 12450,
        "maintenance_interval_hours": 500,
        "hours_since_last_maintenance": 487,
        "last_maintenance_date": "2026-05-15",
        "next_scheduled_maintenance": "2026-07-15",
        "failure_history": [
            {
                "date": "2026-03-10",
                "failure_type": "spindle_bearing_wear",
                "description": "Spindle bearing showing excessive vibration, replaced",
                "downtime_hours": 6.5,
                "resolution": "Bearing assembly replaced, spindle realigned",
                "cost_usd": 2800.0,
            },
            {
                "date": "2025-11-20",
                "failure_type": "coolant_leak",
                "description": "Coolant pump seal failure causing leak",
                "downtime_hours": 3.0,
                "resolution": "Pump seal replaced, coolant system flushed",
                "cost_usd": 450.0,
            },
            {
                "date": "2025-06-08",
                "failure_type": "axis_servo_fault",
                "description": "Y-axis servo drive fault, intermittent positioning errors",
                "downtime_hours": 8.0,
                "resolution": "Servo drive replaced, axes recalibrated",
                "cost_usd": 5200.0,
            },
            {
                "date": "2024-12-15",
                "failure_type": "tool_changer_jam",
                "description": "Automatic tool changer mechanism jammed",
                "downtime_hours": 2.0,
                "resolution": "Mechanical jam cleared, ATC lubricated",
                "cost_usd": 320.0,
            },
        ],
        "current_health_score": 0.62,
        "mtbf_hours": 2890.0,
        "reliability_rating": "FAIR",
    },
    "M-07": {
        "equipment_id": "M-07",
        "equipment_name": "Hydraulic Press M-07",
        "equipment_type": "Industrial Hydraulic Press",
        "location": "Bay 1, Line B",
        "manufacturer": "Schuler AG",
        "model_number": "MBA 1000",
        "installation_date": "2021-06-01",
        "total_operating_hours": 8200,
        "maintenance_interval_hours": 1000,
        "hours_since_last_maintenance": 120,
        "last_maintenance_date": "2026-06-10",
        "next_scheduled_maintenance": "2026-10-10",
        "failure_history": [],
        "current_health_score": 0.95,
        "mtbf_hours": 8200.0,
        "reliability_rating": "EXCELLENT",
    },
}

_DEFAULT_MACHINE = {
    "equipment_id": "UNKNOWN",
    "equipment_name": "Unknown Equipment",
    "equipment_type": "General",
    "location": "Unspecified",
    "manufacturer": "Unknown",
    "model_number": "Unknown",
    "installation_date": "2020-01-01",
    "total_operating_hours": 0,
    "maintenance_interval_hours": 500,
    "hours_since_last_maintenance": 0,
    "last_maintenance_date": "2026-01-01",
    "next_scheduled_maintenance": "2026-07-01",
    "failure_history": [],
    "current_health_score": 0.5,
    "mtbf_hours": 1000.0,
    "reliability_rating": "UNKNOWN",
}


# ─── Tool Implementation ───────────────────────────────────────

class MachineHistoryTool(BaseMCPTool):
    name: ClassVar[str] = "machine_history"
    description: ClassVar[str] = (
        "Retrieves complete operational history, failure records, maintenance schedule, "
        "and health metrics for a specified piece of manufacturing equipment."
    )
    permissions: ClassVar[list[ToolPermission]] = [ToolPermission.READ]

    @property
    def input_schema(self) -> Type[BaseModel]:
        return MachineHistoryInput

    @property
    def output_schema(self) -> Type[BaseModel]:
        return MachineHistoryOutput

    async def execute(self, input_data: MachineHistoryInput) -> ToolResult:
        data = _MACHINE_DATA.get(input_data.equipment_id, _DEFAULT_MACHINE.copy())
        if input_data.equipment_id not in _MACHINE_DATA:
            data["equipment_id"] = input_data.equipment_id

        return ToolResult(
            success=True,
            tool_name=self.name,
            data=data,
            source="mock",
        )
