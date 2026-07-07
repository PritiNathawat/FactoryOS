"""
InventoryLookupTool
--------------------
Checks current inventory levels for parts required to repair a machine.

The Inventory Agent uses this to determine:
  - Whether critical repair parts are in stock
  - Current stock levels vs. required quantities
  - Reorder status and lead times
  - Alternative part numbers if primary is unavailable
"""

from __future__ import annotations

from typing import ClassVar, Type

from pydantic import BaseModel, Field

from app.mcp.base import BaseMCPTool, ToolPermission, ToolResult


class InventoryLookupInput(BaseModel):
    equipment_id: str = Field(..., description="Equipment to look up parts for")
    part_category: str = Field(
        default="all",
        description="Filter by category: bearings, seals, electronics, all",
    )


class PartInventory(BaseModel):
    part_number: str
    part_name: str
    category: str
    current_stock: int
    minimum_required: int
    reorder_point: int
    unit_cost_usd: float
    warehouse_location: str
    lead_time_days: int
    status: str  # "in_stock", "low_stock", "out_of_stock", "on_order"
    alternative_part_number: str | None = None


class InventoryLookupOutput(BaseModel):
    equipment_id: str
    parts: list[PartInventory]
    critical_shortages: list[str]
    total_parts_cost_estimate_usd: float
    all_parts_available: bool


_PARTS_BY_EQUIPMENT: dict[str, list[dict]] = {
    "M-12": [
        {
            "part_number": "BRG-SKF-6305-2RS",
            "part_name": "Spindle Bearing SKF 6305-2RS",
            "category": "bearings",
            "current_stock": 2,
            "minimum_required": 2,
            "reorder_point": 3,
            "unit_cost_usd": 145.0,
            "warehouse_location": "Bin A-204",
            "lead_time_days": 3,
            "status": "low_stock",
            "alternative_part_number": "BRG-NSK-6305DDU",
        },
        {
            "part_number": "SEAL-M12-COOLANT-KIT",
            "part_name": "Coolant System Seal Kit M-12",
            "category": "seals",
            "current_stock": 5,
            "minimum_required": 1,
            "reorder_point": 2,
            "unit_cost_usd": 78.0,
            "warehouse_location": "Bin B-102",
            "lead_time_days": 1,
            "status": "in_stock",
            "alternative_part_number": None,
        },
        {
            "part_number": "SERVO-FANUC-A06B-6096",
            "part_name": "FANUC Servo Drive A06B-6096",
            "category": "electronics",
            "current_stock": 0,
            "minimum_required": 1,
            "reorder_point": 1,
            "unit_cost_usd": 4800.0,
            "warehouse_location": "N/A - Out of Stock",
            "lead_time_days": 14,
            "status": "out_of_stock",
            "alternative_part_number": "SERVO-SIEMENS-6SL3210-1SE",
        },
        {
            "part_number": "LUBE-SPINDLE-ISO-VG46",
            "part_name": "Spindle Lubricant ISO VG 46 (1L)",
            "category": "consumables",
            "current_stock": 12,
            "minimum_required": 2,
            "reorder_point": 4,
            "unit_cost_usd": 28.0,
            "warehouse_location": "Bin C-010",
            "lead_time_days": 1,
            "status": "in_stock",
            "alternative_part_number": None,
        },
    ],
}


class InventoryLookupTool(BaseMCPTool):
    name: ClassVar[str] = "inventory_lookup"
    description: ClassVar[str] = (
        "Checks current inventory levels for spare parts required to repair or maintain "
        "a specific piece of equipment. Returns stock levels, costs, and shortages."
    )
    permissions: ClassVar[list[ToolPermission]] = [ToolPermission.READ]

    @property
    def input_schema(self) -> Type[BaseModel]:
        return InventoryLookupInput

    @property
    def output_schema(self) -> Type[BaseModel]:
        return InventoryLookupOutput

    async def execute(self, input_data: InventoryLookupInput) -> ToolResult:
        parts_data = _PARTS_BY_EQUIPMENT.get(input_data.equipment_id, [])

        if input_data.part_category != "all":
            parts_data = [p for p in parts_data if p["category"] == input_data.part_category]

        critical_shortages = [
            p["part_name"] for p in parts_data if p["status"] == "out_of_stock"
        ]
        total_cost = sum(
            p["unit_cost_usd"] * p["minimum_required"] for p in parts_data
        )
        all_available = all(
            p["current_stock"] >= p["minimum_required"] for p in parts_data
        )

        return ToolResult(
            success=True,
            tool_name=self.name,
            data={
                "equipment_id": input_data.equipment_id,
                "parts": parts_data,
                "critical_shortages": critical_shortages,
                "total_parts_cost_estimate_usd": total_cost,
                "all_parts_available": all_available,
            },
            source="mock",
        )
