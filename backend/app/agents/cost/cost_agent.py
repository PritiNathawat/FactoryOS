"""
Cost Intelligence Agent
========================
Provides comprehensive financial analysis of an equipment failure.
Evaluates multiple repair approaches and identifies the optimal cost strategy.

Tools used:
  - cost_estimator: Cost breakdown for each repair type

Skills used:
  - cost_analysis: Comparative financial analysis across repair approaches

Gemini call: 1 (with cost data from 3 repair type estimates in prompt)
"""

from __future__ import annotations

import asyncio
import time

from app.agents.base import BaseAgent
from app.agents.cost.prompts import SYSTEM_PROMPT, build_user_prompt
from app.schemas.agent import AgentContext, AgentResponse
from app.skills.cost_analysis import CostAnalysisSkill


class CostIntelligenceAgent(BaseAgent):
    name = "cost"
    description = (
        "Provides financial analysis of repair approaches. Calculates total cost including "
        "labor, parts, downtime, and expediting. Compares strategies and quantifies ROI."
    )

    def __init__(self, tool_registry, gemini_client) -> None:
        super().__init__(tool_registry, gemini_client)
        self._cost_skill = CostAnalysisSkill()

    async def execute(self, context: AgentContext) -> AgentResponse:
        start = time.monotonic()
        equipment_id = context.equipment_id or "UNKNOWN"

        try:
            # ── Tool calls (3 repair types evaluated in parallel) ──
            repair_types = ["bearing_replacement", "full_overhaul", "temporary_fix"]
            production_data = context.tool_results.get("production_schedule") or {}
            revenue_at_risk = production_data.get("estimated_revenue_at_risk_usd", 0)

            # Downtime estimates per approach (hours)
            downtime_per_approach = {
                "bearing_replacement": 8.0,
                "full_overhaul": 28.0,
                "temporary_fix": 3.0,
            }

            cost_results = await asyncio.gather(
                *[
                    self._safe_tool_call(
                        "cost_estimator",
                        {
                            "equipment_id": equipment_id,
                            "repair_type": rt,
                            "downtime_hours_estimate": downtime_per_approach[rt],
                        },
                    )
                    for rt in repair_types
                ]
            )

            cost_estimates = [r.data for r in cost_results if r.success and r.data]
            cost_of_deferring = max(
                (e.get("cost_of_deferring_usd", 0) for e in cost_estimates), default=0
            )

            # ── Skill: Comparative cost analysis ──────────────
            plans_for_skill = [
                {
                    "plan_name": e.get("repair_type", ""),
                    "repair_type": e.get("repair_type", ""),
                    "labor_cost_usd": e.get("labor_cost_usd", 0),
                    "parts_cost_usd": e.get("parts_cost_usd", 0),
                    "downtime_hours": e.get("total_downtime_cost_usd", 0)
                    / e.get("downtime_cost_per_hour_usd", 4200),
                    "downtime_cost_per_hour_usd": e.get("downtime_cost_per_hour_usd", 4200),
                    "expediting_premium_usd": e.get("expediting_premium_usd", 0),
                }
                for e in cost_estimates
            ]
            cost_analysis = self._cost_skill.run(
                plans=plans_for_skill,
                revenue_at_risk_usd=revenue_at_risk,
                cost_of_deferring_usd=cost_of_deferring,
            )

            # ── Gemini call ────────────────────────────────────
            user_prompt = build_user_prompt(context, cost_estimates, cost_analysis)
            raw = await self.gemini.generate_json(
                user_prompt=user_prompt,
                system_instruction=SYSTEM_PROMPT,
            )

            elapsed = int((time.monotonic() - start) * 1000)
            self._logger.info(
                "Cost intelligence analysis complete",
                extra={"incident_id": context.incident_id, "elapsed_ms": elapsed},
            )

            return self._parse_response(
                raw=raw,
                tools_used=["cost_estimator"],
                elapsed_ms=elapsed,
            )

        except Exception as exc:
            self._logger.error("CostIntelligenceAgent.execute failed", exc_info=exc)
            return self._error_response(str(exc))
