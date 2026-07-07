"""
SupplierLookupTool
-------------------
Finds alternative suppliers for parts not available in inventory.

Used when InventoryLookupTool reports a critical shortage.
The Inventory Agent uses this to find emergency sourcing options.
"""

from __future__ import annotations

from typing import ClassVar, Type

from pydantic import BaseModel, Field

from app.mcp.base import BaseMCPTool, ToolPermission, ToolResult


class SupplierLookupInput(BaseModel):
    part_number: str = Field(..., description="Primary part number to find suppliers for")
    max_lead_time_days: int = Field(default=14, description="Maximum acceptable lead time")


class Supplier(BaseModel):
    supplier_id: str
    supplier_name: str
    part_number: str
    unit_price_usd: float
    available_quantity: int
    lead_time_days: int
    shipping_method: str
    reliability_score: float  # 0.0 - 1.0
    is_oem: bool
    contact_email: str
    notes: str


class SupplierLookupOutput(BaseModel):
    requested_part: str
    suppliers: list[Supplier]
    recommended_supplier_id: str | None
    emergency_available: bool  # Can deliver within 48 hours


_SUPPLIER_DATA: dict[str, list[dict]] = {
    "SERVO-FANUC-A06B-6096": [
        {
            "supplier_id": "SUP-001",
            "supplier_name": "Industrial Parts Direct",
            "part_number": "SERVO-FANUC-A06B-6096",
            "unit_price_usd": 5100.0,
            "available_quantity": 3,
            "lead_time_days": 2,
            "shipping_method": "Express Overnight",
            "reliability_score": 0.94,
            "is_oem": False,
            "contact_email": "orders@industrialpartsdirect.com",
            "notes": "Refurbished with 6-month warranty",
        },
        {
            "supplier_id": "SUP-002",
            "supplier_name": "FANUC America Corporation",
            "part_number": "SERVO-FANUC-A06B-6096",
            "unit_price_usd": 4800.0,
            "available_quantity": 1,
            "lead_time_days": 7,
            "shipping_method": "Standard Freight",
            "reliability_score": 0.99,
            "is_oem": True,
            "contact_email": "parts@fanuc.com",
            "notes": "OEM genuine part, 1-year warranty",
        },
    ],
    "BRG-SKF-6305-2RS": [
        {
            "supplier_id": "SUP-003",
            "supplier_name": "Bearing World Inc.",
            "part_number": "BRG-SKF-6305-2RS",
            "unit_price_usd": 132.0,
            "available_quantity": 50,
            "lead_time_days": 1,
            "shipping_method": "Same-Day Local Delivery",
            "reliability_score": 0.91,
            "is_oem": False,
            "contact_email": "sales@bearingworld.com",
            "notes": "OEM SKF stock, local warehouse",
        },
    ],
}


class SupplierLookupTool(BaseMCPTool):
    name: ClassVar[str] = "supplier_lookup"
    description: ClassVar[str] = (
        "Finds alternative suppliers for a specific part number when internal inventory "
        "is insufficient. Returns supplier options ordered by lead time and reliability."
    )
    permissions: ClassVar[list[ToolPermission]] = [ToolPermission.READ]

    @property
    def input_schema(self) -> Type[BaseModel]:
        return SupplierLookupInput

    @property
    def output_schema(self) -> Type[BaseModel]:
        return SupplierLookupOutput

    async def execute(self, input_data: SupplierLookupInput) -> ToolResult:
        suppliers = _SUPPLIER_DATA.get(input_data.part_number, [])
        filtered = [
            s for s in suppliers if s["lead_time_days"] <= input_data.max_lead_time_days
        ]

        recommended = None
        if filtered:
            # Recommend: fastest delivery from highest-reliability supplier
            sorted_suppliers = sorted(
                filtered, key=lambda s: (s["lead_time_days"], -s["reliability_score"])
            )
            recommended = sorted_suppliers[0]["supplier_id"]

        emergency = any(s["lead_time_days"] <= 2 for s in filtered)

        return ToolResult(
            success=True,
            tool_name=self.name,
            data={
                "requested_part": input_data.part_number,
                "suppliers": filtered,
                "recommended_supplier_id": recommended,
                "emergency_available": emergency,
            },
            source="mock",
        )
