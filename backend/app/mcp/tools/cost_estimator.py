"""
CostEstimatorTool
------------------
Estimates the financial cost of different repair and recovery approaches.

The Cost Intelligence Agent uses this tool to quantify:
  - Labor costs (technician hourly rates × estimated hours)
  - Parts costs (from InventoryLookupTool data)
  - Downtime costs (production value lost per hour)
  - Expediting premiums (rush procurement surcharges)
"""

from __future__ import annotations

from typing import ClassVar, Type

from pydantic import BaseModel, Field

from app.mcp.base import BaseMCPTool, ToolPermission, ToolResult


class CostEstimatorInput(BaseModel):
    equipment_id: str
    repair_type: str = Field(
        ...,
        description="Type of repair: 'bearing_replacement', 'full_overhaul', 'temporary_fix', 'component_swap'",
    )
    downtime_hours_estimate: float = Field(..., ge=0)


class CostBreakdown(BaseModel):
    category: str
    description: str
    amount_usd: float
    is_recurring: bool = False


class CostEstimatorOutput(BaseModel):
    equipment_id: str
    repair_type: str
    labor_cost_usd: float
    parts_cost_usd: float
    downtime_cost_per_hour_usd: float
    total_downtime_cost_usd: float
    expediting_premium_usd: float
    total_estimated_cost_usd: float
    cost_breakdown: list[CostBreakdown]
    # Preventive maintenance cost if done now vs. reactive cost if deferred
    cost_of_deferring_usd: float
    notes: str


_PLANT_RATES = {
    "labor_rate_per_hour_usd": 125.0,     # Skilled maintenance technician
    "machine_downtime_cost_per_hour": 4200.0,  # M-12 revenue per production hour
    "expediting_premium_pct": 0.35,        # 35% surcharge for rush orders
}

_REPAIR_TYPES: dict[str, dict] = {
    "bearing_replacement": {
        "labor_hours": 6.0,
        "parts_usd": 290.0,  # Bearing + lubricant
        "notes": "Standard repair. Requires spindle disassembly and precision realignment.",
    },
    "full_overhaul": {
        "labor_hours": 24.0,
        "parts_usd": 8500.0,
        "notes": "Comprehensive rebuild. Addresses all worn components. Extended warranty.",
    },
    "temporary_fix": {
        "labor_hours": 2.0,
        "parts_usd": 45.0,
        "notes": "Temporary stabilization to limp through critical order. HIGH RISK of secondary failure.",
    },
    "component_swap": {
        "labor_hours": 8.0,
        "parts_usd": 5200.0,
        "notes": "Replace servo drive unit. Requires OEM procurement if not in stock.",
    },
}


class CostEstimatorTool(BaseMCPTool):
    name: ClassVar[str] = "cost_estimator"
    description: ClassVar[str] = (
        "Estimates financial cost of a specific repair approach including labor, parts, "
        "downtime loss, and expediting premiums. Compares cost of repair now vs. deferral."
    )
    permissions: ClassVar[list[ToolPermission]] = [ToolPermission.READ]

    @property
    def input_schema(self) -> Type[BaseModel]:
        return CostEstimatorInput

    @property
    def output_schema(self) -> Type[BaseModel]:
        return CostEstimatorOutput

    async def execute(self, input_data: CostEstimatorInput) -> ToolResult:
        rates = _PLANT_RATES
        repair = _REPAIR_TYPES.get(
            input_data.repair_type,
            {"labor_hours": 8.0, "parts_usd": 1000.0, "notes": "Custom repair estimate."},
        )

        labor_cost = repair["labor_hours"] * rates["labor_rate_per_hour_usd"]
        parts_cost = repair["parts_usd"]
        downtime_cost = input_data.downtime_hours_estimate * rates["machine_downtime_cost_per_hour"]
        expediting = parts_cost * rates["expediting_premium_pct"] if input_data.downtime_hours_estimate < 8 else 0.0
        total = labor_cost + parts_cost + downtime_cost + expediting

        breakdown = [
            {"category": "Labor", "description": f"{repair['labor_hours']}h × ${rates['labor_rate_per_hour_usd']}/h", "amount_usd": labor_cost, "is_recurring": False},
            {"category": "Parts", "description": "Required replacement components", "amount_usd": parts_cost, "is_recurring": False},
            {"category": "Downtime", "description": f"{input_data.downtime_hours_estimate}h × ${rates['machine_downtime_cost_per_hour']}/h production loss", "amount_usd": downtime_cost, "is_recurring": False},
        ]
        if expediting > 0:
            breakdown.append({"category": "Expediting", "description": "Rush procurement surcharge (35%)", "amount_usd": expediting, "is_recurring": False})

        return ToolResult(
            success=True,
            tool_name=self.name,
            data={
                "equipment_id": input_data.equipment_id,
                "repair_type": input_data.repair_type,
                "labor_cost_usd": labor_cost,
                "parts_cost_usd": parts_cost,
                "downtime_cost_per_hour_usd": rates["machine_downtime_cost_per_hour"],
                "total_downtime_cost_usd": downtime_cost,
                "expediting_premium_usd": expediting,
                "total_estimated_cost_usd": total,
                "cost_breakdown": breakdown,
                "cost_of_deferring_usd": total * 1.8,
                "notes": repair["notes"],
            },
            source="mock",
        )
