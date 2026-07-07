"""
ProductionScheduleTool
-----------------------
Returns the current production schedule and active work orders for a line.

The Production Agent uses this to calculate:
  - Which orders will be delayed by this incident
  - Whether production can be rerouted to another machine
  - Total units at risk and customer impact
"""

from __future__ import annotations

from typing import ClassVar, Type

from pydantic import BaseModel, Field

from app.mcp.base import BaseMCPTool, ToolPermission, ToolResult


class ProductionScheduleInput(BaseModel):
    equipment_id: str = Field(..., description="Machine that is affected")
    lookahead_days: int = Field(default=7, ge=1, le=30)


class WorkOrder(BaseModel):
    order_id: str
    customer: str
    part_number: str
    quantity_required: int
    quantity_completed: int
    due_date: str
    priority: str  # "critical", "high", "normal", "low"
    estimated_machine_hours: float
    can_be_rerouted: bool
    alternative_machine: str | None


class ProductionScheduleOutput(BaseModel):
    equipment_id: str
    machine_name: str
    current_utilization_pct: float
    active_work_orders: list[WorkOrder]
    total_units_at_risk: int
    critical_orders_count: int
    reroutable_orders_count: int
    reroutable_units: int
    non_reroutable_units: int
    estimated_revenue_at_risk_usd: float
    alternative_machines_available: list[str]


_PRODUCTION_DATA: dict[str, dict] = {
    "M-12": {
        "equipment_id": "M-12",
        "machine_name": "CNC Milling Machine M-12",
        "current_utilization_pct": 87.0,
        "active_work_orders": [
            {
                "order_id": "WO-2026-0841",
                "customer": "Aerospace Components Ltd.",
                "part_number": "AEC-4412-B",
                "quantity_required": 200,
                "quantity_completed": 45,
                "due_date": "2026-07-08",
                "priority": "critical",
                "estimated_machine_hours": 18.5,
                "can_be_rerouted": False,
                "alternative_machine": None,
            },
            {
                "order_id": "WO-2026-0856",
                "customer": "Automotive Tier 1 GmbH",
                "part_number": "AUTO-8821-C",
                "quantity_required": 500,
                "quantity_completed": 200,
                "due_date": "2026-07-12",
                "priority": "high",
                "estimated_machine_hours": 24.0,
                "can_be_rerouted": True,
                "alternative_machine": "M-15",
            },
            {
                "order_id": "WO-2026-0867",
                "customer": "General Manufacturing Co.",
                "part_number": "GM-2210-A",
                "quantity_required": 150,
                "quantity_completed": 0,
                "due_date": "2026-07-18",
                "priority": "normal",
                "estimated_machine_hours": 8.0,
                "can_be_rerouted": True,
                "alternative_machine": "M-09",
            },
        ],
        "total_units_at_risk": 605,
        "critical_orders_count": 1,
        "reroutable_orders_count": 2,
        "reroutable_units": 450,
        "non_reroutable_units": 155,
        "estimated_revenue_at_risk_usd": 284000.0,
        "alternative_machines_available": ["M-09", "M-15"],
    }
}


class ProductionScheduleTool(BaseMCPTool):
    name: ClassVar[str] = "production_schedule"
    description: ClassVar[str] = (
        "Returns active work orders and production schedule for a specific machine. "
        "Identifies orders at risk, which can be rerouted, and total revenue impact."
    )
    permissions: ClassVar[list[ToolPermission]] = [ToolPermission.READ]

    @property
    def input_schema(self) -> Type[BaseModel]:
        return ProductionScheduleInput

    @property
    def output_schema(self) -> Type[BaseModel]:
        return ProductionScheduleOutput

    async def execute(self, input_data: ProductionScheduleInput) -> ToolResult:
        data = _PRODUCTION_DATA.get(
            input_data.equipment_id,
            {
                "equipment_id": input_data.equipment_id,
                "machine_name": f"Machine {input_data.equipment_id}",
                "current_utilization_pct": 0.0,
                "active_work_orders": [],
                "total_units_at_risk": 0,
                "critical_orders_count": 0,
                "reroutable_orders_count": 0,
                "reroutable_units": 0,
                "non_reroutable_units": 0,
                "estimated_revenue_at_risk_usd": 0.0,
                "alternative_machines_available": [],
            },
        )
        return ToolResult(success=True, tool_name=self.name, data=data, source="mock")
