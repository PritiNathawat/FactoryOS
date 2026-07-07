"""
MaintenanceLogsTool
--------------------
Retrieves the service history and technician notes for a machine.

Distinct from MachineHistoryTool which provides structured failure events.
This tool returns the raw maintenance log entries written by technicians —
qualitative observations that are valuable for root cause analysis.
"""

from __future__ import annotations

from typing import ClassVar, Type

from pydantic import BaseModel, Field

from app.mcp.base import BaseMCPTool, ToolPermission, ToolResult


class MaintenanceLogsInput(BaseModel):
    equipment_id: str = Field(..., description="Equipment identifier")
    limit: int = Field(default=10, ge=1, le=50, description="Max number of log entries to return")


class MaintenanceLogEntry(BaseModel):
    log_id: str
    date: str
    technician: str
    maintenance_type: str  # "preventive", "corrective", "inspection"
    duration_hours: float
    observations: str
    actions_taken: str
    parts_replaced: list[str]
    next_action_required: str | None
    severity_flagged: str | None  # "none", "watch", "warning", "critical"


class MaintenanceLogsOutput(BaseModel):
    equipment_id: str
    total_log_entries: int
    returned_entries: int
    logs: list[MaintenanceLogEntry]
    recurring_issues: list[str]
    technician_recommendations: str


_MAINTENANCE_LOGS: dict[str, list[dict]] = {
    "M-12": [
        {
            "log_id": "LOG-2026-0315",
            "date": "2026-05-15",
            "technician": "J. Torres",
            "maintenance_type": "preventive",
            "duration_hours": 3.5,
            "observations": "Vibration levels elevated at spindle. Bearing noise audible at high RPM. Coolant flow rate slightly below spec.",
            "actions_taken": "Lubricated all guide rails. Replaced coolant filters. Tightened spindle lock nut. Vibration still present — flagged for monitoring.",
            "parts_replaced": ["Coolant filters x2", "Spindle lubricant"],
            "next_action_required": "Inspect and possibly replace spindle bearings within 500 operating hours",
            "severity_flagged": "watch",
        },
        {
            "log_id": "LOG-2026-0187",
            "date": "2026-03-10",
            "technician": "M. Singh",
            "maintenance_type": "corrective",
            "duration_hours": 6.5,
            "observations": "Spindle bearing completely seized. Machine shutdown due to grinding noise and thermal overload trip.",
            "actions_taken": "Full bearing assembly replaced. Spindle shaft inspected — no damage. Realigned spindle to 0.002mm runout.",
            "parts_replaced": ["Spindle bearing assembly BRG-SKF-6305-2RS", "Spindle lock ring"],
            "next_action_required": "Monitor vibration signature daily for 2 weeks",
            "severity_flagged": "critical",
        },
        {
            "log_id": "LOG-2025-0892",
            "date": "2025-11-20",
            "technician": "J. Torres",
            "maintenance_type": "corrective",
            "duration_hours": 3.0,
            "observations": "Coolant pump seal failed. Coolant leaking onto workpiece area.",
            "actions_taken": "Replaced pump seal kit. Flushed coolant system. Refilled with fresh coolant.",
            "parts_replaced": ["Coolant pump seal kit SEAL-M12-COOLANT-KIT"],
            "next_action_required": None,
            "severity_flagged": "none",
        },
    ],
}


class MaintenanceLogsTool(BaseMCPTool):
    name: ClassVar[str] = "maintenance_logs"
    description: ClassVar[str] = (
        "Retrieves detailed maintenance log entries including technician observations, "
        "actions taken, parts replaced, and flagged issues for a specific machine."
    )
    permissions: ClassVar[list[ToolPermission]] = [ToolPermission.READ]

    @property
    def input_schema(self) -> Type[BaseModel]:
        return MaintenanceLogsInput

    @property
    def output_schema(self) -> Type[BaseModel]:
        return MaintenanceLogsOutput

    async def execute(self, input_data: MaintenanceLogsInput) -> ToolResult:
        logs = _MAINTENANCE_LOGS.get(input_data.equipment_id, [])
        limited = logs[: input_data.limit]

        recurring = []
        if len(logs) >= 2:
            recurring.append("Spindle bearing wear — recurring pattern detected (2 events in 15 months)")
        if len(logs) >= 1:
            recurring.append("Vibration levels above baseline — ongoing monitoring recommended")

        return ToolResult(
            success=True,
            tool_name=self.name,
            data={
                "equipment_id": input_data.equipment_id,
                "total_log_entries": len(logs),
                "returned_entries": len(limited),
                "logs": limited,
                "recurring_issues": recurring,
                "technician_recommendations": (
                    "Based on recurring bearing issues, recommend comprehensive spindle "
                    "rebuild at next scheduled maintenance. Consider vibration monitoring sensor."
                ),
            },
            source="mock",
        )
