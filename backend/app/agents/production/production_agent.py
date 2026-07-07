"""
Production Agent
=================
Quantifies the production and business impact of an equipment failure.
Evaluates work orders at risk and identifies rerouting options.

Tools used:
  - production_schedule: Active work orders and alternative machines
  
Skills used:
  - downtime_estimation: Estimate repair duration from failure type

Gemini call: 1 (with production schedule + downtime estimate in prompt)
"""

from __future__ import annotations

import time

from app.agents.base import BaseAgent
from app.agents.production.prompts import SYSTEM_PROMPT, build_user_prompt
from app.schemas.agent import AgentContext, AgentResponse
from app.skills.downtime_estimation import DowntimeEstimationSkill


class ProductionAgent(BaseAgent):
    name = "production"
    description = (
        "Quantifies production impact of equipment failures. Identifies work orders at risk, "
        "evaluates rerouting options, and assesses customer delivery impact."
    )

    def __init__(self, tool_registry, gemini_client) -> None:
        super().__init__(tool_registry, gemini_client)
        self._downtime_skill = DowntimeEstimationSkill()

    async def execute(self, context: AgentContext) -> AgentResponse:
        start = time.monotonic()
        equipment_id = context.equipment_id or "UNKNOWN"

        try:
            # ── Tool call ──────────────────────────────────────
            production_result = await self._safe_tool_call(
                "production_schedule",
                {"equipment_id": equipment_id, "lookahead_days": 7},
            )
            production_data = production_result.data or {}

            # ── Skill: Downtime estimation ─────────────────────
            # Use maintenance data from context if available
            machine_history = context.tool_results.get("machine_history", {})
            failure_type = "bearing_failure"  # Default; Maintenance Agent will refine this
            avg_hours = None
            hist_incidents = context.tool_results.get("incident_history", {})
            if hist_incidents:
                avg_hours = hist_incidents.get("average_resolution_time_hours")

            downtime_estimate = self._downtime_skill.run(
                failure_type=failure_type,
                parts_status="out_of_stock",  # Conservative estimate
                tech_experience="experienced",
                historical_avg_hours=avg_hours,
            )

            # ── Gemini call ────────────────────────────────────
            user_prompt = build_user_prompt(context, production_data, downtime_estimate)
            raw = await self.gemini.generate_json(
                user_prompt=user_prompt,
                system_instruction=SYSTEM_PROMPT,
            )

            elapsed = int((time.monotonic() - start) * 1000)
            self._logger.info(
                "Production impact analysis complete",
                extra={"incident_id": context.incident_id, "elapsed_ms": elapsed},
            )

            return self._parse_response(
                raw=raw,
                tools_used=["production_schedule"],
                elapsed_ms=elapsed,
            )

        except Exception as exc:
            self._logger.error("ProductionAgent.execute failed", exc_info=exc)
            return self._error_response(str(exc))
