"""
Inventory Agent
================
Analyzes spare parts availability and identifies sourcing options
for parts required to repair the affected equipment.

Tools used:
  - inventory_lookup: Current stock levels for equipment parts
  - supplier_lookup: Alternative supplier options for out-of-stock parts

Gemini call: 1 (with inventory + supplier data in prompt)
"""

from __future__ import annotations

import time

from app.agents.base import BaseAgent
from app.agents.inventory.prompts import SYSTEM_PROMPT, build_user_prompt
from app.schemas.agent import AgentContext, AgentResponse


class InventoryAgent(BaseAgent):
    name = "inventory"
    description = (
        "Analyzes spare parts inventory for affected equipment. "
        "Detects critical shortages and identifies emergency sourcing options."
    )

    async def execute(self, context: AgentContext) -> AgentResponse:
        start = time.monotonic()
        equipment_id = context.equipment_id or "UNKNOWN"

        try:
            # ── Tool calls ─────────────────────────────────────
            inventory_result = await self._safe_tool_call(
                "inventory_lookup",
                {"equipment_id": equipment_id, "part_category": "all"},
            )
            inventory_data = inventory_result.data or {}

            # Only call supplier_lookup if there are known shortages
            critical_shortages = inventory_data.get("critical_shortages", [])
            supplier_data: dict = {}

            if critical_shortages:
                # Look up the first critical shortage part
                # In future: look up all shortages in parallel
                parts = inventory_data.get("parts", [])
                out_of_stock = [p for p in parts if p.get("status") == "out_of_stock"]
                if out_of_stock:
                    part_number = out_of_stock[0].get("part_number", "")
                    supplier_result = await self._safe_tool_call(
                        "supplier_lookup",
                        {"part_number": part_number, "max_lead_time_days": 14},
                    )
                    supplier_data = supplier_result.data or {}

            # ── Gemini call ────────────────────────────────────
            user_prompt = build_user_prompt(context, inventory_data, supplier_data)
            raw = await self.gemini.generate_json(
                user_prompt=user_prompt,
                system_instruction=SYSTEM_PROMPT,
            )

            elapsed = int((time.monotonic() - start) * 1000)
            self._logger.info(
                "Inventory analysis complete",
                extra={"incident_id": context.incident_id, "elapsed_ms": elapsed},
            )

            tools_used = ["inventory_lookup"]
            if supplier_data:
                tools_used.append("supplier_lookup")

            return self._parse_response(raw=raw, tools_used=tools_used, elapsed_ms=elapsed)

        except Exception as exc:
            self._logger.error("InventoryAgent.execute failed", exc_info=exc)
            return self._error_response(str(exc))
