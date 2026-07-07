"""
Maintenance Agent
==================
Analyzes machine failures and maintenance history to produce
evidence-based repair recommendations.

Tools used:
  - machine_history: Full equipment operational record + failure history
  - maintenance_logs: Technician service logs and observations

Skills used: None (analysis is LLM-based from tool data)

Gemini call: 1 (with machine_history + maintenance_logs data in prompt)
"""

from __future__ import annotations

import time

from app.agents.base import BaseAgent
from app.agents.maintenance.prompts import SYSTEM_PROMPT, build_user_prompt
from app.schemas.agent import AgentContext, AgentResponse, AgentStatus


class MaintenanceAgent(BaseAgent):
    name = "maintenance"
    description = (
        "Analyzes equipment failures using machine history and maintenance logs. "
        "Identifies root causes, recommends repair procedures, and suggests preventive actions."
    )

    async def execute(self, context: AgentContext) -> AgentResponse:
        start = time.monotonic()
        equipment_id = context.equipment_id or "UNKNOWN"

        try:
            # ── Step 1: Gather tool data ───────────────────────
            # Use pre-fetched data from context if available (Manager Agent
            # pre-fetches shared tools to avoid redundant calls).
            # Fall back to direct tool call if not pre-fetched.
            machine_result = await self._safe_tool_call(
                "machine_history",
                {"equipment_id": equipment_id},
            )
            log_result = await self._safe_tool_call(
                "maintenance_logs",
                {"equipment_id": equipment_id, "limit": 10},
            )

            machine_data = machine_result.data or {}
            log_data = log_result.data or {}

            # ── Step 2: Build prompt ───────────────────────────
            user_prompt = build_user_prompt(context, machine_data, log_data)

            # ── Step 3: Call Gemini ────────────────────────────
            raw = await self.gemini.generate_json(
                user_prompt=user_prompt,
                system_instruction=SYSTEM_PROMPT,
            )

            elapsed = int((time.monotonic() - start) * 1000)
            self._logger.info(
                "Maintenance analysis complete",
                extra={
                    "incident_id": context.incident_id,
                    "equipment_id": equipment_id,
                    "elapsed_ms": elapsed,
                    "confidence": raw.get("confidence"),
                },
            )

            return self._parse_response(
                raw=raw,
                tools_used=["machine_history", "maintenance_logs"],
                elapsed_ms=elapsed,
            )

        except Exception as exc:
            self._logger.error("MaintenanceAgent.execute failed", exc_info=exc)
            return self._error_response(str(exc))
